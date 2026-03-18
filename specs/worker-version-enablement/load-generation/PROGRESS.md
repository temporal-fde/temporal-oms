# Worker Version Enablement Workflow - Progress Tracking

**Spec:** [spec.md](./spec.md)
**Status:** 📋 Draft - Ready for Tech Lead Review (API paths clarified)
**Owner:** [Your Name]
**Initiative:** [Worker Version Enablement](../INDEX.md)
**Subdirectory:** `load-generation/` (historical name; contains core workflow + core module)

---

## Current Status

| Component | Status | Owner |
|-----------|--------|-------|
| Spec document | ✅ Complete | [Your Name] |
| API path clarification | ✅ Complete (endpoints → apps-api controller) | [Your Name] |
| Tech lead review | ⏳ Awaiting | [Tech Lead] |
| Implementation planning | ⏳ Blocked (pending approval) | TBD |
| Phase 1: Proto + Workflow | ⏳ Not started | TBD |
| Phase 2: EnablementsWorkers | ⏳ Not started | TBD |
| Phase 3: EnablementsController | ⏳ Not started | TBD |
| Phase 4: V2 + Demo scripts | ⏳ Not started | TBD |

---

## Spec Completion Checklist ✅

- [x] Executive summary written
- [x] Goals & acceptance criteria defined
- [x] Current state analysis
- [x] Desired state architecture
- [x] Technical design (components, configuration, data model)
- [x] Implementation phases (4 phases with deliverables)
- [x] Testing strategy (unit, integration, load test)
- [x] Risk assessment
- [x] Open questions documented

---

## Open Items Before Approval

### Questions Requiring Tech Lead Input

- [ ] Order submission rate: 12 orders/min suitable for demo? Adjust for pacing?
- [ ] Order count: 20 orders good? Scale for longer demo visibility?
- [ ] Demo duration: ~5 minutes from v1-only to completion?
- [ ] DemoPhase transition timing: Auto-transition TRANSITIONING_TO_V2 → RUNNING_BOTH after v2 deployment, or explicit signal?
- [ ] Activity error handling: Retry failed order submissions or skip and continue?

### Design Decisions to Validate

- [ ] Workflow-based demo (proposed: yes - self-referential teaching)
- [ ] Order version tracking via activity context (proposed: yes - Temporal tracks which worker executed)
- [ ] API endpoints in apps-api as separate controller (proposed: yes - isolated from commerce paths)

---

## Tech Lead Review

### Submission Checklist
- [x] Spec is self-contained (can understand without context)
- [x] Goals are measurable
- [x] Acceptance criteria are testable
- [x] Design decisions documented with rationale
- [x] Implementation is appropriately scoped
- [x] Risks identified and mitigated
- [x] No blocking dependencies on other specs

### Review Feedback
```
[Tech Lead: Add feedback here]
```

### Approval Decision
```
☐ APPROVED - Proceed to planning
☐ APPROVED WITH CHANGES - See feedback above, proceed after revisions
☐ NEEDS REWORK - Return to author for major revisions

Approved By: ________________    Date: ________________
```

---

## Next Steps (After Approval)

1. **Planning Phase**
   - Break 4 implementation phases into detailed tasks
   - Create task list with estimates
   - Assign owner + target dates
   - Create Jira/Linear tickets

2. **Phase 1 Implementation** (Core Service)
   - Maven module scaffolding
   - Spring Boot application
   - Configuration files
   - Basic unit test

3. **Phase 2 Implementation** (Submission & Tracking)
   - OrderSubmitter service
   - WorkflowStateTracker service
   - Integration tests with Temporal

4. **Phase 3 Implementation** (Metrics & API)
   - MetricsCollector
   - LoadController REST endpoints
   - REST API tests

5. **Phase 4 Implementation** (Kubernetes & Docs)
   - Dockerfile
   - Kubernetes manifests
   - Integration into deploy script
   - Documentation

6. **Testing & Demo**
   - Load test scenario (300 orders over 5 min)
   - Validate metrics accuracy
   - Demo to team

---

## Timeline Estimate

(To be refined after planning)

| Phase | Estimate | Owner | Status |
|-------|----------|-------|--------|
| Approval & Planning | 1 day | [TBD] | ⏳ Blocked |
| Phase 1: Core Service | 2 days | [TBD] | ⏳ Blocked |
| Phase 2: Submission & Tracking | 3 days | [TBD] | ⏳ Blocked |
| Phase 3: Metrics & API | 2 days | [TBD] | ⏳ Blocked |
| Phase 4: K8s & Docs | 3 days | [TBD] | ⏳ Blocked |
| **Total** | **~11 days** | | |

---

## Dependencies

### Blocks This Sub-Spec
- ✅ None (can start independently)

### Blocked By
- ⏳ Tech lead approval

### External Dependencies
- ✅ Temporal cluster deployed
- ✅ apps-api service available
- ✅ KinD cluster running

---

## Notes for Tech Lead

**Why Workflow-Based Demo?**
Using a Temporal workflow to demonstrate Temporal versioning is the most powerful teaching approach. The workflow itself orchestrates orders, demonstrating:
- Continuous async operations (order submission)
- State management (tracking order progression)
- Interactive control (signals for team to trigger v2 deployment)
- Version routing (build-ids routing orders to v1/v2)

**Self-Referential Teaching:**
The demo *is* the thing being taught - a Temporal workflow that manages versioning. This clarity helps the team understand the concepts better.

**API Clarity:**
- **Workflow activities** call production APIs: apps-api `/api/v1/commerce/orders` and processing-api `/api/v1/enrichment`, `/api/v1/payments/capture`
- **Enablements API endpoints** (optional controller) are separate: `/api/v1/enablements/worker-version/...` in apps-api
- This separation keeps enablements testing isolated from production concerns

**Scope:**
This spec defines the core workflow + activities. Version deployment (v2 workers) and validation framework are separate sub-specs that build on this.

---

## Revision History

| Date | Author | Change | Status |
|------|--------|--------|--------|
| 2026-03-18 | [Your Name] | Initial spec draft (workflow-based approach) | Draft |
| 2026-03-18 | [Your Name] | Clarified API paths: workflow activities call production APIs, enablements endpoints in separate controller | Ready for Review |
