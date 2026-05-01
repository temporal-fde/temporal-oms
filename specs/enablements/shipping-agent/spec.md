# ShippingAgent Integration Spec (Enablements Path)

**Feature Name:** ShippingAgent integration for the enablements/scenario path
**Status:** Implemented for current workshop scenarios; Nexus integration reroute is follow-up
**Owner:** Temporal FDE Team
**Created:** 2026-04-27
**Updated:** 2026-04-29

> **Note:** The parent `worker-version-enablement/` directory is being renamed to `enablements/`
> to reflect its broader scope. This spec should move with that rename.

---

## Overview

Enablements and scenario scripts submit synthetic orders that flow through
`apps.Order` -> `fulfillment.Order` -> `ShippingAgent`. The original gap in this path was that
orders did not carry selected-shipment context, so the ShippingAgent could not reliably exercise
margin or SLA reasoning.

That gap is now closed for the current scripts:

- Each scenario run generates a unique order/workflow ID.
- Each scenario run generates a unique customer ID, which keeps the long-running ShippingAgent
  workflow isolated per order.
- Orders can include `selectedShipment.paidPriceCents`.
- Orders can include explicit `selectedShipment.deliveryDays`, including zero.
- ShippingAgent receives that context as `RecommendShippingOptionRequest.selected_shipment`.
- Runtime shipping and location-event tool calls go through `enablements-api`, not EasyPost.

The Nexus integration handlers for commerce-app, PIMS, and inventory now use `enablements-api` as
their backend.

---

## Current Behavior

### Scenario Triggers

| Scenario | Input trigger | Expected behavior |
|---|---|---|
| Normal valid order | `selectedShipment.paidPriceCents` aligned with fixture rates | ShippingAgent can return `PROCEED` without spontaneous margin leak |
| Margin spike | `selectedShipment.paidPriceCents=1` | ShippingAgent must call `find_alternate_warehouse`, then can finalize `MARGIN_SPIKE` if no alternate resolves margin |
| SLA breach | explicit `selectedShipment.deliveryDays=0` | ShippingAgent must call `find_alternate_warehouse`, then can finalize `SLA_BREACH` if no alternate meets the SLA |

### Shipping Runtime

ShippingAgent keeps the LLM-facing tool name `get_carrier_rates`, but the activity implementation
is now `ShippingActivities.get_carrier_rates` on the `fulfillment-shipping` task queue. It calls
`enablements-api` and returns fixture-backed rates.

The activity accumulates rate options from both primary and alternate warehouse calls so the final
`RecommendShippingOptionResponse.options` contains whichever option the LLM recommends.

### Location Events

The current path calls `enablements-api` and returns `RISK_LEVEL_NONE`, an empty event list, and
the echoed request window/timezone. Real weather/event enrichment is a separate near-term follow-up.

---

## Follow-Up Scope

- Add richer location-event enrichment behind `enablements-api`.
- Add fixture-state query examples or scripts for workshop operators.

---

## References

- [Workshop integrations spec](../integrations/spec.md)
- [ShippingAgent spec](../../fulfillment-order/shipping-agent/spec.md)
- [Scenario scripts](../../../scripts/scenarios/README.md)
- [`ShippingActivities`](../../../python/fulfillment/src/agents/activities/shipping.py)
- [`ShippingAgent` workflow](../../../python/fulfillment/src/agents/workflows/shipping_agent.py)
