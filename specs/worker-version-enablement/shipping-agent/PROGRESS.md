# ShippingAgent Integration (Enablements Path) — Progress Tracking

**Feature:** ShippingAgent integration for the enablements load-generation path
**Status:** 📋 Spec Complete — Awaiting Implementation Session
**Owner:** Temporal FDE Team
**Created:** 2026-04-27
**Updated:** 2026-04-27

---

## Phase Status

| Phase | Description | Status | Blocking On |
|-------|-------------|--------|-------------|
| Phase 1 | Load-generation changes — thread `selected_shipment` from enablements through to ShippingAgent | ✅ Complete | — |

---

## Dependencies

- **ShippingAgent Phase 6** (prompt hardening + post-loop `find_alternate_warehouse` enforcement) — ✅ Complete
- **Session pre-flight**: integrations Nexus endpoint registered in local k8s cluster; EasyPost test key active

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-04-27 | Mike Nichols | Initial spec written. Traced full enablements → apps → fulfillment → ShippingAgent call chain. Identified that `customer_paid_price` and `transit_days_sla` are never populated, silently disabling both margin and SLA rules in ShippingAgent. `find_alternate_warehouse` structurally unreachable from enablements path. Recommended fix: hardcode `selected_shipping.price = Money{units=1}` in `apps.OrderImpl` (Option A). Implementation deferred to separate Claude session. |
| 2026-04-27 | Claude | Implemented Phase 1 (Option B — thread through, not hardcode). Added `SelectedShipment` to REST API proto (`apps/api/v1/message.proto`). Added `delivery_days` to `SelectedShippingOption` (fulfillment domain proto). Renamed `transit_days_sla` → `delivery_days_sla` on `CalculateShippingOptionsRequest`; removed `transit_days_sla` from `acme.common.v1.Shipment` (was redundant — SLA derives from `EasyPostRate.delivery_days`). Wired: enablements sets `paid_price_cents=1` → controller maps to `Shipment.paid_price` → `apps.OrderImpl` maps to `SelectedShippingOption.price` → `fulfillment.OrderImpl` passes as `customer_paid_price` → ShippingAgent MARGIN_SPIKE triggers deterministically. `delivery_days_sla` path also wired end-to-end; enablements does not set it (SLA_BREACH not required for workshop demo). |
