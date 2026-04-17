# ShippingAgent — Progress Tracking

**Feature:** `ShippingAgent` — AI-Powered Shipping Rate Selection
**Status:** 📋 Draft — Ready for Review
**Owner:** Temporal FDE Team
**Created:** 2026-04-15
**Updated:** 2026-04-15

---

## Phase Status

| Phase | Description | Status | Blocking On |
|-------|-------------|--------|-------------|
| Phase 1 | Proto Schema | ⏳ Not started | — |
| Phase 2 | Activity Implementations | ⏳ Not started | Phase 1 |
| Phase 3 | ShippingAgent Workflow + Agentic Loop | ⏳ Not started | Phase 2 |
| Phase 4 | Nexus Handler + `fulfillment.Order` V2 Wiring | ⏳ Not started | Phase 3 + `fulfillment.Order` Phase 3–4 complete |
| Phase 5 | Workshop Scenarios + Demo Scripts | ⏳ Not started | Phase 4 |

---

## Open Questions

| Question | Needed By | Status |
|----------|-----------|--------|
| PredictHQ `within_km` default for Workshop demos | Phase 2 | ✅ Resolved: 50km |
| Default `cache_ttl_secs` | Phase 3 | ✅ Resolved: 1800 (30 minutes) |
| `SLA_BREACH` — signal support from ShippingAgent or return to `fulfillment.Order`? | Phase 3 | ✅ Resolved: return to `fulfillment.Order`; agent recommends, caller decides |

---

## Dependencies

- **Inventory Locations spec** — must exist before `lookup_inventory_location` has real data to query. V1 workaround: static config seed.
- **`fulfillment.Order` Phases 3–4 complete** — required before Phase 4 (Nexus wiring into `fulfillment.Order` V2)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-04-15 | Temporal FDE Team | Initial stub |
| 2026-04-15 | Temporal FDE Team | Full spec written; all design questions resolved |
