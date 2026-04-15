# fulfillment.Order Workflow — Progress Tracking

**Feature:** `fulfillment.Order` — Durable Fulfillment Orchestration
**Status:** 📋 Draft — Awaiting Tech Lead Review
**Owner:** Engineering Team
**Created:** 2026-04-15

---

## Current Status

| Phase | Description | Status | Owner | Target |
|-------|-------------|--------|-------|--------|
| Spec | Write and review specification | 📋 Draft | Temporal FDE Team | 2026-04-15 |
| Phase 1 | Proto Schema & Core Types | ⏳ Not started | TBD | TBD |
| Phase 2 | Workflow & Activity Interfaces | ⏳ Not started | TBD | TBD |
| Phase 3 | `fulfillment.Order` Implementation (V1) | ⏳ Not started | TBD | TBD |
| Phase 4 | Nexus Handler for `validateOrder` | ⏳ Not started | TBD | TBD |
| Phase 5 | Worker Versioning — `apps.Order` + `processing.Order` | ⏳ Not started | TBD | TBD |
| Phase 6 | Activity Implementations | ⏳ Not started | TBD | TBD |
| Phase 7 | V2 Shipping Path (ShippingAgent) | ⏳ Deferred | TBD | TBD |

---

## Spec Review Checklist

### Author Self-Check (Pre-Review)

- [x] Executive summary is clear (non-technical person can understand the "why")
- [x] Goals are measurable and specific
- [x] Acceptance criteria are testable
- [x] Design decisions explain the "why" not just the "what"
- [x] Alternatives considered are documented
- [x] Implementation phases are realistic
- [x] Testing strategy covers happy path + edge cases (cancel, timeout, margin exceeded)
- [x] Risks are identified with mitigations
- [x] Open questions are explicit (ShippingAgent design, fallback notification, etc.)
- [x] Proto schema for all new messages is drafted

### Open Questions for Tech Lead

- [ ] **ShippingAgent (V2):** Nexus operation or Child Workflow? Decision needed before Phase 6 begins.
- [ ] **Fallback shipping notification:** Should the customer be notified silently when a fallback shipping option is used?
- [ ] **`margin_leak` type:** `Double` (minor currency units) vs. a separate `Money` SearchAttribute codec?
- [ ] **Inventory service contract:** Internal service or external API? Affects activity timeout/retry configuration.
- [ ] **`fulfillOrder` as the "processOrder complete" signal:** Confirm `fulfillOrder` Update from `processing.Order` is the trigger — not a separate processOrder signal.
- [ ] **Address validation service:** EasyPost (referenced in shipping_agent.proto) or a separate activity?
- [ ] **V1/V2 demo:** Include in the fulfillment.Order demo session or a separate versioning enablement session?

---

## Review Feedback

### Tech Lead Review

_Awaiting review. Fill in after review meeting._

**Reviewer:**
**Review Date:**
**Decision:** ⏳ Pending (`APPROVED` / `APPROVED WITH CHANGES` / `NEEDS REWORK`)

**Feedback:**

---

## Decision Log

### Decision: Kafka → Temporal workflow replacement (2026-04-15)

**Rationale:** The existing `FulfillmentsImpl` + embedded Kafka + `KafkaConsumer` approach provides no durability, compensation, cancellation, or delivery tracking. Moving to a Temporal workflow gives us all of these for free while reducing operational complexity (no Kafka broker in the production path).

**Alternatives Considered:** Keep Kafka, add a Kafka consumer workflow in `fulfillment-workers` — doubles the infrastructure surface area with no additional value since the consumer is just a passthrough today.

**Status:** Accepted

---

### Decision: Detached scope for inventory compensation (2026-04-15)

**Rationale:** If the main workflow scope is cancelled (via `cancelOrder` Signal or timeout), a catch-block compensation would also be cancelled before it could execute. A detached scope runs to completion regardless of the parent scope's cancellation state.

**Status:** Accepted — matches the pattern available in `processing.OrderImpl`

---

## Next Steps

1. **Schedule tech lead review** — walk through architecture diagram in spec, resolve open questions
2. **Resolve ShippingAgent decision** (Nexus vs. Child WF) — unblocks Phase 6 scoping
3. **Assign phase owners** — decide who implements Phase 1 through Phase 5
4. **Phase 1 kickoff** — extend `proto/acme/fulfillment/domain/v1/workflows.proto` with new Java messages

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-04-15 | Engineering Team | Initial spec + PROGRESS.md created |
