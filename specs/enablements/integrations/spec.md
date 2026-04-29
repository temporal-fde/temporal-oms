# Enablements Specification: Integration Stubs

**Feature Name:** Integration Stubs - Enablements API External Services
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-28
**Updated:** 2026-04-29

---

## Overview

### Executive Summary

The workshop needs credible external systems without requiring every participant to provision
commerce, PIMS, inventory, carrier, and supply-chain-risk services. The workshop integration
surface now lives in `enablements-api`.

`enablements-api` becomes the one place to manage integration fixture state, REST operations,
scenario mutation, and fixture inspection. Nexus remains a compatibility ingress for existing OMS
workflows, but it is not the source of truth for integration behavior. The target Nexus handlers
live with enablements, are stateless adapters, and delegate to `enablements-api` over HTTP.

The services in scope are:

- `commerce-app` - validate incoming orders
- `pims` - enrich order items with SKU and brand data
- `inventory` - resolve warehouses and stub the inventory lifecycle
- `shipping` / `carriers` - replace runtime EasyPost calls with captured address, rate,
  shipment, and label fixtures
- `location-events` - provide supply-chain risk signals for the ShippingAgent

Payments exists in the current implementation, but it is not part of this workshop slice unless we
decide to include payment validation in the exercise narrative.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Give enablement participants one integration mental model: external APIs backed by
  `enablements-api`, not ad hoc mocks scattered across workers
- Goal 2: Document the current stubbed APIs and exact request/response signatures before adding
  more enablements behavior
- Goal 3: Bring `location-events` into the same integration discussion so supply-chain risk data is
  seeded and inspectable like inventory, PIMS, and commerce-app data
- Goal 4: Keep the stubs realistic enough to drive the OMS workflow and ShippingAgent scenarios
  without introducing real vendor setup
- Goal 5: Support `scenarios` input to alter the response behavior of various stubbed services so that dependents can demonstrate alternate behavior.
- Goal 6: Serve captured, deterministic shipping fixtures through the existing message contracts

### Acceptance Criteria

- [x] The enablements spec lists every in-scope service operation and its request/response type
- [x] The spec identifies `enablements-api` as the target owner for enablements integrations
- [x] The spec identifies which behavior is already implemented vs planned
- [x] `location-events` has a proposed service contract and a clear migration path from the
      current Python activity stub
- [x] EasyPost replacement APIs are listed for address verification, carrier rates, shipments,
      and label printing
- [x] The spec defines how `selected_shipment` flows end-to-end as `acme.common.v1.Shipment`
- [x] The spec defines the fixture hierarchy and deterministic ID strategy for shipping data
- [x] The spec defines the Nexus compatibility reroute from apps-owned handlers to
      enablements-owned HTTP adapters
- [x] Open requirements are explicit enough to review before implementation starts

### Requirements and Motivation

The integration layer should satisfy these enablements requirements:

- **No vendor setup for core exercises:** participants should not need commerce, PIMS, inventory,
  or risk-event accounts to complete the enablement.
- **Observable behavior:** fixture state and demo reference data should be queryable through
  `enablements-api` inspection endpoints
- **Service boundary fidelity:** callers should interact with HTTP APIs hosted by
  `enablements-api` that look like external systems. Existing workflow callers may continue to use
  the `oms-integrations-v1` Nexus endpoint, but that endpoint should be backed by enablements-owned
  handlers that call `enablements-api` over HTTP
- **Deterministic scenarios:** facilitators need stable ways to produce invalid orders, SKU
  enrichment, primary vs alternate warehouse selection, and location-risk outcomes
- **No runtime EasyPost dependency:** EasyPost may be used by a capture script to build fixtures,
  but normal local/enablements execution should not need an EasyPost key or network access
- **Contract compatibility:** Java workflows, Python activities, and REST endpoints should keep the
  current request/response contracts where practical
- **Low reset cost:** enablements data should be resettable by restarting `enablements-api` or
  reloading its packaged fixtures
- **Clear promotion path:** any stubbed service should have an obvious replacement path to a real
  service later

The motivation for bringing these together is not just code reuse. It gives the enablements a single
story for external dependencies: the OMS stays composed of bounded contexts, while enablements owns
the deterministic simulator for the systems we do not want participants to provision. This also
makes the ShippingAgent exercise easier to explain because PIMS, inventory, carrier data, and
location-events all contribute facts to one recommendation path.

---

## Current State (As-Is)

### Enablements-Owned Integrations

`enablements-api` owns the enablements integration simulator state and fixture-backed behavior.
The `oms-integrations-v1` Nexus endpoint remains a compatibility ingress for workflow callers, but
it targets enablements workers and delegates to `enablements-api` over HTTP.

`location-events` follows the same model. Today the LLM-facing Python activity remains registered
on the `agents` task queue, but it delegates to `enablements-api`:

```python
async def get_location_events(
    request: GetLocationEventsRequest,
) -> GetLocationEventsResponse
```

The current first pass returns `RISK_LEVEL_NONE` with no events through the enablements API path.

Workshop integration APIs, fixture state, inspection endpoints, and compatibility Nexus handlers
live in the enablements bounded context. The `apps` bounded context keeps order/payment webhook
orchestration, but it does not own integration simulator behavior.

### Existing Stub Behavior

#### Commerce-App

Service interface:

```java
ValidateOrderResponse validateOrder(ValidateOrderRequest request);
```

Backed by `Integrations.validateOrder(ValidateOrderRequest)`.

Request:

```protobuf
message ValidateOrderRequest {
  int64 validation_timeout_secs = 1;
  string customer_id = 2;
  acme.oms.v1.Order order = 3;
}
```

Response:

```protobuf
message ValidateOrderResponse {
  acme.oms.v1.Order order = 1;
  bool manual_correction_needed = 2;
  string support_ticket_id = 3;
  repeated string validation_failures = 4;
}
```

Current stub rule:

- If `order.order_id` contains `"invalid"`, return `manual_correction_needed=true`
- Otherwise return the order with `manual_correction_needed=false`

#### PIMS

Service interface:

```java
EnrichOrderResponse enrichOrder(EnrichOrderRequest request);
```

Backed by `Integrations.enrichOrder(EnrichOrderRequest)`.

Request:

```protobuf
message EnrichOrderRequest {
  acme.oms.v1.Order order = 1;
}
```

Response:

```protobuf
message EnrichOrderResponse {
  acme.oms.v1.Order order = 1;
  repeated EnrichedItem items = 2;
}

message EnrichedItem {
  string item_id = 1;
  string sku_id = 2;
  string brand_code = 3;
  int32 quantity = 4;
}
```

Current stub rule:

- Known item IDs map through a static item map to SKU and brand code
- Unknown item IDs map to `sku_id="ELEC-" + item_id`, `brand_code="GENERIC"`
- Quantity is copied from the order line item

#### Inventory

Service interface:

```java
LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request);
FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request);
HoldItemsResponse holdItems(HoldItemsRequest request);
ReserveItemsResponse reserveItems(ReserveItemsRequest request);
DeductInventoryResponse deductInventory(DeductInventoryRequest request);
ReleaseHoldResponse releaseHold(ReleaseHoldRequest request);
```

Backed by matching `Integrations` update handlers.

Lookup request/response:

```protobuf
message LookupInventoryAddressRequest {
  repeated ShippingLineItem items = 1;
  optional string address_id = 2;
}

message LookupInventoryAddressResponse {
  acme.common.v1.Address address = 1;
}
```

Alternate warehouse request/response:

```protobuf
message FindAlternateWarehouseRequest {
  repeated ShippingLineItem items = 1;
  string current_address_id = 2;
  optional string to_address_id = 3;
}

message FindAlternateWarehouseResponse {
  optional acme.common.v1.Address address = 1;
}
```

Inventory lifecycle request/response:

```protobuf
message HoldItemsRequest {
  string order_id = 1;
  repeated FulfillmentItem items = 2;
}

message HoldItemsResponse {
  string hold_id = 1;
}

message ReserveItemsRequest {
  string order_id = 1;
  string hold_id = 2;
  repeated FulfillmentItem items = 3;
}

message ReserveItemsResponse {
  string reservation_id = 1;
}

message DeductInventoryRequest {
  string order_id = 1;
  string reservation_id = 2;
}

message DeductInventoryResponse {
  bool success = 1;
}

message ReleaseHoldRequest {
  string order_id = 1;
  string hold_id = 2;
}

message ReleaseHoldResponse {
  bool success = 1;
}
```

Current enablements-owned stub rules:

- Warehouse addresses are served from packaged `enablements-api` fixture data
- Collection A warehouses are primary; Collection B warehouses are alternates
- `lookupInventoryAddress` returns a direct warehouse when `address_id` is present
- Otherwise it picks the first warehouse whose SKU prefixes match the first line item's `sku_id`
- `findAlternateWarehouse` excludes `current_address_id` and returns another matching warehouse
- `holdItems` returns `hold_stub_{order_id}`
- `reserveItems` returns `reservation_stub_{order_id}`
- `deductInventory` and `releaseHold` return `success=true`

#### Location-Events

Current activity signature:

```python
async def get_location_events(
    request: GetLocationEventsRequest,
) -> GetLocationEventsResponse
```

Request:

```protobuf
message GetLocationEventsRequest {
  acme.common.v1.Coordinate coordinate = 1;
  double within_km = 2;
  google.protobuf.Timestamp active_from = 3;
  google.protobuf.Timestamp active_to = 4;
  string timezone = 5;
}
```

Response:

```protobuf
message GetLocationEventsResponse {
  LocationRiskSummary summary = 1;
  repeated LocationEvent events = 2;
  google.protobuf.Timestamp window_from = 3;
  google.protobuf.Timestamp window_to = 4;
  string timezone = 5;
}
```

Current stub rule:

- Always return `overall_risk_level=RISK_LEVEL_NONE`
- Return no events
- Echo `active_from`, `active_to`, and `timezone`

#### Former EasyPost-Dependent Shipping APIs

Shipping runtime behavior has moved to fixture-backed `enablements-api` calls. The logical
operations are still split across Java and Python callers, but they no longer call EasyPost during
local/workshop execution:

- Java `Carriers.verifyAddress(VerifyAddressRequest)` verifies the destination address before
  fulfillment continues through `enablements-api`
- Python `ShippingActivities.verify_address(VerifyAddressRequest)` is the same logical operation
  for the ShippingAgent/cart path through `enablements-api`
- Python `ShippingActivities.get_carrier_rates(GetShippingRatesRequest)` retrieves fixture-backed
  shipment rates from `enablements-api`
- Java `Carriers.printShippingLabel(PrintShippingLabelRequest)` validates the fixture shipment/rate
  pair and returns deterministic synthetic tracking data through `enablements-api`

Current request/response contracts that need fixture-backed support:

```protobuf
message VerifyAddressRequest {
  acme.common.v1.Address address = 1;
  string customer_id = 2;
}

message VerifyAddressResponse {
  acme.common.v1.Address address = 1;
}

message GetShippingRatesRequest {
  string from_easypost_id = 1;
  string to_easypost_id = 2;
  repeated ShippingLineItem items = 3;
  acme.common.v1.Shipment selected_shipment = 4;
}

message GetShippingRatesResponse {
  string shipment_id = 1;
  repeated ShippingOption options = 2;
}

message PrintShippingLabelRequest {
  string order_id = 1;
  string shipment_id = 2;
  string rate_id = 3;
}

message PrintShippingLabelResponse {
  string tracking_number = 1;
  string label_url = 2;
}
```

Legacy Java-only carrier rate messages still exist in `workflows.proto`:

```protobuf
message GetCarrierRatesRequest {
  string order_id = 1;
  string easypost_address_id = 2;
  repeated FulfillmentItem items = 3;
}

message GetCarrierRatesResponse {
  string shipment_id = 1;
  repeated CarrierRate rates = 2;
}
```

These should be treated as compatibility surface only. The active ShippingAgent path uses
`GetShippingRatesRequest/Response`, and `fulfillment.Order` prints labels with
`PrintShippingLabelRequest/Response`.

#### Selected Shipment Flow

The checkout selection now flows as a single common message:

```protobuf
message Shipment {
  optional EasyPostShipment easypost = 1;
  optional Money paid_price = 2;
  optional google.protobuf.Timestamp delivery_date = 3;
}

message EasyPostShipment {
  string shipment_id = 1;
  EasyPostRate selected_rate = 2;
}

message EasyPostRate {
  string rate_id = 1;
  optional int64 delivery_days = 2;
  optional google.protobuf.Timestamp delivery_date = 3;
  bool delivery_date_guaranteed = 4;
}
```

The same `selected_shipment` is carried through:

- `apps.api.orders.v1.SubmitOrderRequest.order.selected_shipment`
- `acme.oms.v1.Order.selected_shipment`
- `StartOrderFulfillmentRequest.selected_shipment`
- `FulfillOrderRequest.selected_shipment`
- `CalculateShippingOptionsRequest.selected_shipment`
- `GetShippingRatesRequest.selected_shipment`

This removes the fulfillment-specific `SelectedShippingOption` duplication and gives shipping one
canonical place to read the paid price, selected rate ID, shipment ID, delivery days, and delivery
date.

### Pain Points / Gaps

- There is a limit of 10 concurrent updates for a single workflow execution in Temporal. That means simulating a service under load falls over pretty quick.
- Inventory, PIMS, and location risk are connected in the ShippingAgent scenario, but that
  motivation is not captured in one place
- Runtime EasyPost calls require an API key, network access, and rate-limit management for a
  enablements path that should be deterministic
- Warehouse startup currently verifies addresses through EasyPost; this couples inventory seed
  loading to a vendor call even though the relevant IDs, coordinates, and timezones are stable
- `get_carrier_rates` creates a new shipment on every call; repeated enablements runs can produce
  different IDs and rate ordering unless responses are captured
- `printShippingLabel` currently buys through EasyPost; even with test keys, the enablements only
  needs a realistic tracking number and label URL response
- SLA and margin scenarios are now driven by `selected_shipment` fields, but the spec needs to
  describe those triggers so fixture behavior and prompts stay aligned

## Desired State (To-Be)

### Architecture Overview

The integration layer becomes the enablement's shared external-system simulator. Each service keeps a
domain-shaped API, but responses come from deterministic seeded data rather than real vendors.

The converged target is:

```text
callers
  -> enablements-api REST operation
  -> enablements integration service
  -> fixture store / in-memory cache
  -> current protobuf response type
```

All new integration fixture state should be managed inside `enablements-api`. The API owns the
fixture loader/cache, scenario mutation, REST contracts, and inspection endpoints. Other workers
call it over HTTP.

Existing workflow callers that already use Nexus should keep the same service contracts and endpoint
name, but the backing worker moves from apps to enablements:

```text
processing.Order / fulfillment.Order
  -> Nexus operation on oms-integrations-v1
  -> configured enablements worker namespace, integrations task queue
  -> enablements-owned Nexus service handler
  -> enablements-api REST operation
  -> enablements integration service
  -> fixture store / in-memory cache
```

Nexus handlers must not directly access fixture state or inject the fixture services. Their job is
only request/response transport adaptation. This keeps `enablements-api` as the inspectable owner
and avoids split-brain fixture state between an API process and a worker process.

### Key Capabilities

- **Single inspectable source of stub truth:** participants can query `enablements-api` and see
  warehouse, address, shipment, rate, label, and location-event fixture state
- **Service-shaped APIs:** callers use explicit REST endpoints, so the integrations boundary looks
  like an external service rather than a direct test double
- **Deterministic scenario hooks:** order ID, item ID, SKU prefix, warehouse, and coordinate inputs
  can drive predictable outcomes
- **Fixture-backed shipping:** address verification, rate lookup, shipment selection, and label
  printing are served from local fixtures instead of EasyPost
- **Single owner, Nexus compatibility adapter:** `enablements-api` owns the implementation. Nexus
  usage is a compatibility adapter hosted by enablements workers and must delegate to
  `enablements-api` over HTTP
- **Location-events on the same foundation:** `location-events` should use the same
  `enablements-api` fixture store/cache pattern. The first pass returns an empty event list;
  later enrichment can use request inputs to hint at risk scenarios.

### `enablements-api` REST Surface

All in-scope enablements integrations should be exposed by `enablements-api` and backed by services in
that module. Endpoints should accept and return the existing protobuf message types directly where
practical so Java workflows, Python activities, scripts, and tests use the same contracts.

`enablements-api` should copy the existing protobuf JSON HTTP conversion pattern from apps:

- Source converter:
  `java/apps/apps-core/src/main/java/com/acme/apps/converters/ProtobufJsonHttpMessageConverter.java`
- Target converter:
  `java/enablements/enablements-api/src/main/java/com/acme/enablements/converters/ProtobufJsonHttpMessageConverter.java`
- Target MVC config:
  `java/enablements/enablements-api/src/main/java/com/acme/enablements/config/WebMvcConfig.java`

Register the copied converter first in Spring MVC, matching the apps `WebMvcConfig` pattern, so
controllers can use generated protobuf classes as request and response types. The converter should
keep the apps behavior: `JsonFormat.parser().ignoringUnknownFields()` for reads and
`JsonFormat.printer().includingDefaultValueFields()` for writes. Including default values matters
because explicit zero values such as `delivery_days=0` are meaningful scenario inputs.

If a read endpoint cannot practically carry a full protobuf JSON request as `GET` input in a
specific client, the controller may map query/path parameters into the same protobuf request type
before calling the service. The internal service contract should still be the current protobuf
request/response pair.

Commerce-app:

```http
POST /api/v1/integrations/commerce-app/validate-order
```

- Request: `ValidateOrderRequest`
- Response: `ValidateOrderResponse`

PIMS:

```http
GET /api/v1/integrations/pims/enrich-order
```

- Request: `EnrichOrderRequest`
- Response: `EnrichOrderResponse`

Payments, only if payment validation remains registered:

```http
POST /api/v1/integrations/payments/validate-payment
```

- Request: `ValidatePaymentRequest`
- Response: `ValidatePaymentResponse`

Inventory:

```http
GET /api/v1/integrations/inventory/lookup-address
GET /api/v1/integrations/inventory/alternate-warehouse
GET /api/v1/integrations/inventory/holds
GET /api/v1/integrations/inventory/reservations
POST /api/v1/integrations/inventory/deduct
POST /api/v1/integrations/inventory/release-hold
```

- Requests: `LookupInventoryAddressRequest`, `FindAlternateWarehouseRequest`,
  `HoldItemsRequest`, `ReserveItemsRequest`, `DeductInventoryRequest`, `ReleaseHoldRequest`
- Responses: `LookupInventoryAddressResponse`, `FindAlternateWarehouseResponse`,
  `HoldItemsResponse`, `ReserveItemsResponse`, `DeductInventoryResponse`, `ReleaseHoldResponse`

Shipping:

```http
GET /api/v1/integrations/shipping/verify-address
GET /api/v1/integrations/shipping/rates
GET /api/v1/integrations/shipping/labels
GET  /api/v1/integrations/shipping/fixtures
```

- Requests: `VerifyAddressRequest`, `GetShippingRatesRequest`, `PrintShippingLabelRequest`
- Responses: `VerifyAddressResponse`, `GetShippingRatesResponse`, `PrintShippingLabelResponse`

Location-events:

```http
GET /api/v1/integrations/location-events
```

- Request: `GetLocationEventsRequest`
- Response: `GetLocationEventsResponse`

Fixture state:

```http
GET /api/v1/integrations/fixtures
```

- Response: `GetEnablementIntegrationsFixturesResponse` or equivalent JSON DTO

No endpoint in this surface should require callers to know about Nexus or worker internals.

### Nexus Compatibility Surface

The existing Nexus service contracts in `java/oms/src/main/java/com/acme/oms/services/` stay
stable:

- `CommerceAppService`
- `ProductInformationManagementService`
- `InventoryService`
- `PaymentsService`, only if payment validation remains registered for a future exercise

The target implementation should move the corresponding Nexus service implementations out of
`apps-core` and into enablements. The worker process that registers them should be
`enablements-workers`, on an `integrations` task queue. The existing Nexus endpoint name
`oms-integrations-v1` should be retargeted from `apps / integrations` to the configured
enablements worker namespace and `integrations` task queue so processing and fulfillment callers do
not need contract changes.

Each Nexus handler should delegate to `enablements-api` over HTTP and return the same protobuf
response type. If a simple Java helper is useful, expose it from `enablements-core` as a thin
protobuf-aware HTTP caller. It should not own fixture state, and it should not make
`enablements-api` depend on worker-only Nexus registration. Register any Nexus service beans only in
the worker process, either by package placement, explicit Spring configuration, or conditional
configuration.

### EasyPost Replacement / Shipping

EasyPost should no longer be called by normal workshop/runtime flows. Instead, a capture script
uses EasyPost ahead of time to create realistic fixture data. Runtime code reads that fixture data
and returns message-compatible responses.

The shipping fixture hierarchy should be:

```text
address
  -> shipment
     -> rates
        -> label
```

Key rules:

- Each verified address has a deterministic fixture ID that stays in the current
  `EasyPostAddress.id` field
- Each origin/destination address pair has its own deterministic shipment fixture
- Each shipment fixture contains every rate captured for that shipment, not only the checkout
  selected rate
- Each rate fixture has a deterministic label fixture so `shipment_id + rate_id` can always print
  a label without another vendor call
- `shipment_id` and `rate_id` are treated as companions for label lookup, but lookups by
  `shipment_id` alone must still work when the caller first needs to list rates
- Captured rates do not need to cover every possible selected delivery-day value. Runtime scenario
  logic can tweak copied rate payloads on demand based on `selected_shipment` while still starting
  from realistic captured fixtures
- `delivery_days=0` is a scenario trigger for SLA breach and must be preserved when explicitly
  passed on `selected_shipment.easypost.selected_rate.delivery_days`
- `paid_price.units=1` remains the deterministic margin leak/spike trigger
- The fixture implementation may mutate returned rates on the fly for scenario triggers, but the
  mutation should be deterministic and should not change the public message contracts

The fixture capture script should:

- Start from the hardcoded warehouse addresses currently used by `OrderActivitiesImpl` and the
  enablements shipping fixtures
- Add roughly 10 additional legitimate destination addresses for richer rate coverage
- Verify every address and persist the resulting `EasyPostAddress` fields, including coordinates
  and timezone when available
- For each interesting origin/destination pair, create a shipment with the current default parcel
  assumptions and capture all returned rates
- For each captured rate, synthesize a deterministic label/tracking fixture from
  `shipment_id + rate_id`. The capture script does not need to buy labels from EasyPost.
- Write a JSON fixture database that `enablements-api` can load with stable IDs
- Avoid hand-editing captured payloads except for documented scenario fixtures

The runtime fixture loader should expose queryable metadata:

- known addresses and their fixture IDs
- known shipments and origin/destination address IDs
- rates available per shipment, including `carrier`, `service_level`, `cost`, `estimated_days`,
  `rate_id`, and `shipment_id`
- labels available per `shipment_id + rate_id`, including tracking number and label URL
- location-event fixture configuration, even though the first pass returns an empty event list
- scenario overrides applied to a request

### Shipping APIs

The backing implementation lives in `enablements-api` and is exposed through REST operations.
Internal Java service methods should still use the current request/response message types:

```java
VerifyAddressResponse verifyAddress(VerifyAddressRequest request);
GetShippingRatesResponse getShippingRates(GetShippingRatesRequest request);
PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request);
```

Optional compatibility operation:

```java
GetCarrierRatesResponse getCarrierRates(GetCarrierRatesRequest request);
```

REST endpoints over the same implementation:

```http
GET /api/v1/integrations/shipping/verify-address
GET /api/v1/integrations/shipping/rates
GET /api/v1/integrations/shipping/labels
GET  /api/v1/integrations/shipping/fixtures
```

REST should use the copied protobuf JSON HTTP converter and the current generated message types so
it cannot drift from the activity and workflow contracts.

### Scenario Behavior

Scenario behavior can come from a future global `scenarios` input, but the initial implementation
can derive scenarios from already-threaded request fields:

| Trigger | Source | Expected fixture behavior |
|---------|--------|---------------------------|
| Invalid order | `order.order_id` contains `invalid` | `commerce-app.validateOrder` returns manual correction required |
| Margin leak/spike | `selected_shipment.paid_price.units == 1` | `getShippingRates` returns rates that all exceed paid price; prompt/rule returns `MARGIN_SPIKE` |
| SLA breach | explicit `selected_shipment.easypost.selected_rate.delivery_days == 0` | `getShippingRates` returns no acceptable rate within the selected SLA; prompt/rule returns `SLA_BREACH` |
| Alternate warehouse | `findAlternateWarehouse` with current address ID | returns another fixture warehouse matching item prefixes and excluding current origin |
| Location risk | future input-derived hint, TBD | first pass returns empty events; later enrichment can return risk summaries from the same fixture/cache layer |

If/when global scenarios are added, they should be explicit metadata on the top-level order or
integration request rather than magic substrings. Until then, request-field triggers are acceptable
because they exercise the real message contracts.

### Proposed Location-Events Service

Introduce an `enablements-api` REST operation matching the existing activity contract:

```http
GET /api/v1/integrations/location-events
```

The service implementation should use the same `enablements-api` fixture/cache pattern as
shipping. The ShippingAgent tool can keep the LLM tool name `get_location_events`; the
dispatch implementation can call `enablements-api` over HTTP.

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Put all new integration fixture ownership in `enablements-api` | Enablements is the workshop/demo bounded context; one API owns fixtures, scenario mutation, inspection, and any optional internal adapters | Spread state across apps, fulfillment, Python activities, and Nexus handlers - harder to reason about and reset |
| Add an `enablements-api` module following the Java bounded-context convention | Apps, processing, and fulfillment already use `*-api` modules for REST deployment; enablements should follow the same shape | Put controllers into `enablements-core` or `apps-api` - violates local module conventions and blurs ownership |
| Use REST as the integration behavior boundary | REST is simple to call from Java workflows, Python activities, Nexus adapters, scripts, and Kubernetes | Make Nexus the source of truth - useful for Temporal demos, but the wrong owner for fixture state |
| Host integration Nexus compatibility in enablements workers | Existing workflow callers keep stable Nexus contracts while the implementation moves out of apps and delegates to `enablements-api` | Leave Nexus handlers in `apps-core` - pragmatic historically, but keeps integration simulator ownership in the wrong bounded context |
| Treat `location-events` as an enablements integration service | Risk data is external-domain context like inventory and PIMS; bringing it together clarifies the workshop architecture and avoids Python-only fixture logic | Keep it as a Python activity - simpler short-term but splits the integration story |
| Preserve the existing `get_location_events` tool name | Avoids retraining the LLM prompt and keeps ShippingAgent history readable | Rename to Java-style `getLocationEvents` - leaks service implementation style into agent tools |
| Remove payments from the workshop integration path | The order workflow path does not depend on payments; keeping it registered adds noise without workshop value | Keep payments registered but undocumented - low effort, but leaves an unused service in the story |
| Replace runtime EasyPost calls with shipping fixture reads | Removes API keys, network variance, rate limits, and live label purchasing from workshop execution | Continue using EasyPost test mode - realistic but slow, brittle, and hard to reset |
| Preserve current protobuf request/response contracts | Keeps Java workflows, Python agent tools, and REST callers aligned while internals change | Introduce workshop-only DTOs - easier fixture modeling but creates contract drift |
| Copy the apps protobuf JSON HTTP converter into `enablements-api` | Lets controllers accept and return the generated protobuf classes directly, including default values needed by scenario triggers | Rebuild DTOs for every endpoint - more boilerplate and higher drift risk |
| Capture all rates per shipment | The LLM may choose any rate depending on margin, SLA, or risk context | Persist only the cheapest/selected rate - insufficient for fallback and recommendation paths |
| Use `selected_shipment` as the scenario context | The values already flow from checkout to ShippingAgent and rates; no magic order ID parsing is needed for margin/SLA | Add hidden scenario strings to order IDs - convenient but opaque and easy to forget |
| Synthesize label responses from shipment/rate fixtures | The workflow only needs deterministic tracking and label URL data; buying labels adds unnecessary capture cost and API coupling | Buy test labels for every captured rate - more realistic, but not needed for the demo |
| Expose demo fixture data for inspection | Workshop operators should be able to see addresses, shipments, rates, labels, and location-event fixture config | Keep fixture data private - simpler API surface, harder to debug demos |

### Component Design

#### `enablements-api`

- **Purpose:** Workshop-owned integration simulator API
- **Responsibilities:** Load fixture data, serve REST operations, mutate scenario responses,
  expose demo/reference state, and own all integration simulator state. Nexus adapters must call
  this API over HTTP when fixture behavior or state matters.
- **Current migration state:** Shipping and location-event activity paths use `enablements-api`.
  The `oms-integrations-v1` Nexus compatibility endpoint now targets enablements workers, where
  commerce-app, PIMS, and inventory service handlers are stateless HTTP adapters over
  `enablements-api`. Payments is intentionally not registered for this workshop slice.
- **Interfaces:**
  - REST endpoints under `/api/v1/integrations/**`
  - shared Java services for commerce-app, PIMS, inventory, shipping, and location-events
  - fixture state endpoint

#### `enablements-core`

- **Purpose:** Shared enablements workflow/activity code plus reusable integration transport
  helpers.
- **Responsibilities:** Optionally expose a thin protobuf-aware HTTP caller for
  `enablements-api` integration endpoints and host enablements-owned Nexus service adapter classes
  if that keeps the module layout simple.
- **Constraints:** The HTTP caller and Nexus adapters are stateless transport code. They must not
  load fixtures, mutate scenario state, or inject `enablements-api` fixture services directly.

#### `enablements-workers`

- **Purpose:** Worker deployment for enablements workflows and compatibility Nexus handlers.
- **Responsibilities:** Register the existing `enablements` task queue for
  `WorkerVersionEnablement` and an `integrations` task queue for Nexus service compatibility.
- **Interfaces:**
  - `integrations` task queue with Nexus service beans for commerce-app, PIMS, inventory, and any
    intentionally retained payments service
  - handlers delegate to `enablements-api` over HTTP
  - `oms-integrations-v1` Nexus endpoint targets the configured enablements worker namespace and
    `integrations` task queue

#### Shipping Service

- **Purpose:** Own the EasyPost replacement and serve deterministic shipping data
- **Responsibilities:** Verify addresses from fixtures, return captured rates, print deterministic
  labels, apply scenario-specific rate mutations, expose fixture state for workshop/debug use
- **Interfaces:**
  - `enablements-api` REST operations for `verifyAddress`, `getShippingRates`, and
    `printShippingLabel`
  - optional compatibility service method for `getCarrierRates`
  - JSON fixture database loaded into `enablements-api` cache at startup

#### ShippingAgent Tool Dispatch

- **Purpose:** Let the LLM request risk and shipping data through the same tool names it uses today
- **Responsibilities:** Dispatch `get_location_events` and `get_carrier_rates` to
  `enablements-api` over HTTP while preserving the LLM-facing tool names
- **Interfaces:** Python activity/tool adapters that call `enablements-api` and return the current
  Pydantic/protobuf response types

### Data Model / Schemas

No proto change is required for the first seeded version if `LocationEventsService` reuses
`GetLocationEventsRequest` and `GetLocationEventsResponse` from
`proto/acme/fulfillment/domain/v1/shipping_agent.proto`.

No proto change should be required for the EasyPost replacement if the shipping service returns the current
messages:

- `VerifyAddressRequest/Response`
- `GetShippingRatesRequest/Response`
- `PrintShippingLabelRequest/Response`
- optionally `GetCarrierRatesRequest/Response`

Potential additive change:

```protobuf
message GetEnablementIntegrationsFixturesResponse {
  repeated WarehouseFixture warehouses = 1;
  repeated LocationEventSeed location_event_seeds = 2;
  repeated ShippingAddressFixture shipping_addresses = 3;
  repeated ShippingShipmentFixture shipping_shipments = 4;
}
```

The workshop-facing fixture state endpoint should expose all reference/demo data needed to explain
a run: warehouses, shipping addresses, shipments, rates, synthesized labels, and location-event
fixture configuration. This is only for observability and workshop debugging; operational callers
should continue to use the service-shaped endpoints above.

Proposed JSON fixture shape:

```json
{
  "addresses": [
    {
      "id": "adr_wh_east_01",
      "street1": "100 Commerce Drive",
      "city": "Newark",
      "state": "NJ",
      "zip": "07102",
      "country": "US",
      "residential": false,
      "coordinate": {"latitude": 40.734, "longitude": -74.172},
      "timezone": "America/New_York"
    }
  ],
  "shipments": [
    {
      "shipment_id": "shp_adr_wh_east_01_to_adr_dest_nyc_01",
      "from_address_id": "adr_wh_east_01",
      "to_address_id": "adr_dest_nyc_01",
      "parcel": {"weight_oz": 16, "length_in": 6, "width_in": 6, "height_in": 4},
      "rates": [
        {
          "rate_id": "rate_ups_ground_nyc_01",
          "carrier": "UPS",
          "service_level": "Ground",
          "cost": {"currency": "USD", "units": 1200},
          "estimated_days": 5,
          "delivery_days": 5
        }
      ],
      "labels": [
        {
          "rate_id": "rate_ups_ground_nyc_01",
          "source": "synthetic",
          "tracking_number": "1ZFIXTURE000000001",
          "label_url": "https://example.invalid/labels/1ZFIXTURE000000001.pdf"
        }
      ]
    }
  ]
}
```

### Configuration / Deployment

Add `enablements-api` as a sibling module to `enablements-core` and `enablements-workers`, matching
the `apps`, `processing`, and `fulfillment` bounded-context convention:

```xml
<modules>
  <module>enablements-core</module>
  <module>enablements-api</module>
  <module>enablements-workers</module>
</modules>
```

`enablements-api` owns the integration REST surface and fixture resources. Payments is
intentionally omitted unless a future exercise introduces payment validation.

`enablements-workers` should also own the integration Nexus compatibility worker:

```yaml
spring.temporal:
  namespace: ${TEMPORAL_ENABLEMENTS_NAMESPACE:default}
  workers:
    - task-queue: enablements
      workflow-classes:
        - com.acme.enablements.workflows.WorkerVersionEnablementImpl
      activity-beans:
        - order-activities
        - deployment-activities
    - task-queue: integrations
      nexus-service-beans:
        - commerce-app-service
        - pims-service
        - inventory-service
```

The `oms-integrations-v1` Nexus endpoint should target the configured enablements worker namespace
and the `integrations` task queue. `apps-workers` should stop registering integration Nexus service
beans after the enablements worker is in place.

Shipping configuration:

```yaml
workshop:
  integrations:
    shipping:
      fixture-path: classpath:/fixtures/shipping-fixtures.json
      mode: fixture # fixture | easypost-capture
    location-events:
      mode: fixture
```

`fixture` is the normal local/workshop mode. `easypost-capture` should only be used by the offline
capture script or a deliberate developer task.

---

## Implementation Strategy

### Phase 1: Document and Align Requirements

Deliverables:

- [x] Review this spec and confirm the in-scope services
- [x] Add `enablements-api` module to `java/enablements/pom.xml`
- [x] Remove payments from the workshop integration narrative and registration unless a future
      exercise needs it
- [x] Copy `ProtobufJsonHttpMessageConverter` and `WebMvcConfig` pattern from apps into
      `enablements-api`
- [x] Document the `enablements-api` service/cache shape for all integration runtime lookups
- [x] Document the REST endpoint names under `enablements-api`
- [x] Define the minimum seeded scenarios needed for the workshop

### Phase 2: EasyPost Fixture Capture

Deliverables:

- [x] Inventory the warehouse and destination addresses that must exist in the shipping fixtures
- [x] Add roughly 10 legitimate destination addresses for richer route/rate coverage
- [x] Write a capture script that verifies addresses through EasyPost and persists address
      payloads, coordinates, and timezones
- [x] For each configured origin/destination pair, capture shipment and all returned rates
- [x] For every captured rate, generate a deterministic synthetic label/tracking payload from
      `shipment_id + rate_id`
- [x] Write `shipping-fixtures.json` with stable IDs and enough raw payload detail to debug fixture
      mismatches
- [ ] Document how to refresh fixtures intentionally without changing runtime behavior

### Phase 3: Shipping Runtime Service

Deliverables:

- [x] Create an `enablements-api` fixture loader/cache for shipping data
- [x] Implement `verifyAddress(VerifyAddressRequest)` from fixtures
- [x] Implement `getShippingRates(GetShippingRatesRequest)` from fixtures
- [x] Implement `printShippingLabel(PrintShippingLabelRequest)` from fixtures
- [x] Optionally implement `getCarrierRates(GetCarrierRatesRequest)` as a compatibility wrapper
- [x] Add deterministic scenario mutation for `paid_price.units=1` and explicit
      `delivery_days=0`
- [x] Expose the implementation through `enablements-api` REST endpoints
- [x] Add fixture state REST endpoints for manual use and workshop scripts

### Phase 4: Location-Events Integration Service

Deliverables:

- [x] Create `LocationEventsService` inside `enablements-api`
- [x] Return empty events and `RISK_LEVEL_NONE` in the first pass
- [x] Leave room for future input-derived risk hints without adding scenario fields now
- [x] Expose `GET /api/v1/integrations/location-events`

### Phase 5: ShippingAgent Dispatch Migration

Deliverables:

- [x] Add Python HTTP client/adapters for `enablements-api`
- [x] Keep the ShippingAgent LLM-facing tool definitions stable
- [x] Keep LLM tool name as `get_location_events`
- [x] Keep request/response protos unchanged
- [x] Replace the local Python shipping/location activity implementations after the
      `enablements-api` path is verified
- [x] Move `get_carrier_rates` to fixture-backed shipping without changing the
      LLM-facing tool name
- [x] Ensure `selected_shipment` is attached by workflow context and not invented by the LLM

### Phase 6: Fulfillment Carrier Migration

Deliverables:

- [x] Replace Java `CarriersImpl.verifyAddress` EasyPost calls with fixture-backed verification
- [x] Replace Java `CarriersImpl.printShippingLabel` EasyPost calls with fixture-backed label
      lookup
- [x] Remove EasyPost key as a runtime requirement for local/workshop fulfillment workers
- [x] Keep failure behavior for invalid address/rate IDs deterministic and non-retryable

Initial implementation should deliver Phases 2-6 together. Splitting `location-events` from
EasyPost replacement would leave the workshop dependent on the same scattered integration paths
this spec is intended to remove.

### Phase 7: Nexus Integration Reroute

Deliverables:

- [x] Add or expose a thin Java HTTP caller in `enablements-core` for
      `/api/v1/integrations/**`
- [x] Move commerce-app, PIMS, inventory, and any intentionally retained payments Nexus service
      implementations from `apps-core` to enablements-owned code
- [x] Register an `integrations` task queue in `enablements-workers` with the enablements-owned
      Nexus service beans
- [x] Retarget `oms-integrations-v1` from `apps / integrations` to the configured enablements
      worker namespace and `integrations` task queue
- [x] Remove the `integrations` task queue and integration Nexus service registration from
      `apps-workers` after compatibility is verified
- [x] Decide whether `payments-service` is intentionally retained under enablements or removed
      from the workshop integration endpoint
- [x] Confirm `payments-service` is not retained, so no payment-validation endpoint is needed
- [x] Remove obsolete apps-owned integration workflow code after the reroute was verified

### Phase 8: Workshop Exercise Material

Deliverables:

- [ ] Add exercise notes explaining why integrations are owned by `enablements-api`
- [ ] Add a query/check script for the `enablements-api` fixture state endpoint
- [ ] Add a scenario that demonstrates inventory lookup, alternate warehouse lookup, and
      location risk in one ShippingAgent run
- [x] Add a scenario that demonstrates `paid_price.units=1` margin leak/spike
- [x] Add a scenario that demonstrates `delivery_days=0` SLA breach
- [x] Add a dynamic scenario selector that discovers scenario subdirectories
- [ ] Add a script or REST example that lists fixture addresses, rates, shipments, and labels

### Critical Files / Modules

To Create:

- `java/enablements/enablements-api/pom.xml` - REST API module, following other Java bounded
  contexts
- `java/enablements/enablements-api/src/main/java/com/acme/enablements/ApiApplication.java`
- `java/enablements/enablements-api/src/main/java/com/acme/enablements/config/WebMvcConfig.java` -
  register the protobuf JSON HTTP converter first
- `java/enablements/enablements-api/src/main/java/com/acme/enablements/converters/ProtobufJsonHttpMessageConverter.java` -
  copy of the apps converter with enablements package names
- `java/enablements/enablements-api/src/main/java/com/acme/enablements/controllers/IntegrationsController.java`
  - REST controller for commerce-app, PIMS, inventory, shipping, location-events, and fixture
    state
- `java/enablements/enablements-api/src/main/java/com/acme/enablements/integrations/**` -
  fixture loader/cache, services, DTO helpers, and scenario mutation
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/integrations/**` -
  optional stateless HTTP client/helper for calling `enablements-api`
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/services/**` -
  Nexus service adapters that preserve the `oms` service contracts and delegate to
  `enablements-api`
- `java/enablements/enablements-api/src/main/resources/fixtures/shipping-fixtures.json` - captured
  fixture database
- `scripts/capture-easypost-fixtures.*` - offline fixture capture script
- `python/fulfillment/src/services/enablements_integrations.py` - Python HTTP client for
  `enablements-api`

To Modify:

- `java/enablements/pom.xml` - add `enablements-api`
- `java/enablements/enablements-core/src/main/resources/acme.enablements.yaml` - add the
  `integrations` task queue and Nexus service bean registration for enablements workers
- `scripts/setup-temporal-namespaces.sh` or equivalent environment setup - retarget
  `oms-integrations-v1` to the configured enablements worker namespace and `integrations` task
  queue
- `java/apps/apps-core/src/main/resources/acme.apps.yaml` - remove the `integrations` task queue
  after the enablements worker is verified
- `java/apps/apps-core/src/main/java/com/acme/apps/services/**` - move or remove integration
  Nexus service implementations once enablements-owned adapters are registered
- `java/apps/apps-core/src/main/java/com/acme/apps/workflows/Integrations*.java` - retain only as
  prior-art context until compatibility is verified, then remove in a follow-up if no callers
  depend on it
- existing callers/config - point workshop/demo integration URLs at `enablements-api`
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/CarriersImpl.java` -
  replace EasyPost address and label calls with `enablements-api` calls
- `python/fulfillment/src/agents/workflows/shipping_agent.py` - keep tool names but route
  dispatch/adapters to `enablements-api`
- `python/fulfillment/src/agents/activities/shipping.py` - fixture-backed adapter for
  `verify_address` and `get_carrier_rates`
- `python/fulfillment/src/workers/fulfillment_worker.py` - main `agents` worker for
  ShippingAgent, LLM, inventory, and location-event activities
- `python/fulfillment/src/workers/shipping_worker.py` - `fulfillment-shipping` worker for shipping
  activities

---

## Testing Strategy

### Unit Tests

- Commerce-app: `invalid` order ID sets `manual_correction_needed=true`
- PIMS: known item IDs map to expected SKU and brand code; unknown item IDs map to `ELEC-*`
- Inventory: SKU prefixes resolve to expected primary warehouse
- Inventory: alternate lookup excludes current EasyPost address ID
- Inventory lifecycle: hold/reserve/deduct/release return stable stub IDs/results
- Protobuf JSON HTTP converter: request and response messages round-trip through Spring MVC
  without endpoint-specific DTOs
- Protobuf JSON HTTP converter: default values are included in responses, and explicit zero values
  such as `delivery_days=0` survive request parsing
- Shipping: known address returns a verified `EasyPostAddress` with stable ID,
  coordinates, timezone, and residential flag
- Shipping: unknown address fails deterministically with the same non-retryable semantics
  callers expect from verification failure
- Shipping: origin/destination address pair returns the expected deterministic
  `shipment_id` and all captured rates
- Shipping: `shipment_id + rate_id` returns deterministic tracking number and label URL
- Shipping: invalid `rate_id` for a shipment returns an invalid-rate error
- Shipping: explicit `selected_shipment.easypost.selected_rate.delivery_days=0` is
  preserved and triggers SLA-breach fixture behavior
- Shipping: `selected_shipment.paid_price.units=1` triggers margin leak/spike fixture
  behavior without changing message contracts
- Location-events: first pass returns `RISK_LEVEL_NONE`, empty events, and echoes the request
  window/timezone
- Location-events: fixture configuration is visible for future enrichment even when no events are
  returned

### Integration Tests

- `fulfillment.Order` validates addresses and prints labels without a runtime EasyPost key
- `ShippingAgent` calls inventory lookup, carrier rates, location events, and alternate warehouse
  lookup without changing the public tool names
- `ShippingAgent` receives every captured rate for a shipment and can choose any returned
  `recommended_option_id`
- `enablements-api` shipping endpoints return stable payloads for repeated requests
- `enablements-api` location-events endpoint returns empty-risk payloads in the first pass
- `enablements-api` fixture state endpoint exposes demo/reference data

Follow-up integration tests should cover the Nexus reroute after it is implemented:

- `processing.Order` calls commerce-app and PIMS through Nexus handlers backed by `enablements-api`
- `fulfillment.Order` calls inventory lifecycle operations through Nexus handlers backed by
  `enablements-api`
- `oms-integrations-v1` targets the configured enablements worker namespace and `integrations`
  task queue
- Nexus service adapters do not directly instantiate or inject fixture services; observable state
  comes from `enablements-api`

### Validation Checklist

- [ ] Existing processing and fulfillment workflow tests pass
- [x] ShippingAgent tests pass with `get_location_events` backed by `enablements-api`
- [x] ShippingAgent tests pass with fixture-backed `get_carrier_rates`
- [ ] Fulfillment label-printing tests pass without EasyPost
- [ ] `enablements-api` exposes inspectable fixture state
- [ ] Workshop can inspect location-event fixture configuration even though first pass returns no
      events
- [x] Workshop scenario can demonstrate margin leak/spike with `paid_price.units=1`
- [x] Workshop scenario can demonstrate SLA breach with explicit `delivery_days=0`
- [ ] Local startup succeeds without `EASYPOST_API_KEY` in fixture mode

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| `location-events` migration introduces cross-language HTTP/client friction | Medium | Medium | Implement it through `enablements-api` and add parity tests before removing the Python activity |
| `enablements-api` becomes a dumping ground | Medium | Medium | Limit it to workshop stubs and document promotion criteria for real services |
| Seeded behavior becomes too artificial for the ShippingAgent prompt | Medium | Medium | Keep first-pass location events empty; add realistic event titles, categories, ranks, and windows only when enrichment is designed |
| EasyPost warehouse verification slows or blocks workshop startup | High | Medium | Remove runtime verification; load precomputed address fixtures |
| Fixture capture script accidentally changes stable IDs | Medium | Medium | Generate deterministic IDs from address/route/rate keys and review fixture diffs |
| Captured rates do not naturally match a desired SLA scenario | Medium | Medium | Mutate copied rate payloads on demand based on scenario inputs |
| REST and Nexus compatibility behavior drift | Medium | Medium | Make Nexus handlers stateless HTTP adapters and keep fixture ownership in `enablements-api` |
| Integration Nexus endpoint remains backed by apps workers | Medium | Medium | Retarget `oms-integrations-v1` to the configured enablements worker namespace and `integrations` task queue, then remove the apps registration after verification |
| Removing EasyPost hides real integration errors | Low | Medium | Keep capture mode documented and make fixture failures explicit/non-retryable |
| Payments remains registered but undocumented in the exercise | Low | High | Remove payments from workshop registration unless the workshop narrative needs it |

---

## Dependencies

### External Dependencies

- Existing protobuf-generated Java and Python types
- EasyPost test-mode API access only for the offline fixture capture script
- Local fixture database loaded by `enablements-api`

### Cross-Cutting Concerns

- `processing.Order` depends on `commerce-app` and `pims`
- `fulfillment.Order` depends on `inventory`
- `fulfillment.Order` depends on address verification and label printing
- `ShippingAgent` depends on `inventory`, fixture-backed carrier rates, and `location-events`
- Workshop scripts and docs should treat `enablements-api` as part of the local platform
- Existing workflow callers depend on the `oms-integrations-v1` Nexus endpoint name remaining
  stable even though the endpoint target moves to enablements

### Rollout Blockers

- Confirm whether generated code can reference `GetLocationEventsRequest/Response` from the Java
  `enablements-api` module without additional build changes

---

## Resolved Decisions & Notes

### Resolved Decisions

- [x] `location-events` uses the same `enablements-api` service/cache pattern as shipping
- [x] first-pass `location-events` returns `RISK_LEVEL_NONE` and an empty event list; risk
      enrichment is deferred
- [x] all demo/reference fixture data should be inspectable: warehouses, addresses, shipments,
      rates, labels, and location-event fixture configuration
- [x] scenario behavior starts with request-field triggers, not a global `scenarios` input
- [x] payments is removed from the workshop integration path unless a future exercise needs it
- [x] fixture capture should add roughly 10 legitimate destination addresses that EasyPost accepts
      for variety
- [x] labels are synthesized deterministically from `shipment_id + rate_id`; the capture script
      does not need to buy labels
- [x] REST endpoints live in `enablements-api`
- [x] canonical fixture JSON lives under `enablements-api/src/main/resources/fixtures` so it is
      packaged for local and Kubernetes runs
- [x] EasyPost replacement and `location-events` migration should be delivered together
- [x] Nexus service handlers are compatibility adapters, not fixture owners
- [x] Integration Nexus handlers should move from apps to enablements and delegate to
      `enablements-api` over HTTP
- [x] The `oms-integrations-v1` endpoint name should stay stable for callers while its target moves
      to the configured enablements worker namespace and `integrations` task queue

### Implementation Notes

- PIMS fixtures use uppercase item IDs such as `ITEM-ELEC-001`. The commerce REST product endpoint
  still returns lowercase `item-{n}` values; workshop scripts should use known item IDs when
  deterministic SKU/warehouse behavior matters.
- `lookupInventoryAddress` currently matches only the first item SKU. If multi-item orders are
  important for the workshop, this needs a requirement: split by warehouse, reject mixed prefixes,
  or choose a primary warehouse deterministically.
- The ShippingAgent tool names should remain stable; only the dispatch/adapters need to change to
  call `enablements-api`.
- Enablements-owned Nexus service adapters should not access fixture state directly. If they need a
  helper, use a stateless HTTP caller in `enablements-core` that talks to `enablements-api`.
- The Python converter must preserve explicit zero values for `delivery_days`; `delivery_days=0`
  is meaningful scenario input, not an absent value.
- `selected_shipment` should be supplied by workflow/request context. The LLM should not be
  responsible for inventing selected shipment fields when calling `get_carrier_rates`.
- The current default parcel is 1 lb, 6x6x4 inches. Fixture capture should use that parcel unless
  the message contracts grow parcel fields later.

---

## References & Links

- `java/enablements/pom.xml`
- `java/enablements/enablements-core`
- `java/enablements/enablements-workers`
- `java/enablements/enablements-api/src/main/java/com/acme/enablements/controllers/IntegrationsController.java`
- `java/enablements/enablements-api/src/main/java/com/acme/enablements/integrations/**`
- `scripts/setup-temporal-namespaces.sh`
- `python/fulfillment/src/agents/activities/location_events.py`
- `python/fulfillment/src/agents/activities/shipping.py`
- `python/fulfillment/src/agents/workflows/shipping_agent.py`
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/CarriersImpl.java`
- `proto/acme/fulfillment/domain/v1/shipping_agent.proto`
- `proto/acme/fulfillment/domain/v1/workflows.proto`
- `proto/acme/common/v1/values.proto`
- `specs/fulfillment/location-events/spec.md`
