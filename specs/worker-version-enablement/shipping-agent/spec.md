# ShippingAgent Integration Spec (Enablements Path)

**Feature Name:** ShippingAgent integration for the enablements load-generation path
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-27
**Updated:** 2026-04-27

> **Note:** The parent `worker-version-enablement/` directory is being renamed to `enablements/`
> to reflect its broader scope. This spec will move with the rename.

---

## Overview

The enablements load-generator submits synthetic orders to demonstrate worker versioning during
live sessions. Those orders flow through `apps.Order` → `fulfillment.Order` → `ShippingAgent`.
However, as of today, the generator never sets `customer_paid_price` or `transit_days_sla` in
the orders it submits. The result is that `ShippingAgent` silently skips its margin and SLA
reasoning for every enablements order, and `find_alternate_warehouse` — the most interesting
branch in the agentic loop — is never triggered.

This spec documents the gap, traces the root cause, and defines what must change in the
load-generation layer to exercise the full ShippingAgent path.

---

## Current State (As-Is)

### The gap

Three fields are needed by `ShippingAgent`'s reasoning rules. None of them are populated when
an order originates from the enablements load-generator.

| Field in `CalculateShippingOptionsRequest` | Expected source | Actual value (enablements path) | Effect on ShippingAgent |
|---|---|---|---|
| `customer_paid_price` | `StartOrderFulfillmentRequest.selected_shipping.price` | `Money{units=0}` (proto default — never set) | `build_system_prompt` hits else-branch: "No customer paid price — skip margin spike logic." MARGIN_SPIKE rule disabled. |
| `selected_shipping_option_id` | `StartOrderFulfillmentRequest.selected_shipping.option_id` | `""` (empty string) | No routing effect, but the agent has nothing to compare rates against. |
| `transit_days_sla` | Not present in `StartOrderFulfillmentRequest` at all | `0` (never set in `fulfillment.OrderImpl`) | SLA rule disabled: "No transit SLA specified." SLA_BREACH rule disabled. |

Net effect: `find_alternate_warehouse` is structurally unreachable through the enablements path.
Every order gets `outcome=PROCEED` unless EasyPost returns no rates at all.

### Root cause trace

```
enablements.OrderActivitiesImpl.callOrderEndpoint()          [line 99]
  → SubmitOrderRequest { customer_id, order { items, shipping_address } }
  → NO shipping price, NO selected option, NO SLA
        ↓
apps.OrderImpl.execute()                                      [line 123]
  → StartOrderFulfillmentRequest { order_id, customer_id, placed_order }
  → selected_shipping NOT set → proto default SelectedShippingOption{}
        ↓
fulfillment.OrderImpl.fulfillOrder()                         [line 234]
  → state.getArgs().getSelectedShipping().getPrice()
  → returns Money{units=0, currency=""}  (proto default)
        ↓
LlmActivities.build_system_prompt()                          [llm.py:102]
  → r.customer_paid_price.units > 0  →  False
  → "MARGIN RULE: No customer paid price — skip margin spike logic."
```

### What the proto already supports

The fields exist — the data just never flows into them:

- `StartOrderFulfillmentRequest.selected_shipping: SelectedShippingOption`
  - `option_id: string`
  - `price: acme.common.v1.Money`  ← maps to `customer_paid_price`
- `CalculateShippingOptionsRequest.transit_days_sla: optional int32`  ← defined, never set
- `fulfillment.OrderImpl` already reads and forwards both fields correctly once set

No proto changes are required. The gap is entirely in the data flowing through.

---

## Desired State (To-Be)

Enablements orders arrive at `ShippingAgent` with a real `customer_paid_price` — a value low
enough that real EasyPost rates will reliably exceed it, triggering MARGIN_SPIKE →
`find_alternate_warehouse`. The alternate warehouse call and the enforcement rejection/retry
path (ShippingAgent Phase 6) become visible in Temporal UI history during live sessions.

### Why `customer_paid_price=1` (1 cent) is the right trigger

Any real EasyPost shipment rate exceeds 1 cent. Setting `customer_paid_price.units=1` is a
deterministic, no-guesswork way to trigger MARGIN_SPIKE on every single enablements order,
without EasyPost stubbing or test-specific code in the production path. `find_alternate_warehouse`
then fires, returns empty (no alternate warehouse in seed data), and the agent finalizes
`MARGIN_SPIKE` — the complete interesting path, visible end-to-end in workflow history.

### What changes (deferred — separate Claude session)

The propagation chain needs one additional link. Two options:

**Option A — Hardcode in `apps.OrderImpl` (simpler, workshop-appropriate)**
In `apps.OrderImpl` before calling `fulfillment.fulfillOrder`, set:
```
StartOrderFulfillmentRequest.selected_shipping.price = Money{units=1, currency="USD"}
```
No proto changes. No enablements changes. Every order from any caller gets the trigger price.
Appropriate for workshop/demo purposes where all orders should exercise the full agent path.

**Option B — Thread through from `SubmitOrdersRequest` (more realistic, more work)**
1. Add `shipping_price_cents: optional int64` to `SubmitOrdersRequest` (enablements proto)
2. `enablements.OrderActivitiesImpl` passes it to apps via `SubmitOrderRequest` (apps proto also needs the field)
3. `apps.OrderImpl` reads it and sets `selected_shipping.price` accordingly
4. `fulfillment.OrderImpl` already reads it correctly — no change needed

Option A is recommended for the workshop. Option B is the production-correct path.

---

## Implementation Strategy

### Phase 1 — Load-generation changes

> **Deferred to a separate Claude session.**
> ShippingAgent Phase 6 (enforcement hardening) is complete ✅ — the Python side is ready.
> This phase covers the Java-side data flow fix.

Recommended approach: **Option A** (hardcode in `apps.OrderImpl`)

- [ ] In `apps.OrderImpl.execute()`, set `selected_shipping.price = Money{units=1, currency="USD"}`
      on the `StartOrderFulfillmentRequest` before calling `fulfillment.validateOrder` (line 140)
      and `fulfillment.fulfillOrder` (line 172)
- [ ] Verify in Temporal UI that `find_alternate_warehouse` appears in ShippingAgent workflow
      history during an enablements run
- [ ] Optionally: also set `transit_days_sla` in `CalculateShippingOptionsRequest` inside
      `fulfillment.OrderImpl.fulfillOrder()` — a hardcoded value (e.g. 3 days) would also
      demonstrate the SLA path, but MARGIN_SPIKE is higher priority

---

## Dependencies

- **ShippingAgent Phase 6** — prompt hardening + post-loop enforcement — ✅ Complete
- **Existing load-generation spec** (`load-generation/spec.md`) — Phase 1 of this spec augments
  the load-generation layer; changes should be coordinated with that spec

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Hardcoded price in `apps.OrderImpl` affects non-enablements callers | Low | Low | `apps.OrderImpl` is the storefront/demo app, not a production service; the price is intentionally synthetic for workshop purposes |
| `find_alternate_warehouse` Nexus call fails in local k8s (integrations endpoint not registered) | Medium | Medium | Integrations endpoint must be registered in the local cluster before the enablements session; add to session pre-flight checklist |
| EasyPost rate fetch fails during enablements demo (network/quota) | High | Low | Session pre-flight: verify EasyPost test key is active and rate-limit headroom exists |

---

## Open Questions

None — the gap is fully understood. Implementation approach is selected (Option A).

---

## References

- [`fulfillment.OrderImpl.fulfillOrder()`](../../../java/fulfillment/fulfillment-core/src/main/java/com/acme/fulfillment/workflows/OrderImpl.java) — line 228: `CalculateShippingOptionsRequest` construction
- [`apps.OrderImpl.execute()`](../../../java/apps/apps-core/src/main/java/com/acme/apps/workflows/OrderImpl.java) — line 123: `StartOrderFulfillmentRequest` construction (missing `selected_shipping`)
- [`enablements.OrderActivitiesImpl`](../../../java/enablements/enablements-core/src/main/java/com/acme/enablements/activities/OrderActivitiesImpl.java) — line 99: order submission (no shipping price)
- [`LlmActivities.build_system_prompt()`](../../../python/fulfillment/src/agents/activities/llm.py) — line 102: `customer_paid_price.units > 0` guard
- [ShippingAgent spec](../../fulfillment-order/shipping-agent/spec.md) — Phase 6: alternate warehouse enforcement
- [Load-generation spec](../load-generation/spec.md) — the existing load-gen sub-spec this phase augments
