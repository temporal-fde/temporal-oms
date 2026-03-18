# Worker Version Enablement Initiative - Progress Tracking

**Initiative:** Demonstrate safe worker version transitions using Temporal's build-id routing
**Status:** 📋 Spec Phase - Sub-specs ready for tech lead review
**Owner:** [Your Name]
**Created:** 2026-03-18

---

## Initiative Overview

This initiative has 3 sub-specs that work together:

1. **Load Generation Service** - Continuous order submission + state tracking
2. **Version Deployment Setup** - Multi-version workers with build-id routing
3. **Validation Framework** - Verify zero failures during transitions

See [INDEX.md](./INDEX.md) for architecture overview and dependency diagram.

---

## Current Status Summary

| Sub-Spec | Status | Owner | Review Date | Approval |
|----------|--------|-------|-------------|----------|
| [Load Generation](./load-generation/) | 📋 Draft | [Your Name] | TBD | ⏳ Pending |
| [Version Deployment](./version-deployment/) | 📋 Draft | [Your Name] | TBD | ⏳ Pending |
| [Validation Framework](./validation-framework/) | 📋 Draft | [Your Name] | TBD | ⏳ Pending |

**Overall Status:** ⏳ **Awaiting Tech Lead Review of All Specs**

---

## Submission Checklist ✅

All three specs complete and ready for review:

### Load Generation Service
- [x] Spec written
- [x] Goals & acceptance criteria clear
- [x] Architecture documented
- [x] Implementation strategy defined
- [x] Testing approach specified
- [x] PROGRESS.md prepared for review

### Version Deployment Setup
- [x] Spec written
- [x] Goals & acceptance criteria clear
- [x] Architecture documented
- [x] Implementation strategy defined
- [x] Testing approach specified
- [x] PROGRESS.md prepared for review

### Validation Framework
- [x] Spec written
- [x] Goals & acceptance criteria clear
- [x] Architecture documented
- [x] Implementation strategy defined
- [x] Testing approach specified
- [x] PROGRESS.md prepared for review

---

## Review Process

### Phase 1: Tech Lead Review (Current)

**Timeline:** Week of 2026-03-18

For each sub-spec, tech lead should:
1. Read spec.md
2. Understand goals, architecture, implementation plan
3. Provide feedback in PROGRESS.md → "Review Feedback" section
4. Make approval decision (APPROVED / APPROVED WITH CHANGES / NEEDS REWORK)

**Open Questions** for tech lead review:

**Load Generation:**
- [ ] Load rate default: 1/sec or different?
- [ ] Metrics persistence: In-memory only?
- [ ] Failure handling: Max retries?

**Version Deployment:**
- [ ] V2 code: New features or just version test?
- [ ] Long-running workflows: Keep on v1 or allow v2?
- [ ] Runbook audience: Engineering or prod team?

**Validation Framework:**
- [ ] Separate module or part of load-generator?
- [ ] Report formats: JSON only or add HTML?
- [ ] Validation in CI/CD later?

### Phase 2: Planning (After Approval)

**Timeline:** Week of 2026-03-25

Once all specs approved:
1. Break each spec into detailed tasks
2. Estimate effort per phase
3. Identify execution sequence (load-gen → versions → validation)
4. Create Jira/Linear tickets
5. Assign owners + target dates

### Phase 3: Implementation (After Planning)

**Timeline:** Weeks of 2026-04-01 through 2026-04-14 (est. 2-3 weeks)

Phases 1-4 for each sub-spec, in sequence:
- Load Generation: 4 phases, ~11 days
- Version Deployment: 4 phases, ~7 days (can overlap with load-gen phase 3-4)
- Validation Framework: 4 phases, ~9 days (starts after versions deployed)

### Phase 4: Validation & Demo

**Timeline:** Week of 2026-04-21

1. Run load generator test
2. Deploy version 2 workers
3. Run validation framework
4. Demo to team + discuss learnings
5. Update PROGRESS.md: Initiative → COMPLETE

---

## Dependency Graph

```
Week 1: Review & Approval
├─ [Load Generation] ← review
├─ [Version Deployment] ← review
└─ [Validation Framework] ← review

Week 2: Planning
├─ [Load Generation] ← plan
├─ [Version Deployment] ← plan
└─ [Validation Framework] ← plan

Weeks 3-5: Implementation (Sequential)
├─ [Load Generation] Phase 1-4 ── done ✓
│                                    ↓
├─ [Version Deployment] Phase 1-4 ──  done ✓
│                                        ↓
└─ [Validation Framework] Phase 1-4 ── running

Week 6: Demo & Close
└─ Run demo + update documentation
```

---

## Open Items By Category

### Questions for Tech Lead (See Individual Specs)

- [ ] Load Generation: Rate, metrics, failure handling
- [ ] Version Deployment: V2 changes, long-running workflows, runbook audience
- [ ] Validation: Module location, report formats, CI/CD integration

### Assumptions to Validate

- [ ] Temporal cluster supports build-ids (verify version)
- [ ] Current workflows forward-compatible with v2
- [ ] 1.3 GB headroom in KinD cluster (after lean resource config)

### Tech Decisions (Already Made)

✅ Separate services (not monolithic)
✅ Prometheus metrics (not custom)
✅ Temporal SDK queries (not external DB)
✅ ConfigMap-driven configuration (not hardcoded)
✅ Conservative assertions (fail on ambiguity, not optimistic)

---

## Next Steps

### Immediate (This Week)

1. **Schedule tech lead review meeting** (30-60 min)
   - Walk through architecture diagrams
   - Discuss design decisions
   - Answer open questions
   - Get preliminary feedback

2. **Compile feedback** from tech lead into each spec's PROGRESS.md
   - Note: "Approved", "Approved with changes", or "Needs rework"
   - If changes requested, discuss timeline for revisions

3. **Revise specs** if needed (1-2 days turnaround)
   - Address tech lead feedback
   - Update PROGRESS.md with new approval decision

### Week 2: Planning (After Approval)

1. Break specs into implementation tasks
2. Estimate effort per phase
3. Create execution plan with dates
4. Assign owners (if team available)

### Week 3+: Implementation

Execute phases in sequence:
- Load gen (Weeks 3-4)
- Versions (Weeks 4-5)
- Validation (Weeks 5-6)

---

## Success Criteria (Overall Initiative)

By end of Week 4, we will have run an **enablement session** where:

### Pre-Session (Infrastructure)
- [x] Load Generator Service
  - Submits 10-20 orders continuously
  - Tracks workflow state
  - Can be started/stopped via REST
- [x] Version Deployment
  - V1 and V2 workers configured
  - Build-ids wired
  - Can deploy v2 during running load

### Session Deliverables
- [x] **Talk Track (10 min)**
  - Crisp explanation of the problem (why restart breaks things)
  - Clear solution (build-id routing)
  - Safe deployment pattern
  - How monitoring works

- [x] **Demo Scripts (3 scenarios, 5 min each)**
  1. Scenario: "New workflows use v2, old stay on v1"
     - Start load gen (v1 only)
     - Deploy v2 workers
     - Show new orders go to v2
     - Show old orders complete on v1

  2. Scenario: "All workflows complete successfully"
     - Wait for all orders to finish
     - Show zero failures
     - Explain throughput unaffected

  3. Scenario: "Rollback if issues detected"
     - Mark v2 incompatible
     - Show new workflows fall back to v1
     - Explain recovery process

- [x] **Runbook**
  - Pre-flight checklist
  - Step-by-step deployment
  - Monitoring thresholds
  - Rollback triggers

- [x] **Team Understanding**
  - Team can explain the pattern
  - Team knows when to use it
  - Team could execute it for real workflow changes

---

## Key Contacts & Owners

| Role | Name | Contact |
|------|------|---------|
| Initiative Owner | [Your Name] | [email/slack] |
| Tech Lead | [TBD] | [email/slack] |
| Temporal SME | [TBD] | [email/slack] |

---

## Decision Log

### Decision: Three Sub-Specs Instead of Monolithic (2026-03-18)
**Rationale:**
- Each sub-spec has clear, independent value
- Can be reviewed, implemented, and tracked separately
- Parallel work possible (load-gen and versions can be reviewed together)
- Clearer scope boundaries
- Better reusability (load-gen useful for other testing)

**Alternatives Considered:**
- Single monolithic spec (harder to review, too many open questions, harder to track progress)
- Waterfall sequential specs (would block review and planning)

**Status:** Accepted (used for this initiative)

---

## Revision History

| Date | Author | Change | Status |
|------|--------|--------|--------|
| 2026-03-18 | [Your Name] | Initial initiative framing + 3 sub-specs | Draft |
| | | Ready for tech lead review | |
