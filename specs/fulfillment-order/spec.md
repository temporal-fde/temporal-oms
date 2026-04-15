# fulfillment.Order Workflow Specification

**Feature Name:** `fulfillment.Order` — Durable Fulfillment Orchestration
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-15
**Updated:** 2026-04-15

---

## Overview

### Executive Summary

The `fulfillment.Order` workflow replaces the current Kafka-based fulfillment path with a first-class Temporal workflow that durably orchestrates the full post-processing fulfillment lifecycle. Today, `processing.FulfillmentsImpl` publishes a serialized proto to an embedded Kafka topic and the in-process `KafkaConsumer` stores records in a `HashMap`. There is no compensation on failure, no ability to cancel, and no delivery status tracking.

This workflow brings fulfillment under Temporal's durable execution guarantees. Two existing workflows are updated via **Worker Versioning** to integrate with it:

- **`apps.Order` (new version):** Calls a `validateOrder` Nexus operation in the `submitOrder` Update handler — as soon as the order is submitted — which uses UpdateWithStart to kick off `fulfillment.Order` and validate the shipping address. After processing completes, `apps.Order` sends the `fulfillOrder` Update to `fulfillment.Order`.
- **`processing.Order` (new version):** Removes the `Fulfillments.fulfillOrder()` activity call — fulfillment is now driven by `apps.Order` via Nexus.

Worker Versioning governs the rollout in both the `apps` and `processing` namespaces. In-flight workflows on old versions complete unaffected; new workflows pick up the updated behavior.

The workflow is developed in the `fulfillment` bounded context at `https://github.com/temporal-fde` and lives in the `java/fulfillment/` modules in this repository. The Temporal namespace is `fulfillment`.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Replace the Kafka fulfillment path with a durable Temporal workflow in the `fulfillment` bounded context
- Goal 2: `apps.Order` starts `fulfillment.Order` via a `validateOrder` Nexus operation early in the order lifecycle, enabling address validation concurrent with processing
- Goal 3: Inventory holds are placed eagerly and reliably released via a detached compensation scope on `cancelOrder` Signal or timeout
- Goal 4: Shipping rate revalidation with margin comparison on `fulfillOrder`, with a `margin_leak` SearchAttribute for cost-over-margin reporting
- Goal 5: V1 and V2 shipping validation paths are clearly separated by `Workflow.getVersion()` so replay safety is preserved
- Goal 6: Worker Versioning governs the rollout in `apps` and `processing` namespaces with zero impact on in-flight workflows

### Acceptance Criteria

- [ ] `fulfillment.Order` starts via UpdateWithStart triggered by a `validateOrder` Nexus operation from `apps.Order`
- [ ] `validateOrder` validates the shipping address and returns a `ValidateOrderResponse`
- [ ] `FulfillmentOptions` (including `shipping_margin`) are loaded via LocalActivity on workflow start
- [ ] Inventory hold is placed on workflow start and durably released in a detached scope on `cancelOrder` Signal or timeout
- [ ] `fulfillOrder` Update is accepted after `processOrder` completes (sent by `apps.Order`) and drives all fulfillment activities
- [ ] Shipping rates are re-queried; `margin_leak` SearchAttribute is set when actual rate exceeds `shipping_margin`
- [ ] Shipping label is printed via the `Carriers.printShippingLabel` activity
- [ ] Inventory is deducted after fulfillment; label printing and deduction execute concurrently
- [ ] `notifyDeliveryStatus` Signal transitions the workflow to DELIVERED (complete) or CANCELED (customer notification)
- [ ] `apps.Order` new version calls `validateOrder` Nexus early and `fulfillOrder` Update after processing — gated by Worker Versioning
- [ ] `processing.Order` new version removes `Fulfillments.fulfillOrder()` activity call — gated by Worker Versioning
- [ ] Old `apps.Order` and `processing.Order` workflows complete unaffected on their existing versions

---

## Current State (As-Is)

### What exists today?

- `apps.Order` (`OrderImpl`) orchestrates order completion; calls `processing.processOrder()` via Nexus after accumulating `submitOrder` + `capturePayment` Updates
- `processing.Order` calls `Fulfillments.fulfillOrder()` activity at the end of enrichment
- `FulfillmentsImpl` serializes `FulfillOrderRequest` to JSON and publishes to an embedded Kafka topic
- `KafkaConsumer` (in processing-workers) stores Kafka messages in an in-memory `HashMap` — no durable storage, no workflow
- `java/fulfillment/` module skeleton exists (`fulfillment-core`, `fulfillment-api`, `fulfillment-workers`) but contains no workflow or activity implementations
- `proto/acme/fulfillment/domain/v1/` has Python-era messages; `shipping_agent.proto` exists for the V2 path but is not wired up

### Pain points / gaps

- **No durability:** Kafka + HashMap loses all fulfillment state on any restart
- **No compensation:** Failed fulfillment leaves inventory holds unreleased
- **No cancellation:** No way to cancel an in-flight fulfillment
- **No delivery tracking:** System cannot learn whether an order was delivered or failed delivery
- **Late address validation:** Address problems surface during shipping label generation, after inventory is already allocated and payment captured
- **Dead-end Kafka path:** `processing.Order` fires a Kafka event and gets no feedback — fulfillment result is invisible to the order lifecycle

---

## Desired State (To-Be)

### Architecture Overview

```
apps.Order (apps namespace)
│
│  1. In submitOrder Update handler:
│     ──► validateOrder Nexus operation
│              │
│              └──► fulfillment.Order (fulfillment namespace)
│                   ├── [UpdateWithStart] validateOrder Update
│                   │   - validate shipping address
│                   │   - load FulfillmentOptions (LocalActivity)
│                   │   - place inventory hold
│                   └── [wait] for fulfillOrder Update
│
│  2. processOrder Nexus operation (concurrent with fulfillment start)
│     ──► processing.Order (processing namespace)
│         [V2 via Worker Versioning]: removes Fulfillments.fulfillOrder() activity
│
│  3. After processOrder completes:
│     ──► fulfillOrder Update ──► fulfillment.Order
│
└── (apps.Order completes)

fulfillment.Order (fulfillment namespace)
│
│  [validateOrder Update]
│  ├── LoadFulfillmentOptions (LocalActivity) → shipping_margin
│  ├── Allocations.holdItems()
│  └── return ValidateOrderResponse
│
│  [wait for fulfillOrder Update]
│         ↑ cancelOrder Signal ──► [detached scope] Allocations.releaseHold()
│         ↑ timeout             ──► [detached scope] Allocations.releaseHold()
│
│  [fulfillOrder Update — carries ProcessedOrder]
│  ├── Allocations.reserveItems()
│  ├── Re-query shipping rates
│  │   V1: DeliveryService.getShippingRates()
│  │   V2: ShippingAgent Nexus / Child Workflow (TBD)
│  │   → set margin_leak SearchAttribute if rate > shipping_margin
│  │   → select fallback within margin if original option unavailable
│  ├── [concurrent] Carriers.printShippingLabel()
│  │               + Allocations.deductInventory()
│  └── [wait] notifyDeliveryStatus Signal
│         DELIVERED ──► complete workflow
│         CANCELED  ──► notify customer, complete workflow
```

### Key Capabilities

- **Early fulfillment start via Nexus:** `apps.Order` triggers `fulfillment.Order` as soon as order data is available, before processing completes — address validation runs concurrently with enrichment
- **Worker Versioning-gated rollout:** Both `apps.Order` and `processing.Order` adopt new behavior via new build-ids; old in-flight workflows are unaffected
- **Reliable inventory compensation:** Detached scope releases the hold regardless of how (cancel, timeout, error) the workflow ends before fulfillment
- **Versioned shipping validation:** V1 (DeliveryService) and V2 (ShippingAgent) separated by `Workflow.getVersion()` — safe to replay across versions
- **`margin_leak` observability:** Over-margin shipping cost delta is queryable in Temporal UI and reportable in downstream analytics
- **Concurrent label print + inventory deduction:** Reduces fulfillment latency by parallelizing independent terminal activities
- **Delivery status lifecycle:** `notifyDeliveryStatus` Signal closes the loop between the carrier and the OMS

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| `apps.Order` (not processing) starts `fulfillment.Order` | `apps.Order` is the application-layer orchestrator that owns the full order lifecycle; processing is a domain service that should not know about fulfillment | Have `processing.Order` start fulfillment — couples domain service to fulfillment concerns, wrong layer |
| `validateOrder` as Nexus operation (not a direct Temporal Update across namespaces) | Nexus is the cross-namespace call primitive in Temporal; it provides typed, cancellable operations with proper error propagation | Direct SDK cross-namespace workflow stub — works but bypasses Nexus routing, harder to observe and version |
| Worker Versioning for `apps.Order` + `processing.Order` changes | In-flight workflows must not be disrupted; versioning lets old workflows run to completion on old workers while new workflows adopt the new behavior atomically | Feature flag / config — not determinism-safe; replaying old history with new flag breaks |
| Remove `Fulfillments.fulfillOrder()` from `processing.Order` (not just stub it out) | The activity does nothing valuable under the new model; keeping it adds noise to workflow history and replay surface area | Keep activity as a no-op — misleading in workflow history, still burns a task queue slot |
| Inventory hold on `validateOrder` (not on `fulfillOrder`) | Order may sit in `processOrder` for minutes; holding inventory at start prevents stock-out during that window | Hold at fulfillment time — risks stock-out between validation and fulfillment |
| Detached scope for inventory release | Main scope cancellation must not prevent compensation from executing | Catch-block compensation — cancelled before it can run if the scope itself is cancelled |
| `shipping_margin` loaded via LocalActivity | Policy may vary per tenant/SKU; LocalActivity runs in-process (no task queue round-trip) so it is fast | Hardcode in config — couples shipping policy to deployment cycle |
| `margin_leak` as SearchAttribute (Double) | Enables cross-workflow analytics queries in Temporal UI without fetching history; SearchAttribute API requires scalar types | `Money` proto in workflow result — requires fetching history, no native Temporal query support |
| Concurrent label print + deduct | Both terminal activities have no data dependency; concurrency reduces fulfillment latency | Sequential — simpler, adds unnecessary latency |

### Component Design

#### `Fulfillment` Nexus Service (new, `fulfillment-api` or `fulfillment-workers`)

- **Purpose:** Expose `validateOrder` as a Nexus operation callable from `apps.Order`
- **Responsibilities:**
  - Accept `ValidateOrderRequest` from the `apps` namespace
  - Perform UpdateWithStart on `fulfillment.Order` with the `validateOrder` Update
  - Return `ValidateOrderResponse` to the caller
- **Interfaces:**
  - Nexus endpoint name: `order-fulfillment` (registered in OMS properties, matching the pattern for `order-processing`)
  - Input: `ValidateOrderRequest`
  - Output: `ValidateOrderResponse`

#### `fulfillment.Order` Workflow (`fulfillment-core`)

- **Purpose:** Orchestrates the full post-processing fulfillment lifecycle
- **Workflow ID:** `order_id`
- **Task Queue:** `fulfillment`
- **Namespace:** `fulfillment`
- **Versioning:** PINNED
- **Interfaces:**
  - Update: `validateOrder(ValidateOrderRequest) → ValidateOrderResponse`
  - Update: `fulfillOrder(FulfillOrderRequest) → FulfillOrderResponse`
  - Signal: `cancelOrder(CancelOrderRequest)`
  - Signal: `notifyDeliveryStatus(NotifyDeliveryStatusRequest)`
  - Query: `getState() → GetFulfillmentOrderStateResponse`
  - SearchAttribute: `margin_leak` (Double)

#### `apps.Order` — new version (Worker Versioning)

- **New behavior vs. old:**
  - Added: call `validateOrder` Nexus operation to `fulfillment.Order` when order data is available
  - Added: call `fulfillOrder` Update on `fulfillment.Order` after `processOrder` completes
  - Unchanged: all existing Update/Signal handlers, `processOrder` Nexus operation, compensation logic
- **When `validateOrder` fires:** in the `submitOrder` Update handler, as soon as the order is submitted — the shipping address is available at that point and fulfillment should start as early as possible

#### `processing.Order` — new version (Worker Versioning)

- **New behavior vs. old:** Removes `Fulfillments.fulfillOrder()` activity call after enrichment
- **Mechanism:** `Workflow.getVersion("remove-kafka-fulfillment", DEFAULT_VERSION, 1)` branch skips the activity on new executions; old in-flight workflows replay the original path

#### `Allocations` Activity (`fulfillment-core`)

- **Methods:** `holdItems`, `reserveItems`, `deductInventory`, `releaseHold`

#### `DeliveryService` Activity (`fulfillment-core`, V1)

- **Methods:** `getShippingRates(GetShippingRatesRequest) → GetShippingRatesResponse`

#### `ShippingAgent` (V2 — Nexus operation or Child Workflow, TBD)

- **Interface:** defined in `proto/acme/fulfillment/domain/v1/shipping_agent.proto`
- **Decision:** Nexus vs. Child Workflow to be resolved before Phase 6

#### `Carriers` Activity (`fulfillment-core`)

- **Methods:** `printShippingLabel(PrintShippingLabelRequest) → PrintShippingLabelResponse`

#### `FulfillmentOptionsLoader` LocalActivity (`fulfillment-core`)

- **Methods:** `loadOptions(LoadFulfillmentOptionsRequest) → FulfillmentOptions`
- **Why LocalActivity:** in-process call; no external I/O; fast; not subject to task queue scheduling

### Data Model / Schemas

All new Java fulfillment messages belong in `proto/acme/fulfillment/domain/v1/workflows.proto` (alongside existing Python-era messages — avoid naming conflicts; see Implementation Notes).

```protobuf
// ─── Workflow Start ────────────────────────────────────────────────────────

message StartOrderFulfillmentRequest {
  string order_id = 1;
  StartOrderFulfillmentExecutionOptions execution_options = 2;
  SelectedShipping selected_shipping = 3;
  string customer_id = 4;
  acme.apps.domain.apps.v1.CompleteOrderRequest placed_order = 5;
}

message StartOrderFulfillmentExecutionOptions {
  optional int64 fulfillment_timeout_secs = 1;
}

message SelectedShipping {
  google.protobuf.Timestamp timestamp = 1;
  acme.common.v1.Money price = 2;
  string shipping_option_id = 3;
  google.protobuf.Timestamp date = 4;  // expected ship date
}

// ─── validateOrder Update (also the Nexus operation input/output) ──────────

message ValidateOrderRequest {
  string order_id = 1;
  acme.common.v1.Address address = 2;
}

message ValidateOrderResponse {
  string order_id = 1;
  ValidatedAddress address = 2;
}

message ValidatedAddress {
  acme.common.v1.Address normalized = 1;
  bool is_valid = 2;
  repeated string validation_messages = 3;
  optional acme.common.v1.Coordinate coordinate = 4;  // for ShippingAgent V2
}

// ─── FulfillmentOptions (loaded via LocalActivity) ─────────────────────────

message FulfillmentOptions {
  acme.common.v1.Money shipping_margin = 1;
}

// ─── fulfillOrder Update ───────────────────────────────────────────────────

message FulfillOrderRequest {                         // fulfillment domain version
  ProcessedOrder processed_order = 1;
}

message FulfillOrderResponse {
  string tracking_number = 1;
  ShippingSelection shipping_selection = 2;
}

message ProcessedOrder {
  string order_id = 1;
  string customer_id = 2;
  acme.processing.domain.processing.v1.GetProcessOrderStateResponse processing_result = 3;
}

// ─── cancelOrder Signal ────────────────────────────────────────────────────

message CancelFulfillmentRequest {
  string order_id = 1;
  string reason = 2;
}

// ─── notifyDeliveryStatus Signal ───────────────────────────────────────────

message NotifyDeliveryStatusRequest {
  string order_id = 1;
  DeliveryStatus status = 2;
  optional string carrier_tracking_id = 3;
  optional string failure_reason = 4;
}

enum DeliveryStatus {
  DELIVERY_STATUS_UNSPECIFIED = 0;
  DELIVERY_STATUS_DELIVERED = 1;
  DELIVERY_STATUS_CANCELED = 2;
}

// ─── Workflow State Query ──────────────────────────────────────────────────

message GetFulfillmentOrderStateResponse {
  StartOrderFulfillmentRequest args = 1;
  FulfillmentOptions options = 2;
  ValidateOrderResponse validation = 3;
  FulfillOrderRequest fulfillment_request = 4;
  ShippingSelection shipping_selection = 5;
  string tracking_number = 6;
  DeliveryStatus delivery_status = 7;
  repeated string errors = 8;
}

message ShippingSelection {
  string shipping_option_id = 1;
  acme.common.v1.Money actual_price = 2;
  acme.common.v1.Money margin_delta = 3;  // positive = over margin
  bool used_fallback = 4;
  string fallback_reason = 5;
}
```

#### SearchAttributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `margin_leak` | `Double` | Delta (minor currency units) between actual shipping cost and `shipping_margin`. Set only when actual > margin. |

### Configuration / Deployment

```yaml
# java/fulfillment/fulfillment-core/src/main/resources/acme.fulfillment.yaml
spring.temporal:
  namespace: ${TEMPORAL_NAMESPACE:fulfillment}
  workers:
    - task-queue: fulfillment
      workflow-classes:
        - com.acme.fulfillment.workflows.OrderImpl
      activity-beans:
        - allocations-activities
        - delivery-service-activities
        - carriers-activities
        - fulfillment-options-local-activities
```

The `order-fulfillment` Nexus endpoint must be registered in the OMS properties (same mechanism as `order-processing` in `apps.Order`):

```yaml
# apps OmsProperties nexus endpoints
nexus:
  endpoints:
    order-processing: <processing-nexus-endpoint>
    order-fulfillment: <fulfillment-nexus-endpoint>   # new
```

---

## Implementation Strategy

### Phase 1: Proto Schema & Core Types

Deliverables:
- [ ] Extend `proto/acme/fulfillment/domain/v1/workflows.proto` with all new Java fulfillment messages
- [ ] Run `buf generate` to produce Java classes in `fulfillment-core`
- [ ] Register `margin_leak` SearchAttribute: `temporal operator search-attribute create --namespace fulfillment --name margin_leak --type Double`

### Phase 2: `fulfillment.Order` Workflow & Activity Interfaces

Deliverables:
- [ ] `fulfillment-core`: `Order` workflow interface (`execute`, `validateOrder` Update + validator, `fulfillOrder` Update + validator, `cancelOrder` Signal, `notifyDeliveryStatus` Signal, `getState` Query)
- [ ] `fulfillment-core`: `Allocations` activity interface (`holdItems`, `reserveItems`, `deductInventory`, `releaseHold`)
- [ ] `fulfillment-core`: `DeliveryService` activity interface (`getShippingRates`)
- [ ] `fulfillment-core`: `Carriers` activity interface (`printShippingLabel`)
- [ ] `fulfillment-core`: `FulfillmentOptionsLoader` local activity interface (`loadOptions`)
- [ ] `fulfillment-core`: `Fulfillment` Nexus service interface (wraps `validateOrder` as a Nexus operation)

### Phase 3: `fulfillment.Order` Workflow Implementation (V1 shipping path)

Deliverables:
- [ ] `fulfillment-core`: `OrderImpl`
  - `@WorkflowInit`: initialize activity stubs with appropriate timeouts
  - `execute()`: open detached compensation scope → `Workflow.await()` for fulfillOrder or cancel/timeout → fire compensation if needed
  - `validateOrder` Update handler: `loadOptions` (LocalActivity) → `holdItems` → validate address → return `ValidateOrderResponse`
  - `fulfillOrder` Update handler: `reserveItems` → `getShippingRates` (V1) → margin check + `margin_leak` SearchAttribute → concurrent (`printShippingLabel` + `deductInventory`) → await `notifyDeliveryStatus`
  - `cancelOrder` Signal handler: set cancellation flag
  - `notifyDeliveryStatus` Signal handler: set delivery status
  - `getState` Query: return `GetFulfillmentOrderStateResponse`
- [ ] Stub activity implementations returning defaults (real impls Phase 5)
- [ ] Register workflow + activity beans in `acme.fulfillment.yaml`
- [ ] Unit test: happy path (start → validateOrder → fulfillOrder → DELIVERED)
- [ ] Unit test: `cancelOrder` before `fulfillOrder` → verify `releaseHold` called
- [ ] Unit test: timeout before `fulfillOrder` → verify `releaseHold` called
- [ ] Unit test: rate within margin → `margin_leak` SearchAttribute NOT set
- [ ] Unit test: rate exceeds margin → `margin_leak` SearchAttribute set to correct delta
- [ ] Unit test: original shipping option unavailable → fallback selected
- [ ] Unit test: `notifyDeliveryStatus(CANCELED)` → customer notification path
- [ ] Unit test: concurrent activities — `printShippingLabel` + `deductInventory` run in parallel

### Phase 4: Nexus Handler for `validateOrder`

Expose the `validateOrder` Nexus operation so `apps.Order` can call across namespaces.

Deliverables:
- [ ] `fulfillment-workers` (or `fulfillment-api`): `FulfillmentNexusHandler` implementing the `Fulfillment` Nexus service interface
  - `validateOrder` operation: does UpdateWithStart on `fulfillment.Order` workflow
- [ ] Register Nexus handler on the `fulfillment` task queue
- [ ] Register `order-fulfillment` Nexus endpoint in the Temporal cluster (pointing to the `fulfillment` namespace + task queue)
- [ ] Integration test: Nexus `validateOrder` → `fulfillment.Order` UpdateWithStart round-trip

### Phase 5: Worker Versioning — `apps.Order` + `processing.Order`

Gate new behavior behind new build-ids so existing in-flight workflows are unaffected.

#### `apps.Order` new version

- [ ] Add `Fulfillment` Nexus service stub to `OrderImpl` (mirrors existing `Processing` Nexus stub pattern)
- [ ] In `execute()`, after `tryScheduleProcessOrder` conditions met, launch `validateOrder` Nexus operation concurrently with `processOrder` Nexus operation
- [ ] After `processOrder` completes successfully, send `fulfillOrder` Update to `fulfillment.Order`
- [ ] Deploy `apps-workers` with new build-id; mark as new default via Worker Versioning

#### `processing.Order` new version

- [ ] Add `Workflow.getVersion("remove-kafka-fulfillment", DEFAULT_VERSION, 1)` branch in `OrderImpl.execute()` to skip `Fulfillments.fulfillOrder()` on new executions
- [ ] Deploy `processing-workers` with new build-id; mark as new default via Worker Versioning

#### Validation

- [ ] Verify old `apps.Order` and `processing.Order` in-flight workflows complete on their existing build-ids
- [ ] Verify new `apps.Order` workflows start `fulfillment.Order` via Nexus
- [ ] Verify `processing.Order` new version does not call `Fulfillments.fulfillOrder()`

### Phase 6: Activity Implementations

Implement real activity logic.

Deliverables:
- [ ] `fulfillment-workers`: `AllocationsImpl`
- [ ] `fulfillment-workers`: `DeliveryServiceImpl` (V1 shipping rates)
- [ ] `fulfillment-workers`: `CarriersImpl` (PrintShippingLabel)
- [ ] `fulfillment-workers`: `FulfillmentOptionsLoaderImpl`

### Phase 7: V2 Shipping Path — `ShippingAgent` (Deferred)

Deferred pending Nexus vs. Child Workflow design decision for `ShippingAgent`.

Deliverables:
- [ ] Implement `ShippingAgent` integration (Nexus or Child Workflow per decision)
- [ ] Add `Workflow.getVersion("shipping-v2", DEFAULT_VERSION, 1)` branch in `fulfillOrder` handler
- [ ] Replay test: start with V1 history, apply V2 code — no `NonDeterminismException`

### Critical Files / Modules

**To Create:**
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/Order.java` — workflow interface (Phase 2)
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/OrderImpl.java` — workflow impl (Phase 3)
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/Allocations.java` (Phase 2)
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/DeliveryService.java` (Phase 2)
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/Carriers.java` (Phase 2)
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/FulfillmentOptionsLoader.java` (Phase 2)
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/nexus/Fulfillment.java` — Nexus service interface (Phase 2)
- `java/fulfillment/fulfillment-workers/src/main/java/com/acme/fulfillment/nexus/FulfillmentNexusHandler.java` — Nexus handler (Phase 4)
- `java/fulfillment/fulfillment-workers/src/main/java/com/acme/fulfillment/activities/AllocationsImpl.java` (Phase 6)
- `java/fulfillment/fulfillment-workers/src/main/java/com/acme/fulfillment/activities/DeliveryServiceImpl.java` (Phase 6)
- `java/fulfillment/fulfillment-workers/src/main/java/com/acme/fulfillment/activities/CarriersImpl.java` (Phase 6)
- `java/fulfillment/fulfillment-workers/src/main/java/com/acme/fulfillment/activities/FulfillmentOptionsLoaderImpl.java` (Phase 6)

**To Modify:**
- `proto/acme/fulfillment/domain/v1/workflows.proto` — add new Java messages (Phase 1)
- `java/fulfillment/fulfillment-core/src/main/resources/acme.fulfillment.yaml` — register workflow + activity beans (Phase 3)
- `java/apps/apps-core/src/main/java/com/acme/apps/workflows/OrderImpl.java` — add Fulfillment Nexus stub + calls (Phase 5, new build-id)
- `java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImpl.java` — version branch to skip `Fulfillments.fulfillOrder()` (Phase 5, new build-id)

---

## Testing Strategy

### Unit Tests (TestWorkflowEnvironment)

- **Happy path:** Start → validateOrder → fulfillOrder → notifyDeliveryStatus(DELIVERED) → complete
- **Cancel before fulfillment:** cancelOrder Signal before fulfillOrder → `releaseHold` called
- **Timeout before fulfillment:** Advance test clock past timeout → `releaseHold` called
- **Rate within margin:** fulfillOrder with rate ≤ margin → `margin_leak` NOT set
- **Rate exceeds margin:** fulfillOrder with rate > margin → `margin_leak` set to correct delta
- **Original option unavailable:** fulfillOrder when option_id absent from re-queried rates → fallback selected within margin
- **CANCELED delivery:** notifyDeliveryStatus(CANCELED) → customer notification, complete
- **Concurrent activities:** `printShippingLabel` + `deductInventory` issued as concurrent Promises

### Integration Tests

- Nexus `validateOrder` → `fulfillment.Order` UpdateWithStart round-trip (real Temporal cluster)
- `apps.Order` new version → `fulfillment.Order` start via Nexus + `fulfillOrder` Update after processing
- Worker Versioning: old `apps.Order` in-flight workflow completes without touching `fulfillment.Order`
- Worker Versioning: old `processing.Order` in-flight workflow calls `Fulfillments.fulfillOrder()` (legacy path intact)

### Workflow Versioning Tests (Phase 7)

- Replay V1 `fulfillment.Order` history with V2 code: no `NonDeterminismException`
- `processing.Order`: replay old history (pre-version branch) with new code: old path preserved

### Validation Checklist

- [ ] All `fulfillment.Order` unit tests pass with `TestWorkflowEnvironment`
- [ ] Nexus integration test passes against local Temporal cluster
- [ ] `margin_leak` SearchAttribute visible in Temporal UI
- [ ] `processing.Order` new version does NOT emit Kafka messages
- [ ] Old in-flight workflows in `apps` and `processing` complete unaffected
- [ ] V2 replay test passes (Phase 7)

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| `order-fulfillment` Nexus endpoint not yet registered — blocks `apps.Order` V2 rollout | High | Medium | Phase 4 (Nexus handler) must complete before Phase 5 (`apps.Order` new version); endpoint registration is a one-time ops step |
| Worker Versioning in `apps` namespace: `apps.Order` V2 tries to call `fulfillment.Order` but `fulfillment-workers` not yet deployed | High | Medium | Deploy `fulfillment-workers` and register Nexus endpoint before deploying new `apps-workers` build-id |
| Detached scope for inventory compensation is easy to break in refactors | High | Medium | Dedicated unit tests for both cancel and timeout compensation paths; CI must run these |
| Proto naming conflict: existing Python-era `FulfillOrderRequest` in same package | Low | High | New Java messages use distinct names (`StartOrderFulfillmentRequest`, not `FulfillOrderRequest`); long-term, split into separate `.proto` files |
| `Workflow.getVersion()` branch in `processing.Order` — wrong placement causes non-determinism on replay | High | Low | Follow existing `VersioningBehavior.PINNED` pattern in `processing.OrderImpl`; write replay test before deploying new build-id |
| `ShippingAgent` design (Nexus vs. Child WF) unresolved — V2 path has interface, no wiring | Low (for V1) | High | V2 deferred to Phase 7; V1 uses DeliveryService only; no V1 code depends on V2 being resolved |

---

## Dependencies

### External Dependencies

- Temporal Java SDK 1.26+ (UpdateWithStart, Nexus SDK, SearchAttribute upsert, Worker Versioning APIs)
- `proto/acme/common/v1/values.proto` — `Money`, `Address`, `Coordinate`
- `proto/acme/apps/domain/v1/workflows.proto` — `CompleteOrderRequest` (in `StartOrderFulfillmentRequest`)
- `proto/acme/processing/domain/v1/workflows.proto` — `GetProcessOrderStateResponse` (in `ProcessedOrder`)
- `proto/acme/fulfillment/domain/v1/shipping_agent.proto` — V2 interface (Phase 7)

### Cross-Cutting Concerns

- **`order-fulfillment` Nexus endpoint:** Must be registered in Temporal cluster and wired into `apps.Order` OMS properties before Phase 5 ships
- **`margin_leak` SearchAttribute registration:** One-time cluster operation; must precede first `fulfillment.Order` execution that sets it
- **`fulfillment-workers` deployment order:** Must be running and Nexus endpoint registered before `apps-workers` new build-id is marked as default
- **`processing.Order` build-id:** New build-id must be tested for replay safety before being marked as default in the `processing` namespace

### Rollout Blockers

- [ ] `margin_leak` SearchAttribute registered in `fulfillment` Temporal namespace
- [ ] `fulfillment-workers` deployed and healthy on `fulfillment` task queue
- [ ] `order-fulfillment` Nexus endpoint registered and accessible from `apps` namespace
- [ ] Proto buf generation produces correct Java classes for all new messages
- [ ] ShippingAgent design decision (Nexus vs. Child WF) — required before Phase 7 only

---

## Open Questions & Notes

### Questions for Tech Lead / Product

- [x] **`validateOrder` trigger in `apps.Order`:** Fires in the `submitOrder` Update handler — as soon as the order is submitted. Address is available at that point; no need to wait for payment capture. ✅ Resolved.
- [ ] **ShippingAgent (V2):** Nexus operation or Child Workflow? Decision needed before Phase 7.
- [ ] **Fallback shipping notification:** When a fallback shipping option is used (original unavailable), should the customer be notified, or is this silent?
- [ ] **`margin_leak` units:** `Double` (minor currency units, e.g., cents) confirmed? Or a richer Money-codec SearchAttribute?
- [ ] **Inventory service contract:** Internal service or external API? Affects `Allocations` activity timeout and retry policy.
- [ ] **Address validation service:** Which service backs `ValidatedAddress`? EasyPost (referenced in `shipping_agent.proto`)? A stub for now?
- [ ] **`FulfillOrderResponse` in `apps.Order` state:** Should `apps.Order` store the `FulfillOrderResponse` (tracking number, shipping selection) in `GetCompleteOrderStateResponse`?

### Implementation Notes

- **`apps.Order` Nexus stub:** Follow the existing `Processing` Nexus service stub pattern in `OrderImpl`. The `Fulfillment` Nexus stub uses endpoint name `order-fulfillment` from OMS properties.
- **UpdateWithStart in Nexus handler:** Use `WorkflowClient.startUpdateWithStart()` with `WorkflowIDConflictPolicy.WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING` so duplicate Nexus calls are idempotent.
- **Sequencing in `apps.Order`:** `validateOrder` Nexus fires in `submitOrder` (before payment is even captured). `processOrder` Nexus fires later in `execute()` once both order + payment are accumulated. These are not concurrent — `validateOrder` starts the fulfillment workflow early; `processOrder` drives processing independently; `fulfillOrder` Update closes the loop after processing completes.
- **`Workflow.getVersion()` in `processing.Order`:** Place the version branch immediately before the `fulfillments.fulfillOrder()` call. Version name: `"remove-kafka-fulfillment"`. Old path = `DEFAULT_VERSION`, new path = `1`.
- **Proto naming:** Existing Python-era messages in `workflows.proto` use names like `FulfillOrderRequest`, `Item`, `Status`. New Java messages must not reuse these names. Consider a comment block separator in the proto file marking the Java section.
- **`margin_leak` SearchAttribute:** Call `Workflow.upsertTypedSearchAttributes(SearchAttributeKey.forDouble("margin_leak").valueSet(delta))` only when delta > 0. Never set to 0 or a negative value.
- **Concurrent activities:** Use `Promise.allOf(Async.function(carriers::printShippingLabel, ...), Async.function(allocations::deductInventory, ...))`. Do NOT use `ExecutorService` — not deterministic in Temporal workflows.

---

## References & Links

- [temporal-fde GitHub organization](https://github.com/temporal-fde) — workflow development home
- [apps.OrderImpl](../../java/apps/apps-core/src/main/java/com/acme/apps/workflows/OrderImpl.java) — existing Nexus pattern, detached scope compensation, WorkflowInit
- [processing.OrderImpl](../../java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImpl.java) — VersioningBehavior.PINNED pattern
- [FulfillmentsImpl.java (Kafka path being replaced)](../../java/processing/processing-core/src/main/java/com/acme/processing/workflows/activities/FulfillmentsImpl.java)
- [fulfillment-core acme.fulfillment.yaml](../../java/fulfillment/fulfillment-core/src/main/resources/acme.fulfillment.yaml)
- [shipping_agent.proto](../../proto/acme/fulfillment/domain/v1/shipping_agent.proto) — ShippingAgent V2 interface
- [common/v1/values.proto](../../proto/acme/common/v1/values.proto) — Money, Address, Coordinate
- [Temporal UpdateWithStart docs](https://docs.temporal.io/develop/java/message-passing#update-with-start)
- [Temporal Nexus docs](https://docs.temporal.io/nexus)
- [Temporal Worker Versioning docs](https://docs.temporal.io/workers#worker-versioning)
