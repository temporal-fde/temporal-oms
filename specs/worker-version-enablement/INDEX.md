# Worker Version Enablement Initiative

**Status:** Draft - Sub-specs Ready for Tech Lead Review
**Owner:** [Your Name]
**Initiative Start:** 2026-03-18
**Type:** Enablement Session (teach the team safe versioning patterns)

---

## Overview

Run an **enablement session** to teach the team how to safely deploy workflow code changes using Temporal worker versioning. Through live demos and concrete scenarios, the team will learn:

1. **The Problem:** How workflow code changes can break in-flight workflows (and why you can't just restart workers)
2. **The Solution:** Worker versioning via build-ids (new workflows → v2, old workflows stay on v1)
3. **The Practice:** Step-by-step deployment process + monitoring + rollback

**Deliverables:**
- Crisp talk track (15-20 min explanation)
- Live demo scripts (5-10 min per scenario)
- 3 concrete scenarios showing different cases
- Runbook the team can use for production

**Success:** Team watches demo, understands the pattern, can explain it to others.

---

## Goals

- Teach team the **problem** (why restarting workers breaks workflows)
- Teach team the **solution** (worker versioning with build-ids)
- Demonstrate **safe deployment pattern** (v1 → v2 transition with live load)
- Show **monitoring & rollback** (how to detect issues, recover)
- Enable team to apply this pattern in production

---

## Sub-Specifications

### 1. Load Generation Service
**Spec:** [load-generation/spec.md](./load-generation/spec.md)
**Status:** 📋 Draft
**Owner:** TBD
**Purpose:** Create orders continuously, track state across completion stages, expose metrics

**Key Deliverables:**
- REST API for load control (`/load/start`, `/load/stop`)
- Workflow state tracking (via Temporal SDK queries)
- Metrics endpoint for monitoring
- Kubernetes deployment + Ingress

**Why it matters:** Provides realistic, observable load for testing version transitions

---

### 2. Version Deployment Setup
**Spec:** [version-deployment/spec.md](./version-deployment/spec.md)
**Status:** 📋 Draft
**Owner:** TBD
**Purpose:** Configure workers with build-id versioning, deploy V1 + V2 side-by-side

**Key Deliverables:**
- Worker build-id configuration (V1, V2)
- Temporal SDK worker versioning setup
- Multi-version deployment topology
- Canary deployment strategy
- Runbook for version transitions

**Why it matters:** Foundation for safe version upgrades; enables gradual rollout

---

### 3. Validation Framework
**Spec:** [validation-framework/spec.md](./validation-framework/spec.md)
**Status:** 📋 Draft
**Owner:** TBD
**Purpose:** Verify workflows don't fail during version transitions, detect data loss

**Key Deliverables:**
- Workflow state validator (queries + assertions)
- Failure detection logic
- Metrics collection (throughput, version distribution)
- Test scenarios & scripts
- Health report generation

**Why it matters:** Objective proof that versioning works; catch issues before production

---

## Implementation Dependencies

```
┌─────────────────────────────────────────┐
│  Load Generation Service (Phase 1)      │ ← Can start independently
│  (Creates load for testing)             │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Version Deployment Setup (Phase 2)     │ ← Builds on load gen
│  (V1 + V2 workers, build-ids)          │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Validation Framework (Phase 3)         │ ← Tests the transition
│  (Verify zero failures)                 │
└─────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Demo & Runbook (Phase 4)               │ ← Captures learnings
│  (Document repeatable process)          │
└─────────────────────────────────────────┘
```

**Note:** Load Gen and Version Deployment can be reviewed in parallel, but Version Deployment depends on Load Gen being available for testing.

---

## Enablement Session Outline

```
Session: "Worker Versioning in Temporal" (30-45 min)

Part 1: Talk Track (10 min)
├─ Problem: "Why can't we just restart workers with new code?"
├─ Solution: "Worker versioning via build-id routing"
├─ Pattern: "v1 → v2 transition without downtime"
└─ Monitoring: "How we know it's working"

Part 2: Live Demo (15-20 min)
├─ Scenario 1: "New workflows route to v2, old stay on v1"
├─ Scenario 2: "All workflows complete successfully"
└─ Scenario 3: "Rollback if v2 has issues"

Part 3: Runbook (5 min)
├─ Pre-flight checks
├─ Deployment steps
├─ Monitoring during transition
└─ Rollback procedure

Timeline:
├─ Week 1: Build demo infrastructure (load gen + versions)
├─ Week 2: Write talk track & scenario scripts
├─ Week 3: Dry run + refine
└─ Week 4: Team enablement session
```

---

## Open Questions (For All Sub-Specs)

- [ ] Should V2 workers have code changes (logic, schema) or just version bump?
- [ ] Load test duration: 5 min, 30 min, or 1 hour?
- [ ] Success metrics: throughput maintained? latency <5s? zero failures?
- [ ] After demo, should load-gen be production feature or test-only?
- [ ] Document Temporal build-id patterns for entire team?

---

## Tracking Progress

**Overall Initiative Status:**
- [ ] Spec Review (all 3 sub-specs approved)
- [ ] Planning (break into tasks, estimate)
- [ ] Phase 1: Load Generation (implement + test)
- [ ] Phase 2: Version Deployment (implement + test)
- [ ] Phase 3: Validation Framework (implement + test)
- [ ] Phase 4: Demo & Documentation (validate + ship)
- [ ] Complete (all acceptance criteria met)

**See:** [PROGRESS.md](./PROGRESS.md) for detailed status tracking

---

## Key Assumptions

- Temporal cluster supports worker versioning (build-id routing)
- Current workflow definitions are forward-compatible
- 1.3 GB headroom in KinD cluster (after lean resource config)
- apps-api stable for order submissions during testing

---

## References

- [Temporal Worker Versioning Docs](https://temporal.io/blog/worker-versioning)
- [Load Generation Spec](./load-generation/spec.md)
- [Version Deployment Spec](./version-deployment/spec.md)
- [Validation Framework Spec](./validation-framework/spec.md)
- [Initiative PROGRESS.md](./PROGRESS.md)
