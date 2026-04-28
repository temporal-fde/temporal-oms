# Workshop Specification: Integration Stubs

**Feature Name:** Integration Stubs - Workflow-backed External Services for Workshop
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-28
**Updated:** 2026-04-28

---

## Overview

### Executive Summary

The workshop needs credible external systems without requiring every participant to provision
commerce, PIMS, inventory, and supply-chain-risk services. The existing `apps.Integrations`
workflow already gives us that pattern: Nexus service handlers expose external-service-shaped
APIs, then route each call into one long-running workflow with `UpdateWithStart`.

This spec documents that integration layer as a first-class workshop component and extends the
target service set to include `location-events`. The goal is to make all non-core OMS dependencies
observable, deterministic enough for exercises, and easy to reset or inspect from Temporal UI.

The services in scope are:

- `commerce-app` - validate incoming orders
- `pims` - enrich order items with SKU and brand data
- `inventory` - resolve warehouses and stub the inventory lifecycle
- `shipping-catalog` / `carriers` - replace runtime EasyPost calls with captured address, rate,
  shipment, and label fixtures
- `location-events` - provide supply-chain risk signals for the ShippingAgent

Payments exists in the current implementation, but it is not part of this workshop slice unless we
decide to include payment validation in the exercise narrative.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Give workshop participants one integration mental model: external APIs backed by a
  simple Temporal workflow, not ad hoc mocks scattered across workers
- Goal 2: Document the current stubbed APIs and exact request/response signatures before adding
  more workshop behavior
- Goal 3: Bring `location-events` into the same integration discussion so supply-chain risk data is
  seeded and inspectable like inventory, PIMS, and commerce-app data
- Goal 4: Keep the stubs realistic enough to drive the OMS workflow and ShippingAgent scenarios
  without introducing real vendor setup
- Goal 5: Support `scenarios` input to alter the response behavior of various stubbed services so that dependents can demonstrate alternate behavior.
- Goal 6: Remove EasyPost from workshop/runtime execution by serving captured, deterministic
  shipping fixtures through the existing message contracts

### Acceptance Criteria

- [ ] The workshop spec lists every in-scope service operation and its request/response type
- [ ] The spec explains the current `apps.Integrations` singleton workflow pattern
- [ ] The spec identifies which behavior is already implemented vs planned
- [ ] `location-events` has a proposed service contract and a clear migration path from the
      current Python activity stub
- [ ] EasyPost replacement APIs are cataloged for address verification, carrier rates, shipments,
      and label printing
- [ ] The spec defines how `selected_shipment` flows end-to-end as `acme.common.v1.Shipment`
- [ ] The spec defines the fixture hierarchy and deterministic ID strategy for shipping data
- [ ] Open requirements are explicit enough to review before implementation starts

### Requirements and Motivation

The integration layer should satisfy these workshop requirements:

- **No vendor setup for core exercises:** participants should not need commerce, PIMS, inventory,
  or risk-event accounts to complete the workshop
- **Observable behavior:** stub calls should show up as Temporal workflow history and queryable
  workflow state where practical
- **Service boundary fidelity:** callers should still use Nexus service APIs so the code path looks
  like a real distributed system, not a direct test double
- **Deterministic scenarios:** facilitators need stable ways to produce invalid orders, SKU
  enrichment, primary vs alternate warehouse selection, and location-risk outcomes
- **No runtime EasyPost dependency:** EasyPost may be used by a capture script to build fixtures,
  but normal local/workshop execution should not need an EasyPost key or network access
- **Contract compatibility:** Java workflows, Python activities, Nexus operations, and optional
  Spring REST endpoints should keep the current request/response contracts where practical
- **Low reset cost:** workshop data should be resettable by terminating or recreating the
  singleton integration workflow
- **Clear promotion path:** any stubbed service should have an obvious replacement path to a real
  service later

The motivation for bringing these together is not just code reuse. It gives the workshop a single
story for external dependencies: the OMS stays composed of bounded contexts, while Temporal gives
us a durable, inspectable simulator for the systems we do not want participants to provision. This
also makes the ShippingAgent exercise easier to explain because PIMS, inventory, and
location-events all contribute facts to one recommendation path.

---

## Current State (As-Is)

### What Exists Today

`java/apps/apps-core/src/main/java/com/acme/apps/workflows/IntegrationsImpl.java` is a singleton
workflow used as an in-memory integration stub.

- Workflow type: `apps.Integrations`
- Workflow ID: `integrations`
- Task queue: `integrations`
- Namespace: `apps`
- Startup activity: `IntegrationsSetup.preloadWarehouseAddresses()`
- Query: `getState() -> GetIntegrationsStateResponse`

Nexus service handlers in `java/apps/apps-core/src/main/java/com/acme/apps/services/` expose
service-shaped operations and route calls into the singleton workflow:

```
caller workflow
  -> Nexus operation on integrations endpoint
  -> executeUpdateWithStart(workflowId="integrations")
  -> apps.Integrations update handler
  -> deterministic stubbed response
```

The `integrations` worker currently registers these Nexus service beans:

- `commerce-app-service`
- `pims-service`
- `payments-service`
- `inventory-service`

`location-events` does not use this pattern yet. Today it is a Python activity registered on the
`agents` task queue:

```python
async def get_location_events(
    request: GetLocationEventsRequest,
) -> GetLocationEventsResponse
```

The activity is stubbed and returns `RISK_LEVEL_NONE` with no events.

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

- Known item IDs map through a static catalog to SKU and brand code
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

Current stub rules:

- Warehouse addresses are pre-verified through EasyPost at `apps.Integrations` startup
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

#### EasyPost-Dependent Shipping APIs

Today shipping data is split across Java and Python EasyPost call sites:

- Java `Carriers.verifyAddress(VerifyAddressRequest)` verifies the destination address before
  fulfillment continues
- Python `EasyPostActivities.verify_address(VerifyAddressRequest)` is the same logical operation
  for the ShippingAgent/cart path
- Python `EasyPostActivities.get_carrier_rates(GetShippingRatesRequest)` creates an EasyPost
  shipment and returns all available rates to the ShippingAgent
- Java `Carriers.printShippingLabel(PrintShippingLabelRequest)` retrieves the shipment, validates
  the selected rate, buys the label, and returns tracking data

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

This removes the fulfillment-specific `SelectedShippingOption` duplication and gives the catalog
one canonical place to read the paid price, selected rate ID, shipment ID, delivery days, and
delivery date.

### Pain Points / Gaps

- There is a limit of 10 concurrent updates for a single workflow execution in Temporal. That means simulating a service under load falls over pretty quick.
- Inventory, PIMS, and location risk are connected in the ShippingAgent scenario, but that
  motivation is not captured in one place
- Runtime EasyPost calls require an API key, network access, and rate-limit management for a
  workshop path that should be deterministic
- Warehouse startup currently verifies addresses through EasyPost; this couples inventory seed
  loading to a vendor call even though the relevant IDs, coordinates, and timezones are stable
- `get_carrier_rates` creates a new shipment on every call; repeated workshop runs can produce
  different IDs and rate ordering unless responses are captured
- `printShippingLabel` currently buys through EasyPost; even with test keys, the workshop only
  needs a realistic tracking number and label URL response
- SLA and margin scenarios are now driven by `selected_shipment` fields, but the spec needs to
  describe those triggers so fixture behavior and prompts stay aligned

## Desired State (To-Be)

### Architecture Overview

The integration layer becomes the workshop's shared external-system simulator. Each service keeps a
domain-shaped API, but responses come from deterministic seeded data rather than real vendors.

The converged target is:

```text
callers
  -> Nexus service operation or Spring REST controller
  -> shared integration implementation
  -> fixture catalog / Spring cache
  -> current protobuf response type
```

Shipping fixture lookups should be implemented as a shared Spring service backed by cache. Nexus
handlers and REST controllers should be thin access paths over that service. `apps.Integrations`
can continue to host existing workflow-backed stubs where workflow history is useful, but shipping
catalog reads should not depend on a single workflow's concurrent Update capacity.

### Key Capabilities

- **Single inspectable source of stub truth:** participants can query `apps.Integrations.getState`
  and see warehouse seed state rather than hunting through test fixtures
- **Service-shaped APIs:** callers still depend on Nexus service interfaces, so the production
  boundary is preserved even though the implementation is workshop-local
- **Deterministic scenario hooks:** order ID, item ID, SKU prefix, warehouse, and coordinate inputs
  can drive predictable outcomes
- **Fixture-backed shipping:** address verification, rate lookup, shipment selection, and label
  printing are served from a local catalog instead of EasyPost
- **Dual access path:** core shipping operations can be exposed as both Nexus operations and Spring
  REST endpoints over the same implementation
- **Location-events on the same foundation:** `location-events` should use the same shared Spring
  service/cache pattern. The first pass returns an empty event list; later enrichment can use
  request inputs to hint at risk scenarios.

### EasyPost Replacement / Shipping Catalog

EasyPost should no longer be called by normal workshop/runtime flows. Instead, a capture script
uses EasyPost ahead of time to create realistic fixture data. Runtime code reads that fixture data
and returns message-compatible responses.

The catalog hierarchy should be:

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

- Start from the hardcoded warehouse addresses currently used by `OrderActivitiesImpl` and
  `IntegrationsSetup`
- Add roughly 10 additional legitimate destination addresses for richer rate coverage
- Verify every address and persist the resulting `EasyPostAddress` fields, including coordinates
  and timezone when available
- For each interesting origin/destination pair, create a shipment with the current default parcel
  assumptions and capture all returned rates
- For each captured rate, synthesize a deterministic label/tracking fixture from
  `shipment_id + rate_id`. The capture script does not need to buy labels from EasyPost.
- Write a JSON fixture database that the Java integrations service can load with stable IDs
- Avoid hand-editing captured payloads except for documented scenario fixtures

The runtime fixture loader should expose queryable metadata:

- known addresses and their fixture IDs
- known shipments and origin/destination address IDs
- rates available per shipment, including `carrier`, `service_level`, `cost`, `estimated_days`,
  `rate_id`, and `shipment_id`
- labels available per `shipment_id + rate_id`, including tracking number and label URL
- location-event fixture configuration, even though the first pass returns an empty event list
- scenario overrides applied to a request

### Shipping Catalog APIs

The same backing implementation should be callable through Nexus and Spring REST.
The preferred operations are:

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
POST /api/v1/integrations/shipping/verify-address
POST /api/v1/integrations/shipping/rates
POST /api/v1/integrations/shipping/labels
GET  /api/v1/integrations/shipping/catalog
```

REST should use the same protobuf-generated JSON shape or an exact DTO mapping so it cannot drift
from the Nexus/activity contracts.

### Scenario Behavior

Scenario behavior can come from a future global `scenarios` input, but the initial implementation
can derive scenarios from already-threaded request fields:

| Trigger | Source | Expected fixture behavior |
|---------|--------|---------------------------|
| Invalid order | `order.order_id` contains `invalid` | `commerce-app.validateOrder` returns manual correction required |
| Margin leak/spike | `selected_shipment.paid_price.units == 1` | `getShippingRates` returns rates that all exceed paid price; prompt/rule returns `MARGIN_SPIKE` |
| SLA breach | explicit `selected_shipment.easypost.selected_rate.delivery_days == 0` | `getShippingRates` returns no acceptable rate within the selected SLA; prompt/rule returns `SLA_BREACH` |
| Alternate warehouse | `findAlternateWarehouse` with current address ID | returns another catalog warehouse matching item prefixes and excluding current origin |
| Location risk | future input-derived hint, TBD | first pass returns empty events; later enrichment can return risk summaries from the same fixture/cache layer |

If/when global scenarios are added, they should be explicit metadata on the top-level order or
integration request rather than magic substrings. Until then, request-field triggers are acceptable
because they exercise the real message contracts.

### Proposed Location-Events Service

Introduce a Nexus service contract matching the existing activity contract:

```java
@Service
public interface LocationEventsService {
    @Operation
    GetLocationEventsResponse getLocationEvents(GetLocationEventsRequest request);
}
```

The service implementation should use the same shared Spring service/cache pattern as the shipping
catalog. The ShippingAgent tool can then switch from an activity tool to a Nexus tool while keeping
the LLM tool name `get_location_events` and the existing proto request/response types.

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Keep existing workflow-backed stubs where useful, but use Spring cache for catalog reads | Existing commerce/PIMS/inventory workflow history remains visible; high-volume shipping and location fixture reads avoid single-workflow Update limits | Force every stub through one singleton workflow - simpler story but hits Update concurrency limits |
| Keep service-shaped Nexus APIs | Callers exercise the same cross-namespace shape they would use with real services | Direct workflow calls from every domain - couples callers to workshop implementation details |
| Use `UpdateWithStart` for workflow-backed integration operations | The integration workflow starts lazily for commerce/PIMS/inventory callers that use workflow-backed stubs | Explicit startup script - another workshop ordering dependency |
| Treat `location-events` as an integration service using the shared Spring service/cache pattern | Risk data is external-domain context like inventory and PIMS; bringing it together clarifies the workshop architecture and avoids Python-only fixture logic | Keep it as a Python activity - simpler short-term but splits the integration story |
| Preserve the existing `get_location_events` tool name | Avoids retraining the LLM prompt and keeps ShippingAgent history readable | Rename to Java-style `getLocationEvents` - leaks service implementation style into agent tools |
| Remove payments from the workshop integration path | The order workflow path does not depend on payments; keeping it registered adds noise without workshop value | Keep payments registered but undocumented - low effort, but leaves an unused service in the story |
| Replace runtime EasyPost calls with fixture catalog reads | Removes API keys, network variance, rate limits, and live label purchasing from workshop execution | Continue using EasyPost test mode - realistic but slow, brittle, and hard to reset |
| Preserve current protobuf request/response contracts | Keeps Java workflows, Python agent tools, and REST/Nexus callers aligned while internals change | Introduce workshop-only DTOs - easier fixture modeling but creates contract drift |
| Capture all rates per shipment | The LLM may choose any rate depending on margin, SLA, or risk context | Persist only the cheapest/selected rate - insufficient for fallback and recommendation paths |
| Use `selected_shipment` as the scenario context | The values already flow from checkout to ShippingAgent and rates; no magic order ID parsing is needed for margin/SLA | Add hidden scenario strings to order IDs - convenient but opaque and easy to forget |
| Allow Nexus and REST over the same shipping implementation | Activities and Nexus operations can share fixture logic, while REST makes manual testing easier | Implement separate activity and controller logic - faster initially but guarantees drift |
| Synthesize label responses from shipment/rate fixtures | The workflow only needs deterministic tracking and label URL data; buying labels adds unnecessary capture cost and API coupling | Buy test labels for every captured rate - more realistic, but not needed for the demo |
| Expose demo fixture data for inspection | Workshop operators should be able to see addresses, shipments, rates, labels, and location-event fixture config | Keep fixture data private - simpler API surface, harder to debug demos |

### Component Design

#### `apps.Integrations` Workflow

- **Purpose:** Durable workshop stub for external APIs
- **Responsibilities:** Hold seeded integration data, serve Update handlers, expose query state
- **Interfaces:**
  - `execute(StartIntegrationsRequest)`
  - `getState() -> GetIntegrationsStateResponse`
  - Update handlers for commerce-app, PIMS, and inventory

#### Service Handlers

- **Purpose:** Preserve Nexus service boundaries for callers
- **Responsibilities:** Implement sync Nexus operations. Workflow-backed stubs call
  `executeUpdateWithStart`; catalog-backed stubs call the shared Spring service/cache directly.
- **Interfaces:** Java Nexus service implementations in `java/apps/apps-core/.../services/`

#### Shipping Catalog Service

- **Purpose:** Own the EasyPost replacement catalog and serve deterministic shipping data
- **Responsibilities:** Verify addresses from fixtures, return captured rates, print deterministic
  labels, apply scenario-specific rate mutations, expose catalog inspection
- **Interfaces:**
  - Nexus operations for `verifyAddress`, `getShippingRates`, and `printShippingLabel`
  - Optional compatibility Nexus operation for `getCarrierRates`
  - Spring REST controller over the same service methods
  - JSON fixture database loaded into Spring cache at startup

#### ShippingAgent Tool Dispatch

- **Purpose:** Let the LLM request risk and shipping data through the same tool names it uses today
- **Responsibilities:** Dispatch `get_location_events` to the integrations endpoint once
  `LocationEventsService` exists; dispatch `get_carrier_rates` to the fixture-backed
  `getShippingRates` operation while preserving the LLM-facing tool name
- **Interfaces:** Python `nexus_tool(...)` with `GetLocationEventsRequest` and
  `GetLocationEventsResponse`; Python or Java service type for `GetShippingRatesRequest` and
  `GetShippingRatesResponse`

### Data Model / Schemas

No proto change is required for the first seeded version if `LocationEventsService` reuses
`GetLocationEventsRequest` and `GetLocationEventsResponse` from
`proto/acme/fulfillment/domain/v1/shipping_agent.proto`.

No proto change should be required for the EasyPost replacement if the catalog returns the current
messages:

- `VerifyAddressRequest/Response`
- `GetShippingRatesRequest/Response`
- `PrintShippingLabelRequest/Response`
- optionally `GetCarrierRatesRequest/Response`

Potential additive change:

```protobuf
message GetIntegrationsStateResponse {
  repeated WarehouseEntry warehouses = 1;
  repeated LocationEventSeed location_event_seeds = 2;
  repeated ShippingAddressFixture shipping_addresses = 3;
  repeated ShippingShipmentFixture shipping_shipments = 4;
}
```

The workshop-facing state/query or REST inspection endpoint should expose all reference/demo data
needed to explain a run: warehouses, shipping addresses, shipments, rates, synthesized labels, and
location-event fixture configuration.

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

Existing worker registration:

```yaml
spring.temporal:
  workers:
    - task-queue: integrations
      workflow-classes:
        - com.acme.apps.workflows.IntegrationsImpl
      activity-beans:
        - integrations-setup-activities
      nexus-service-beans:
        - commerce-app-service
        - pims-service
        - payments-service
        - inventory-service
```

Planned addition:

```yaml
      nexus-service-beans:
        - commerce-app-service
        - pims-service
        - inventory-service
        - location-events-service
        - shipping-catalog-service
```

Payments is intentionally omitted from the workshop integration registration unless a future
exercise introduces payment validation.

Shipping catalog configuration:

```yaml
workshop:
  integrations:
    shipping-catalog:
      fixture-path: classpath:/fixtures/shipping-catalog.json
      mode: fixture # fixture | easypost-capture
```

`fixture` is the normal local/workshop mode. `easypost-capture` should only be used by the offline
capture script or a deliberate developer task.

---

## Implementation Strategy

### Phase 1: Document and Align Requirements

Deliverables:

- [ ] Review this spec and confirm the in-scope services
- [ ] Remove payments from the workshop integration narrative and registration unless a future
      exercise needs it
- [ ] Document the shared Spring service/cache shape for shipping catalog runtime lookups
- [ ] Document the REST endpoint names under `apps-api`
- [ ] Document the Nexus service names for shipping catalog and location-events
- [ ] Define the minimum seeded scenarios needed for the workshop

### Phase 2: EasyPost Fixture Capture

Deliverables:

- [ ] Inventory the warehouse and destination addresses that must exist in the catalog
- [ ] Add roughly 10 legitimate destination addresses for richer route/rate coverage
- [ ] Write a capture script that verifies addresses through EasyPost and persists address
      payloads, coordinates, and timezones
- [ ] For each configured origin/destination pair, capture shipment and all returned rates
- [ ] For every captured rate, generate a deterministic synthetic label/tracking payload from
      `shipment_id + rate_id`
- [ ] Write `shipping-catalog.json` with stable IDs and enough raw payload detail to debug fixture
      mismatches
- [ ] Document how to refresh fixtures intentionally without changing runtime behavior

### Phase 3: Shipping Catalog Runtime Service

Deliverables:

- [ ] Create a fixture loader and Spring cache for shipping catalog data
- [ ] Implement `verifyAddress(VerifyAddressRequest)` from fixtures
- [ ] Implement `getShippingRates(GetShippingRatesRequest)` from fixtures
- [ ] Implement `printShippingLabel(PrintShippingLabelRequest)` from fixtures
- [ ] Optionally implement `getCarrierRates(GetCarrierRatesRequest)` as a compatibility wrapper
- [ ] Add deterministic scenario mutation for `paid_price.units=1` and explicit
      `delivery_days=0`
- [ ] Expose the same implementation through Nexus operations and Spring REST endpoints
- [ ] Add REST controller endpoints for manual use and workshop scripts

### Phase 4: Location-Events Integration Service

Deliverables:

- [ ] Create `LocationEventsService` Nexus interface
- [ ] Create `LocationEventsServiceImpl` backed by the shared Spring service/cache pattern
- [ ] Return empty events and `RISK_LEVEL_NONE` in the first pass
- [ ] Leave room for future input-derived risk hints without adding scenario fields now
- [ ] Register `location-events-service` on the `integrations` worker

### Phase 5: ShippingAgent Dispatch Migration

Deliverables:

- [ ] Add a Python Nexus service stub for `LocationEventsService`
- [ ] Change the ShippingAgent tool definition from `activity_tool` to `nexus_tool`
- [ ] Keep LLM tool name as `get_location_events`
- [ ] Keep request/response protos unchanged
- [ ] Remove or de-register the local Python activity only after the Nexus path is verified
- [ ] Move `get_carrier_rates` to the fixture-backed shipping catalog without changing the
      LLM-facing tool name
- [ ] Ensure `selected_shipment` is attached by workflow context and not invented by the LLM

### Phase 6: Fulfillment Carrier Migration

Deliverables:

- [ ] Replace Java `CarriersImpl.verifyAddress` EasyPost calls with fixture-backed verification
- [ ] Replace Java `CarriersImpl.printShippingLabel` EasyPost calls with fixture-backed label
      lookup
- [ ] Remove EasyPost key as a runtime requirement for local/workshop fulfillment workers
- [ ] Keep failure behavior for invalid address/rate IDs deterministic and non-retryable

Initial implementation should deliver Phases 2-6 together. Splitting `location-events` from
EasyPost replacement would leave the workshop dependent on the same scattered integration paths
this spec is intended to remove.

### Phase 7: Workshop Exercise Material

Deliverables:

- [ ] Add exercise notes explaining why integrations are workflow-backed
- [ ] Add a query/check script for the `apps.Integrations` workflow state
- [ ] Add a scenario that demonstrates inventory lookup, alternate warehouse lookup, and
      location risk in one ShippingAgent run
- [ ] Add a scenario that demonstrates `paid_price.units=1` margin leak/spike
- [ ] Add a scenario that demonstrates `delivery_days=0` SLA breach
- [ ] Add a script or REST example that lists catalog addresses, rates, shipments, and labels

### Critical Files / Modules

To Create:

- `java/oms/src/main/java/com/acme/oms/services/LocationEventsService.java` - Nexus interface
- `java/oms/src/main/java/com/acme/oms/services/ShippingCatalogService.java` - Nexus interface
- `java/apps/apps-core/src/main/java/com/acme/apps/services/LocationEventsServiceImpl.java` -
  Nexus handler
- `java/apps/apps-core/src/main/java/com/acme/apps/services/ShippingCatalogServiceImpl.java` -
  Nexus handler or shared service adapter
- `java/apps/apps-api/src/main/java/com/acme/apps/controllers/ShippingCatalogController.java` -
  REST controller
- `java/apps/apps-core/src/main/resources/fixtures/shipping-catalog.json` - captured fixture
  database
- `scripts/capture-easypost-fixtures.*` - offline fixture capture script
- `python/fulfillment/src/services/location_events_service.py` - Python Nexus client service type
- `python/fulfillment/src/services/shipping_catalog_service.py` - Python Nexus client service type

To Modify:

- `java/apps/apps-core/src/main/java/com/acme/apps/workflows/Integrations.java` - keep existing
  workflow-backed commerce/PIMS/inventory update contracts
- `java/apps/apps-core/src/main/java/com/acme/apps/workflows/IntegrationsImpl.java` - expose
  queryable demo data as needed for workshop inspection
- `java/apps/apps-core/src/main/resources/acme.apps.yaml` - register location-events and
  shipping-catalog service beans; omit payments for workshop mode
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/CarriersImpl.java` -
  replace EasyPost address and label calls with fixture-backed service calls
- `python/fulfillment/src/agents/workflows/shipping_agent.py` - switch tool dispatch to Nexus
- `python/fulfillment/src/agents/activities/easypost.py` - remove or convert to fixture-backed
  adapter after the Nexus path is verified
- `python/fulfillment/src/workers/fulfillment_worker.py` - remove activity registration after
  migration
- `python/fulfillment/src/workers/easypost_worker.py` - remove runtime EasyPost worker once no
  activities depend on it

---

## Testing Strategy

### Unit Tests

- Commerce-app: `invalid` order ID sets `manual_correction_needed=true`
- PIMS: known item IDs map to expected SKU and brand code; unknown item IDs map to `ELEC-*`
- Inventory: SKU prefixes resolve to expected primary warehouse
- Inventory: alternate lookup excludes current EasyPost address ID
- Inventory lifecycle: hold/reserve/deduct/release return stable stub IDs/results
- Shipping catalog: known address returns a verified `EasyPostAddress` with stable ID,
  coordinates, timezone, and residential flag
- Shipping catalog: unknown address fails deterministically with the same non-retryable semantics
  callers expect from verification failure
- Shipping catalog: origin/destination address pair returns the expected deterministic
  `shipment_id` and all captured rates
- Shipping catalog: `shipment_id + rate_id` returns deterministic tracking number and label URL
- Shipping catalog: invalid `rate_id` for a shipment returns an invalid-rate error
- Shipping catalog: explicit `selected_shipment.easypost.selected_rate.delivery_days=0` is
  preserved and triggers SLA-breach fixture behavior
- Shipping catalog: `selected_shipment.paid_price.units=1` triggers margin leak/spike fixture
  behavior without changing message contracts
- Location-events: first pass returns `RISK_LEVEL_NONE`, empty events, and echoes the request
  window/timezone
- Location-events: fixture configuration is visible for future enrichment even when no events are
  returned

### Integration Tests

- `processing.Order` calls commerce-app and PIMS through the integrations endpoint
- `fulfillment.Order` calls inventory lifecycle operations through the integrations endpoint
- `fulfillment.Order` validates addresses and prints labels without a runtime EasyPost key
- `ShippingAgent` calls inventory lookup, carrier rates, location events, and alternate warehouse
  lookup without changing the public tool names
- `ShippingAgent` receives every captured rate for a shipment and can choose any returned
  `recommended_option_id`
- REST and Nexus shipping catalog calls return identical payloads for the same request when both
  access paths are enabled
- REST and Nexus location-events calls return identical empty-risk payloads in the first pass
- `apps.Integrations` starts lazily through `UpdateWithStart` and remains queryable

### Validation Checklist

- [ ] Existing processing and fulfillment workflow tests pass
- [ ] ShippingAgent tests pass with the Nexus-backed `get_location_events` tool
- [ ] ShippingAgent tests pass with fixture-backed `get_carrier_rates`
- [ ] Fulfillment label-printing tests pass without EasyPost
- [ ] Temporal UI shows one long-running `apps.Integrations` workflow
- [ ] Workshop can inspect location-event fixture configuration even though first pass returns no
      events
- [ ] Workshop scenario can demonstrate margin leak/spike with `paid_price.units=1`
- [ ] Workshop scenario can demonstrate SLA breach with explicit `delivery_days=0`
- [ ] Local startup succeeds without `EASYPOST_API_KEY` in fixture mode

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| `location-events` migration introduces cross-language Nexus friction | Medium | Medium | Implement it through the same shared Spring service/cache pattern and add parity tests before removing the Python activity |
| Single integration workflow becomes a dumping ground | Medium | Medium | Limit it to workshop stubs and document promotion criteria for real services |
| Seeded behavior becomes too artificial for the ShippingAgent prompt | Medium | Medium | Keep first-pass location events empty; add realistic event titles, categories, ranks, and windows only when enrichment is designed |
| EasyPost warehouse verification slows or blocks workshop startup | High | Medium | Remove runtime verification; load precomputed address fixtures |
| Fixture capture script accidentally changes stable IDs | Medium | Medium | Generate deterministic IDs from address/route/rate keys and review fixture diffs |
| Captured rates do not naturally match a desired SLA scenario | Medium | Medium | Mutate copied rate payloads on demand based on scenario inputs |
| REST and Nexus implementations drift | Medium | Medium | Put fixture logic in one Spring service and keep controllers/handlers thin |
| Removing EasyPost hides real integration errors | Low | Medium | Keep capture mode documented and make fixture failures explicit/non-retryable |
| Payments remains registered but undocumented in the exercise | Low | High | Remove payments from workshop registration unless the workshop narrative needs it |

---

## Dependencies

### External Dependencies

- Temporal Nexus support in Java and Python workers
- Existing protobuf-generated Java and Python types
- EasyPost test-mode API access only for the offline fixture capture script
- Local fixture database loaded by Java integrations/fulfillment services

### Cross-Cutting Concerns

- `processing.Order` depends on `commerce-app` and `pims`
- `fulfillment.Order` depends on `inventory`
- `fulfillment.Order` depends on address verification and label printing
- `ShippingAgent` depends on `inventory`, fixture-backed carrier rates, and `location-events`
- Workshop scripts and docs should treat the integrations endpoint as part of the local platform

### Rollout Blockers

- Confirm the Java/Python Nexus wiring for the new `location-events` service
- Confirm whether generated code can reference `GetLocationEventsRequest/Response` from the Java
  apps module without additional build changes

---

## Resolved Decisions & Notes

### Resolved Decisions

- [x] `location-events` uses the same shared Spring service/cache pattern as shipping catalog
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
- [x] REST endpoints live in `apps-api`
- [x] canonical fixture JSON lives under `apps-core/src/main/resources/fixtures` so it is packaged
      for local and Kubernetes runs
- [x] EasyPost replacement and `location-events` migration should be delivered together

### Implementation Notes

- The current `IntegrationsImpl` item catalog uses uppercase item IDs such as `ITEM-ELEC-001`.
  The commerce REST product endpoint still returns lowercase `item-{n}` values; workshop scripts
  should use known catalog IDs when deterministic SKU/warehouse behavior matters.
- `lookupInventoryAddress` currently matches only the first item SKU. If multi-item orders are
  important for the workshop, this needs a requirement: split by warehouse, reject mixed prefixes,
  or choose a primary warehouse deterministically.
- The ShippingAgent already supports `nexus_tool(...)`, so moving `get_location_events` to Nexus
  should be a localized dispatch change once a Python service type exists.
- The Python converter must preserve explicit zero values for `delivery_days`; `delivery_days=0`
  is meaningful scenario input, not an absent value.
- `selected_shipment` should be supplied by workflow/request context. The LLM should not be
  responsible for inventing selected shipment fields when calling `get_carrier_rates`.
- The current default parcel is 1 lb, 6x6x4 inches. Fixture capture should use that parcel unless
  the message contracts grow parcel fields later.

---

## References & Links

- `java/apps/apps-core/src/main/java/com/acme/apps/workflows/IntegrationsImpl.java`
- `java/apps/apps-core/src/main/java/com/acme/apps/services/InventoryServiceImpl.java`
- `java/apps/apps-core/src/main/java/com/acme/apps/services/ProductInformationManagementServiceImpl.java`
- `java/apps/apps-core/src/main/java/com/acme/apps/services/CommerceAppServiceImpl.java`
- `python/fulfillment/src/agents/activities/location_events.py`
- `python/fulfillment/src/agents/activities/easypost.py`
- `python/fulfillment/src/agents/workflows/shipping_agent.py`
- `java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/activities/CarriersImpl.java`
- `proto/acme/fulfillment/domain/v1/shipping_agent.proto`
- `proto/acme/fulfillment/domain/v1/workflows.proto`
- `proto/acme/common/v1/values.proto`
- `specs/fulfillment/location-events/spec.md`
