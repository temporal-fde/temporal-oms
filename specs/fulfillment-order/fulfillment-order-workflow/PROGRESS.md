# fulfillment.Order Workflow — Progress Tracking

**Feature:** `fulfillment.Order` — Durable Fulfillment Orchestration
**Status:** ✅ Current V2 path implemented; Nexus integration backend reroute follow-up
**Owner:** Temporal FDE Team
**Created:** 2026-04-15
**Updated:** 2026-04-29

---

## Phase Status

| Phase | Description | Status | Blocking On |
|-------|-------------|--------|-------------|
| Phase 1 | Proto Schema & Core Types | ✅ Complete | — |
| Phase 2 | Workflow & Activity Interfaces | ✅ Complete | Phase 1 |
| Phase 3 | `fulfillment.Order` Implementation (V1) | ✅ Complete | Phase 2 |
| Phase 4 | Nexus Handler for `validateOrder` | ✅ Complete | Phase 2 |
| Phase 5 | Worker Versioning — `apps.Order` + `processing.Order` | ✅ Complete (deploy + validate pending) | — |
| Phase 6 | Activity Implementations | ✅ Complete for fixture-backed workshop path | Inventory Nexus backend reroute remains follow-up |
| Phase 7 | V2 — `ShippingAgent` Nexus Integration | ✅ Complete | ShippingAgent called through Nexus |

Phases 3 and 4 can be worked in parallel once Phase 2 is complete.
Phase 6 can be worked in parallel with Phases 3–4 once Phase 2 is complete.
Phase 5 cannot start until Phases 3 and 4 are both complete and the deployment spec is underway.

---

## Open Questions (Must Resolve Before Indicated Phase)

| Question | Needed By | Status |
|----------|-----------|--------|
| **Fallback shipping notification:** Silent — no customer notification when a fallback option is selected within margin. | Phase 3 | ✅ Resolved |
| **`margin_leak` type:** `Long` (cents integer). Register as `--type Int` (Temporal's `Int` type maps to `Long` in Java SDK). | Phase 1 | ✅ Resolved |
| **Inventory service contract:** Stub implementation for now; real integration deferred to a follow-up. Phase 3 uses default timeouts; Phase 6 delivers the stub only. | Phase 6 | ✅ Resolved |
| **`FulfillOrderResponse` in `apps.Order` state:** No — `apps.Order` does not store tracking number or shipping selection. `fulfillment.Order` is the source of truth for fulfillment state. | Phase 5 | ✅ Resolved |

---

## Detailed Task Breakdown

### Phase 1 — Proto Schema & Core Types
> ✅ Complete

- [x] Add `EasyPostAddress` message to `proto/acme/common/v1/values.proto`
- [x] Add `optional EasyPostAddress easypost_address = 6` to existing `Address` message in `values.proto`
- [x] Add new Java fulfillment messages to `proto/acme/fulfillment/domain/v1/workflows.proto` (see spec Data Model section for full list)
- [x] Run `buf generate` and verify Java classes produced in `fulfillment-core`
- [ ] Register `margin_leak` SearchAttribute in `fulfillment` namespace: `temporal operator search-attribute create --namespace fulfillment --name margin_leak --type Int`

### Phase 2 — Workflow & Activity Interfaces
> ✅ Complete

- [x] `fulfillment-core`: `Order` workflow interface
  - `execute(StartOrderFulfillmentRequest)`
  - `validateOrder` Update + validator
  - `fulfillOrder` Update + validator
  - `cancelOrder` Signal
  - `notifyDeliveryStatus` Signal
  - `getState` Query
- [x] `fulfillment-core`: `AddressVerification` activity interface — `verifyAddress`
- [x] `fulfillment-core`: `Allocations` activity interface — `holdItems`, `reserveItems`, `deductInventory`, `releaseHold`
- [x] `fulfillment-core`: `DeliveryService` activity interface — `getCarrierRates`
- [x] `fulfillment-core`: `Carriers` activity interface — `printShippingLabel`
- [x] `fulfillment-core`: `FulfillmentOptionsLoader` local activity interface — `loadOptions`
- [x] `fulfillment-core`: `Fulfillment` Nexus service interface — `validateOrder` operation (input: `StartOrderFulfillmentRequest`; see impl note)

### Phase 3 — `fulfillment.Order` Workflow Implementation (V1)
> ✅ Complete (unit tests pending)

- [x] `fulfillment-core`: `OrderImpl` — `@WorkflowInit`, activity stub wiring
- [x] `execute()` body: await `validateOrder` → `loadOptions` → `holdItems` → detached compensation scope → `Workflow.await()` for `fulfillOrder` or cancel/timeout → fire compensation on cancel/timeout
- [x] `validateOrder` Update handler: `AddressVerification.verifyAddress()` → store verified `Address` in state → return `ValidateOrderResponse`
- [x] `fulfillOrder` Update handler:
  - `reserveItems`
  - `ShippingAgent.calculateShippingOptions(...)` through Nexus
  - Apply recommendation; set `margin_leak` / `sla_breach_days` SearchAttributes when applicable
  - Fallback selection for `MARGIN_SPIKE` / `SLA_BREACH`
  - Concurrent: `Carriers.printShippingLabel()` + `Allocations.deductInventory()` via `Promise.allOf`
  - `Workflow.await()` for `notifyDeliveryStatus` Signal
- [x] `cancelOrder` Signal handler: set cancellation flag
- [x] `notifyDeliveryStatus` Signal handler: set delivery status, branch on DELIVERED vs CANCELED
- [x] `getState` Query: return `GetFulfillmentOrderStateResponse`
- [x] Register `OrderImpl` + stub activity beans in `acme.fulfillment.yaml`
- [x] Stub activity implementations in `fulfillment-workers` (Phase 6 delivers real impls)
- [ ] Unit tests (see Testing Strategy in spec):
  - [ ] Happy path
  - [ ] `cancelOrder` before `fulfillOrder` → `releaseHold` called
  - [ ] Timeout before `fulfillOrder` → `releaseHold` called
  - [ ] Rate within margin → `margin_leak` not set
  - [ ] Rate exceeds margin → `margin_leak` set to correct delta
  - [ ] Original option unavailable → fallback selected
  - [ ] `notifyDeliveryStatus(CANCELED)` path
  - [ ] `printShippingLabel` + `deductInventory` execute concurrently

### Phase 4 — Nexus Handler for `validateOrder`
> ✅ Complete (integration test + endpoint registration pending)

- [x] `fulfillment-workers`: `FulfillmentNexusHandler` implementing `Fulfillment` Nexus service interface
  - `validateOrder` operation: `WorkflowClient.executeUpdateWithStart()` on `fulfillment.Order` with `WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING`
  - Note: `Fulfillment` Nexus interface uses `StartOrderFulfillmentRequest` as input (not `ValidateOrderRequest`) so the handler has all data needed for UpdateWithStart
- [x] Register Nexus handler on `fulfillment` task queue in `acme.fulfillment.yaml` (`nexus-service-beans`)
- [ ] Register `order-fulfillment` Nexus endpoint in Temporal cluster (one-time ops step)
- [ ] Integration test: Nexus `validateOrder` → `fulfillment.Order` UpdateWithStart round-trip

### Phase 5 — Worker Versioning: `apps.Order` + `processing.Order`
> Blocked on: Phase 3 complete, Phase 4 complete, deployment spec in progress.
> Resolve `FulfillOrderResponse` in `apps.Order` state question first.

#### `apps.Order` new build-id
- [x] Add `Fulfillment` Nexus service stub to `OrderImpl` (mirrors `Processing` stub; endpoint `order-fulfillment`)
- [x] Add `fulfillOrder` Nexus operation to `Fulfillment` interface + `FulfillmentImpl` handler (ACCEPTED stage)
- [x] In `execute()`, after `Workflow.await()` resolves: call `validateOrder` Nexus and `processOrder` Nexus as concurrent Promises
- [x] After `processOrder` completes: await `validatePromise`, then call `fulfillOrder` Nexus
- [x] Add `@WorkflowVersioningBehavior(PINNED)` to `execute()` and enable deployment-properties in `acme.apps.yaml`
- [ ] Build and deploy `apps-workers` with new build-id; mark as default

#### `processing.Order` new build-id
- [x] Remove `Workflow.getVersion("remove-kafka-fulfillment", ...)` from `OrderImpl.execute()`; the handoff decision is no longer a workflow-version branch
- [ ] Add `send_fulfillment` routing-slip support with legacy-compatible default: absent means `true`, `false` skips `Fulfillments.fulfillOrder()`
- [ ] Write compatibility tests for absent `send_fulfillment` and `send_fulfillment=false` before deploying
- [ ] Build and deploy `processing-workers` with new build-id; mark as default

#### Validation
- [ ] Old `apps.Order` in-flight workflows complete on their existing build-id without touching `fulfillment.Order`
- [ ] Old `processing.Order` in-flight workflows still call `Fulfillments.fulfillOrder()` on their existing build-id
- [ ] New `apps.Order` workflows start `fulfillment.Order` via Nexus
- [ ] New `processing.Order` workflows do not emit Kafka messages

### Phase 6 — Activity Implementations

- [x] `CarriersImpl.verifyAddress` — delegates to `enablements-api` shipping verification
- [x] `CarriersImpl.printShippingLabel` — delegates to `enablements-api` synthetic label lookup
- [x] `FulfillmentOptionsLoaderImpl` — returns fixed workshop shipping margin and Nexus endpoint names
- [x] Inventory lifecycle operations are wired through existing Nexus integration handlers
- [x] Inventory Nexus backend delegates through enablements-owned handlers to `enablements-api`

### Phase 7 — V2 ShippingAgent Nexus Integration

- [x] `fulfillment.Order` calls `ShippingAgent.calculateShippingOptions` through Nexus
- [x] `fulfillment.Order` applies the returned recommendation and selected shipping option
- [x] `fulfillment.Order` prints labels through fixture-backed `CarriersImpl`

---

## Decision Log

### Decision: Kafka → Temporal workflow replacement (2026-04-15)
**Rationale:** The existing `FulfillmentsImpl` + embedded Kafka + `KafkaConsumer` provides no durability, compensation, cancellation, or delivery tracking.
**Status:** Accepted

### Decision: Detached scope for inventory compensation (2026-04-15)
**Rationale:** Cancellation of the main workflow scope must not prevent the compensation activity from running.
**Status:** Accepted

### Decision: `EasyPostAddress` on `common.Address`, no separate `ValidatedAddress` type (2026-04-15)
**Rationale:** Avoids a redundant abstraction layer and preserves the existing external-address contract. Runtime values now come from fixtures rather than live EasyPost calls.
**Status:** Accepted

### Decision: `validateOrder` fires in `apps.Order` `execute()` right before `processOrder` (2026-04-15)
**Rationale:** `apps.Order` collects inputs via Update handlers before its `execute()` proceeds; both `submitOrder` and `capturePayment` must be accumulated before address is confirmed and processing starts.
**Status:** Accepted

### Decision: `ShippingAgent` called via Nexus operation (V2 path) (2026-04-15)
**Rationale:** `ShippingAgent` design is a separate spec; `fulfillment.Order` V2 path calls it via Nexus.
**Status:** Accepted; implemented

### Decision: K8s / Worker Versioning deployment in separate spec (2026-04-15)
**Rationale:** Deployment topology changes are a distinct concern from workflow implementation; separating keeps this spec focused.
**Status:** Accepted; follow-up spec to be written

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-04-15 | Temporal FDE Team | Initial spec + PROGRESS.md |
| 2026-04-15 | Temporal FDE Team | Moved to Planning; detailed task breakdown added |
| 2026-04-15 | Temporal FDE Team | Phases 1–4 implemented: proto schema, workflow + activity interfaces, OrderImpl, FulfillmentNexusHandler, stub activity beans |
| 2026-04-24 | Mike Nichols | Phase 5 code complete: Fulfillment Nexus fulfillOrder operation (ACCEPTED stage), apps.Order PINNED + concurrent validateOrder/processOrder + fulfillOrder dispatch, initial processing.Order handoff branch, acme.apps.yaml deployment-properties enabled |
| 2026-04-30 | Mike Nichols | Removed `Workflow.getVersion` from the processing handoff path; docs now track the `send_fulfillment` routing slip as the required mechanism. |
