# Workshop: Augment with AI - Progress

**Status:** Draft
**Last Updated:** 2026-05-01

---

## Spec Review Status

- [ ] Tech lead review complete
- [ ] Exercise list confirmed (Exercise 01 and 02 now specified; Exercise 03 still open)
- [ ] Open questions resolved

---

## Open Items (blocking)

- [ ] Confirm full exercise list - spec currently has migration -> observe AI -> extend AI
- [x] Confirm Codespaces machine type in `devcontainer.json`
- [ ] Confirm whether Anthropic/OpenAI API keys are pre-configured
- [ ] Verify `temporal worker deployment set-ramping-version` is available in pinned CLI version
- [ ] Confirm Kafka admin port 8071 is available in full-stack local run
- [ ] Decide whether Exercise 02 uses live Anthropic calls by default or a deterministic recorded fallback
- [ ] Decide whether to add the read-only `ShippingAgent.get_options` Query before Exercise 02 implementation

---

## Phase Status

| Phase | Status | Blocker |
|-------|--------|---------|
| Phase 1 - Devcontainer | Complete | Completed April 30, 2026 |
| Phase 1b - Workshop startup runner | Not Started | Confirm local service startup command shape |
| Phase 2 - Exercise 01 | Implemented lab material; validation pending | Workshop startup runner or manual startup |
| Phase 3 - Exercise 02 | Guide and helper scripts implemented; fallback decision open | Live LLM/fallback decision |
| Phase 4 - Exercise 03 | Not Started | Exercise scope confirmed |

---

## Notes

- The safe fulfillment handoff foundation exercise has a planning spec at
  `specs/workshop/exercises/01-safe-fulfillment-handoff/spec.md`.
  Hands-on lab material exists under `workshop/exercises/01-safe-fulfillment-handoff/`.
- Exercise 02 now has a planning spec at
  `specs/workshop/exercises/02-observe-shipping-agent/spec.md`.
- Exercise 03 is intentionally TBD until tech lead confirms the extension scope.
- The Codespaces/devcontainer foundation is complete. Remaining setup work is the workshop startup,
  status, and stop runner layer.
