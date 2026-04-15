# ShippingAgent Workflow Specification

**Feature Name:** `ShippingAgent` — AI-Powered Carrier Rate Selection
**Status:** Draft — Not Started
**Owner:** Temporal FDE Team
**Created:** 2026-04-15
**Updated:** 2026-04-15

---

## Overview

### Executive Summary

_To be written._

The `ShippingAgent` is called by `fulfillment.Order` via a Nexus operation in the V2 shipping path of the `fulfillOrder` Update handler. Its interface is partially defined in `proto/acme/fulfillment/domain/v1/shipping_agent.proto`.

---

## Goals & Success Criteria

_To be written._

---

## Current State (As-Is)

- `shipping_agent.proto` exists with a `StartShippingAgentRequest`, `CalculateShippingOptionsRequest/Response`, and `GetLocationEventsRequest/Response` (for PredictHQ risk data)
- `fulfillment.Order` V1 calls `DeliveryService.getCarrierRates()` directly; V2 will call `ShippingAgent` via Nexus instead
- `ShippingAgent` is not yet implemented

---

## Open Questions & Notes

### Questions for Tech Lead / Product

- [ ] Is `ShippingAgent` a long-running workflow (per customer) or a short-lived per-request operation?
- [ ] What LLM drives the agent reasoning? Claude via Anthropic API?
- [ ] What is the Nexus endpoint name and namespace for `ShippingAgent`?
- [ ] How does `ShippingAgent` relate to the existing `CalculateShippingOptionsRequest` in `shipping_agent.proto`?
- [ ] What location risk data sources feed the agent (PredictHQ confirmed)?

---

## References & Links

- [shipping_agent.proto](../../../proto/acme/fulfillment/domain/v1/shipping_agent.proto)
- [fulfillment.Order spec](../fulfillment-order-workflow/spec.md) — Phase 7 describes how `fulfillment.Order` calls `ShippingAgent` via Nexus
