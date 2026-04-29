# ShippingAgent Integration (Enablements Path) - Progress Tracking

**Feature:** ShippingAgent integration for the enablements/scenario path
**Status:** ✅ Implemented for current workshop scenarios
**Owner:** Temporal FDE Team
**Created:** 2026-04-27
**Updated:** 2026-04-29

---

## Phase Status

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| Phase 1 | Thread selected shipment context through to ShippingAgent | ✅ Complete | `selected_shipment` carries paid price and selected delivery days |
| Phase 2 | Fixture-backed shipping and location activities | ✅ Complete | Activities call `enablements-api`; no runtime EasyPost key required |
| Phase 3 | Scenario scripts | ✅ Complete | Dynamic runner, unique order IDs, unique customer IDs, margin-spike, and SLA-breach scenarios exist |
| Phase 4 | Nexus integration backend reroute | ⏳ Follow-up | Existing Nexus handlers still use `apps.Integrations` for commerce-app, PIMS, and inventory |

---

## Dependencies

- **ShippingAgent alternate warehouse enforcement** - complete.
- **`enablements-api` runtime fixtures** - complete for shipping and first-pass location-events.
- **Nexus backend reroute** - follow-up; do not mark `apps.Integrations` deprecated until that decision is made.
- **Location-events enrichment** - follow-up; current first pass returns empty events and `RISK_LEVEL_NONE`.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-04-27 | Mike Nichols | Initial spec written. Traced full enablements -> apps -> fulfillment -> ShippingAgent call chain and identified missing selected-shipment context. |
| 2026-04-27 | Claude | Implemented selected-shipment threading for paid price and selected delivery days. |
| 2026-04-29 | Codex | Updated progress to current state: scripts now generate unique order/customer IDs, margin/SLA scenarios are explicit, runtime shipping uses `enablements-api`, and Nexus backend reroute remains a follow-up. |
