# PRD: OMS Smart Fulfillment — v2

**Scope**: Fulfillment phase of the Order Management System
**Status**: In development

---

## 1. Executive Summary & Scope

Our current Order Management System (OMS) successfully utilizes Temporal to aggregate inputs, validate data, and capture payments during the **Processing** phase. The system currently drops an enriched Order payload onto the `order-fulfillment` Kafka topic.

**Scope**: This project demonstrates replacing the legacy downstream fulfillment process with a new **Temporal Smart Fulfillment Workflow**. By integrating an LLM-driven "Shipping Agent," this workflow will dynamically handle rate validations, protect business margins from stale shipping quotes, and orchestrate the long-running process of inventory allocation, label generation, and delivery tracking.

See [V2 architecture diagram](oms-v2-architecture.mmd) for the static view of all namespaces and integration points, and [V2 order flow](oms-v2-order-flow.mmd) for the full sequence.

---

## 2. Business Value & Drivers

Our existing fulfillment system is highly deterministic and struggles with the messy realities of supply chains, leading to high support costs and margin leakage. We aim to leverage an LLM paired with Temporal's durable execution to solve these specific business problems:

- **Eradicating Margin Leakage**: Shipping quotes generated at checkout frequently become stale or spike in price by the time an order is processed. The business typically eats this cost. The LLM will intelligently re-shop delivery routes during fulfillment to protect margins without violating the promised customer SLA.
- **Dynamic Logistics Routing**: Standard carrier APIs do not account for local weather or infrastructure events. The LLM Agent will act as an abstraction layer, ingesting unstructured data (weather alerts, news) to filter and rank delivery options proactively.
- **Automated Exception Handling & HitL**: Unstructured delivery notes and localized carrier exceptions currently require manual triage. The LLM will parse, standardize, and summarize exceptions for the Support team when human-in-the-loop intervention is strictly necessary.

---

## 3. Core Use Cases

### Input Criteria

In all cases, the following criteria are used to determine shipping options:

- **Inventory Location**: The agent always calls `lookup_inventory_location` to resolve the warehouse origin from inventory. An inventory location ID can be forced at runtime to skip discovery.
- **Selected Items (sku ids)**: SKUs can be inventoried across N locations. The inventory will impact what is actually available for shipping costs.
- **Destination (address)**: The destination address for the parcels, verified via the `enablements-api` before shipping rate queries.

### Use Case 1: Cart Usage (Setting the Customer Contract)

As a customer, I should be able to view current, reliable shipping options that account for real-world constraints.

- **Trigger**: Customer navigates to the checkout/shipping screen.
- **Action (Temporal Update / Sync API)**: The frontend calls `recommendShippingOption` on the **Shipping Agent** workflow.
  - The Agent uses `get_carrier_rates` tool → `enablements-api /api/v1/integrations/shipping/rates` to fetch available carrier options.
  - The Agent uses `get_location_events` tool → `enablements-api /api/v1/integrations/location-events` to fetch supply chain risk data (weather, infrastructure events) for the destination.
  - The LLM filters out routes severely impacted by disruptions and returns a `ShippingRecommendation` with curated options and a `RecommendationOutcome`.
- **The Handoff**: The customer selects an option. The frontend passes the `rate_id`, the `delivery_days` SLA, and the `paid_price` into the OMS as the binding "Customer Contract" via `SelectedShipment`.

### Use Case 2: Placing an Order (The Fulfillment Workflow)

When an order finishes Processing, it moves to Fulfillment. This workflow ensures the order is delivered on time while actively protecting company margins.

- **Trigger**: `apps.Order` calls `validateOrder` via `UpdateWithStart` (Nexus) to kick off `fulfillment.Order` early, then signals `fulfillOrder` once processing completes.
- **Step 1: Validate Address (`validateOrder` Update)**
  - The workflow verifies the shipping address via `enablements-api /api/v1/integrations/shipping/verify-address`.
  - The verified EasyPost address ID is stored in workflow state for downstream rate queries.
- **Step 2: Rate Validation & Margin Protection**
  - The `ShippingAgent` is called via `recommendShippingOption` Update with the original `selected_shipment` context.
  - The agent calls `get_carrier_rates` and `get_location_events` through `enablements-api` and returns a `ShippingRecommendation`.
  - Possible outcomes (`RecommendationOutcome`):
    - `PROCEED`: Rate valid and within margin — proceed.
    - `CHEAPER_AVAILABLE`: Cheaper option found within SLA — swap and save margin.
    - `FASTER_AVAILABLE`: Faster option found within margin — swap.
    - `MARGIN_SPIKE`: Cost exceeds `shipping_margin` — select best-effort fallback, write `margin_leak` Search Attribute with the cost delta.
    - `SLA_BREACH`: No option meets the customer's transit SLA — select cheapest available, alert logistics team.
- **Step 3: Allocate Inventory (Activity)**
  - Reserve the physical items at the warehouse using the finalized routing details.
- **Step 4: Generate Label (Activity)**
  - Call `enablements-api /api/v1/integrations/shipping/labels` (`PrintShippingLabel`) with the final `rate_id` and EasyPost `shipment_id`. Save the tracking number to workflow state.
- **Step 5: Wait for Delivery (Workflow Await + Signal)**
  - The workflow pauses execution (`Workflow.await`).
  - It listens for a `notifyDeliveryStatus` Signal carrying a `NotifyDeliveryStatusRequest`.
  - `DELIVERY_STATUS_DELIVERED`: Workflow completes.
  - `DELIVERY_STATUS_CANCELED`: Notify customer of delivery failure.

---

## 4. Technical Implementation

### Integration Layer: `enablements-api`

All external service calls are abstracted behind the **`enablements-api`** service (`java/enablements/enablements-api`). Neither workflow workers nor the ShippingAgent call EasyPost or event-data providers directly. Instead, they code to proto-defined contracts and route calls through this integration layer.

- **`enablements-core`** (`java/enablements/enablements-core`) — provides the `EnablementsIntegrationsClient` interface used by Processing and Enablements Java workers.
- **`enablements-api`** — the backing REST service implementing those contracts. For workshops it serves fixture-backed data; for production it routes to real carrier and event-data credentials.
- **Python `EnablementsIntegrationsClient`** (`python/fulfillment/src/services/enablements_integrations.py`) — the Python equivalent used by the ShippingAgent and fulfillment activities.

**Endpoints exposed by `enablements-api`:**

| Domain | Endpoint | External provider (behind abstraction) |
|---|---|---|
| Address verification | `GET /api/v1/integrations/shipping/verify-address` | EasyPost |
| Carrier rates | `GET /api/v1/integrations/shipping/rates` | EasyPost |
| Label printing | `GET /api/v1/integrations/shipping/labels` | EasyPost |
| Location events (SCRM) | `GET /api/v1/integrations/location-events` | PredictHQ-compatible |
| Order validation | `POST /api/v1/integrations/commerce-app/validate-order` | Commerce App |
| PIMS enrichment | `GET /api/v1/integrations/pims/enrich-order` | PIMS |
| Inventory operations | `GET/POST /api/v1/integrations/inventory/*` | Inventory Service |

### Version Considerations

- We can accept the current `apps.Order` and `processing.Order` versioning behavior as **PINNED** and drain off currently running Orders.
- New `processing.Order` versions will no longer call the fulfillment activity that places a message on the Kafka queue.
- `apps.Order` starts a new `fulfillment.Order` Nexus operation *immediately* upon execution via `UpdateWithStart` (`validateOrder`).
  - `fulfillment.Order` verifies the address and holds inventory early, but suspends until the order has been "processed".
  - After an order is "processed," `apps.Order` calls `fulfillOrder` Update on the underlying `fulfillment.Order` to begin fulfillment, passing the enriched `ProcessedOrder`.

### Shipping Agent

The Shipping Agent (`ShippingAgent` workflow) lives inside the **fulfillment** Domain Bounded Context (Python).

- The Shipping Agent is a **READ** — it does not mutate application state.
- Workflow ID is `customer_id` — one long-running agent per customer, caching results across calls.
- Cache key is derived from `(from_address.easypost_address.id, destination postal code + country, sorted items, selected_shipment context)`. A cache hit returns the stored `ShippingOptionsResult` with `cache_hit=true`, skipping the LLM/tool loop entirely.
- Default cache TTL is 1800 seconds (30 minutes).
- Computation is performed inside `recommendShippingOption` Update — the `UpdateID` is the idempotency token for deduplication.
- The agent lifetime is scoped to the `apps.Order` lifecycle.

**Agent Tools (all routed through `enablements-api`):**

| Tool | Activity | Endpoint |
|---|---|---|
| `get_carrier_rates` | `ShippingActivities.get_carrier_rates` (`fulfillment-shipping` task queue) | `GET /api/v1/integrations/shipping/rates` |
| `get_location_events` | `ShippingActivities.get_location_events` | `GET /api/v1/integrations/location-events` |
| `lookup_inventory_location` | `ShippingActivities.lookup_inventory_location` | `GET /api/v1/integrations/inventory/lookup-address` |
| `find_alternate_warehouse` | `ShippingActivities.find_alternate_warehouse` | `GET /api/v1/integrations/inventory/alternate-warehouse` |

**Access**: The Shipping Agent is accessible from:
- REST API (via `apps-api`)
- Workflow call (via Nexus `recommendShippingOption` Update)

### `fulfillment.Order` Workflow

**Workflow Start — `StartOrderFulfillmentRequest`**

```
StartOrderFulfillmentRequest {
  order_id:    <string>
  customer_id: <string>
  options: {
    fulfillment_timeout_secs: <integer>   // optional
  }
  selected_shipment: {                    // acme.common.v1.Shipment — customer's checkout selection
    easypost: {
      shipment_id:   <string>
      selected_rate: {
        rate_id:                   <string>
        delivery_days:             <integer>   // optional
        delivery_date:             <Timestamp> // optional
        delivery_date_guaranteed:  <boolean>
      }
    }
    paid_price: {                         // optional; customer's paid price
      currency: <string>                  // ISO 4217
      units:    <integer>                 // minor currency units
    }
    delivery_date: <Timestamp>            // optional
  }
  placed_order: {                         // PlacedOrder
    order_id:    <string>
    customer_id: <string>
    items: [{
      item_id:    <string>
      sku_id:     <string>
      brand_code: <string>
      quantity:   <integer>
    }]
    shipping_address: <Address>           // acme.common.v1.Address
  }
}
```

**`validateOrder` Update** — enables `UpdateWithStart` so upstream callers can verify the address and kick off the workflow before processing completes.

```
ValidateOrderRequest {
  order_id: <string>
  address:  <Address>
}

ValidateOrderResponse {
  address: <Address>    // easypost_address populated after verification
}
```

**`fulfillOrder` Update** — triggered by `apps.Order` once processing completes.

```
FulfillOrderRequest {
  processed_order: {
    order_id:    <string>
    customer_id: <string>
    items: [{
      item_id:            <string>
      sku_id:             <string>
      brand_code:         <string>
      quantity:           <integer>
      warehouse_id:       <string>   // optional; populated post-processing
      warehouse_location: <string>   // optional
    }]
  }
  selected_shipment: <Shipment>      // optional; falls back to workflow start args
}
```

**`FulfillOrderResponse`** — returned to the `fulfillOrder` Update caller.

```
FulfillOrderResponse {
  tracking_number:    <string>
  shipping_selection: {
    option_id:           <string>
    rate_id:             <string>
    carrier:             <string>
    service_level:       <string>
    actual_price:        <Money>
    margin_delta_cents:  <integer>   // overage in minor units; set when actual > shipping_margin
    is_fallback:         <boolean>
    fallback_reason:     <string>
  }
}
```

**Workflow Execution Steps**

1. Load `FulfillmentOptions` via `LocalActivity`: includes `shipping_margin` (Money) and Nexus endpoint names for the integrations and ShippingAgent services.
2. Hold inventory — `holdItems` Activity places a soft hold on items given `placed_order`.
3. Wait for `fulfillOrder` Update.
   - If `cancelOrder` Signal arrives or the order times out, use a detached Scope to release the hold via `releaseHold` Activity.
4. Allocate inventory — `reserveItems` Activity upgrades the hold to a reservation.
5. Shipping validation & margin comparison via `ShippingAgent`:
   - Call `recommendShippingOption` Update on the ShippingAgent (via Nexus).
   - The agent calls `get_carrier_rates` and `get_location_events` through `enablements-api`.
   - Act on the returned `RecommendationOutcome` (see Use Case 2 above).
   - Write `margin_leak` Search Attribute if outcome is `MARGIN_SPIKE`.
6. Print shipping label — `printShippingLabel` Activity calls `enablements-api /api/v1/integrations/shipping/labels` with the final `shipment_id` and `rate_id`.
7. Deduct inventory — `deductInventory` Activity. (Label printing and deduction may execute concurrently.)
8. Await `notifyDeliveryStatus` Signal:
   - `DELIVERY_STATUS_DELIVERED`: Complete the workflow.
   - `DELIVERY_STATUS_CANCELED`: Notify customer of delivery failure.

---

## 5. Data Specifications

### `fulfillment.Order` Workflow Start (via Nexus from `apps.Order`)

```json
{
  "order_id": "ord_55102",
  "customer_id": "cust_88291",
  "selected_shipment": {
    "easypost": {
      "selected_rate": {
        "rate_id": "rate_abc123",
        "delivery_days": 3,
        "delivery_date_guaranteed": false
      }
    },
    "paid_price": {
      "currency": "USD",
      "units": 800
    }
  },
  "placed_order": {
    "order_id": "ord_55102",
    "customer_id": "cust_88291",
    "items": [
      {
        "item_id": "ITEM-123",
        "sku_id": "SKU-999",
        "brand_code": "BRND-A",
        "quantity": 1
      }
    ],
    "shipping_address": {}
  }
}
```

### `ShippingRecommendation` (ShippingAgent output)

```json
{
  "outcome": "PROCEED",
  "recommended_option_id": "rate_abc123",
  "reasoning": "Original rate is valid and within margin. No supply chain disruptions detected.",
  "margin_delta_cents": 0,
  "origin_risk_level": "RISK_LEVEL_NONE",
  "destination_risk_level": "RISK_LEVEL_LOW"
}
```

---

> **Previous**: [v1 — Order Processing](prd-v1-order-processing.md) established the Temporal-based Processing phase and outputs to the `order-fulfillment` Kafka topic.
