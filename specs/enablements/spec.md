# Enablements Specification

**Feature Name:** Enablements with Load Generation & Validation
**Status:** Draft - Ready for Tech Lead Review
**Owner:** [Your Name]
**Created:** 2026-03-18
**Updated:** 2026-03-18

---

## Overview

### Executive Summary

This feature enables safe deployment of new worker versions in Temporal while maintaining continuous order processing. We need a comprehensive system that:

1. **Generates realistic load** - Creates and maintains Order workflows in various completion stages (new, in-process, completed)
2. **Deploys new worker versions** - Shifts traffic from old to new workers using Temporal's worker versioning and build IDs
3. **Validates versioning behavior** - Ensures workflow compatibility, no data loss, and graceful transitions

The goal is to demonstrate that Temporal's worker versioning prevents workflow failures during worker updates, validating the patterns we'll use in production.

---

## Goals & Success Criteria

### Primary Goals
- Goal 1: Load generator maintains 10+ concurrent orders in different workflow stages
- Goal 2: Deploy new worker version (e.g., v2) while v1 is actively processing orders
- Goal 3: Validate zero workflow failures during version transition
- Goal 4: Verify workers with different versions can coexist peacefully
- Goal 5: Document worker versioning patterns for team reference

### Acceptance Criteria
- [ ] Load generator creates orders continuously and tracks workflow state
- [ ] New worker version can be deployed and marked as default via `temporal workflow start --build-id`
- [ ] Old worker version continues processing existing workflows (no forced migration)
- [ ] New workflows use new worker version, old workflows stay on old version
- [ ] All in-flight workflows complete successfully regardless of version
- [ ] Metrics show successful transitions with zero failures
- [ ] Runbook documents the version transition process

---

## Current State (As-Is)

### What exists today?
- **Processing workers** deployed with static version (e.g., `local-dev`)
- **Order workflows** (Order, Payment, SupportTeam) that span multiple workers
- **Temporal CLI** for manual workflow inspection
- **Scenario scripts** that create individual orders for demo purposes
- **No continuous load** - orders are created manually and processed once

### Pain points / gaps
- Can only test one worker version at a time
- No way to verify "upgrade in flight" scenarios
- Manual workflow state tracking across multiple orders
- Unclear if our workflow definitions are forward/backward compatible
- No metrics/dashboards for version transition health
- Version transition requires manual steps with temporal CLI

---

## Desired State (To-Be)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Load Generation System                     │
├─────────────────────────────────────────────────────────────┤
│  • Load Generator Service (Java/REST)                        │
│  • Tracks order state (created, processing, completed)      │
│  • Submits orders continuously to apps-api                  │
│  • Queries workflow status via Temporal SDK                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   Temporal Cluster                           │
├─────────────────────────────────────────────────────────────┤
│  • Processing Namespace (fde-oms-processing.*)              │
│  • Worker V1 @ build-id: "processing-worker:v1"            │
│  • Worker V2 @ build-id: "processing-worker:v2" (canary)   │
│  • Task routing based on build-id compatibility             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              Validation & Observability                      │
├─────────────────────────────────────────────────────────────┤
│  • Workflow query checks (state transitions, data integrity)│
│  • Metrics collection (completion rate, version dist.)      │
│  • Test assertions (no failures, no data loss)              │
│  • Runbook documents manual steps for prod                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Capabilities
- **Continuous Order Load:** Create orders at configurable rate (e.g., 1/sec), maintain backlog
- **Multi-Version Workers:** Deploy V2 alongside V1, route based on build-id
- **Workflow State Tracking:** Query workflows to track completion stages
- **Automatic Validation:** Detect failures, data loss, state inconsistencies
- **Metrics & Dashboards:** Show order completion rates, version distribution, transition health
- **Runbook Documentation:** Step-by-step guide for version transitions

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Dedicated load-gen service vs CLI scripts | Service is observable, scalable, repeatable; CLI is fragile in long-running tests | Script-based load (bash/Python) - less reliable, harder to monitor |
| Track workflows via Temporal SDK queries | Direct query gives exact state, works in Kubernetes, no extra infrastructure | External DB tracking - adds complexity, eventual consistency |
| Worker versioning via build-id (not semantic versions) | Temporal's task routing uses build-id; explicit control; supports rollback | Custom version logic - reinvents Temporal wheel |
| Load generator is separate service (not worker) | Workflows are the system under test; generator is test infrastructure | Generate from within worker - couples test logic to prod logic |
| Validate via workflow state queries + metrics | Captures both correctness and performance; observable in prod | Only assertions (fail loudly) - miss silent data loss scenarios |

### Component Design

#### Load Generator Service
- **Purpose:** Generate and track orders in different completion stages
- **Responsibilities:**
  - Submit orders via apps-api REST endpoint
  - Query workflow state via Temporal SDK
  - Track: created, in-processing, completed, failed counts
  - Expose metrics endpoint for scraping
- **Interfaces:**
  - Consumes: apps-api (`POST /api/v1/commerce-app/orders/{orderId}`)
  - Consumes: Temporal SDK (workflow state queries)
  - Exposes: REST API (`GET /metrics`, `POST /load/start`, `POST /load/stop`)

#### Worker V1 vs V2 Comparison
- **V1 (baseline):** Current processing-workers implementation (build-id: `processing-worker:v1`)
- **V2 (new):** Same or modified implementation (build-id: `processing-worker:v2`)
- **Difference:** Can be schema change, logic improvement, or just version bump (for testing)

#### Validation Framework
- **Purpose:** Ensure workflows don't fail during version transition
- **Responsibilities:**
  - Query sample of workflows during/after transition
  - Check state consistency (no orphaned workflows)
  - Verify no data loss in state mutations
  - Track metrics (throughput before/after)
- **Interfaces:**
  - Consumes: Temporal SDK (workflow history, state queries)
  - Exposes: Test report (pass/fail, metrics summary)

### Workflow State Model

Orders progress through these stages:
```
Created
  ↓
SubmitOrder update → Processing
  ↓
Payment capture → Payment Completed
  ↓
Enrichment → Enriched
  ↓
Fulfillment → Fulfilled
  ↓
Completed
```

Version compatibility: A workflow started with V1 should be completable by V2 (forward compatibility).

### Configuration / Deployment

**Load Generator Service:**
```yaml
# k8s/base/load-generator/deployment.yaml
- Service: load-generator
- Namespace: temporal-oms-tools
- Port: 8082
- Metrics: /metrics (Prometheus format)
- Env:
  - APPS_API_ENDPOINT: http://apps-api/api/v1
  - LOAD_RATE: 1 (orders/sec)
  - CONCURRENT_ORDERS: 50
```

**Worker Versions:**
```yaml
# Deployment: processing-workers (existing)
- build-id: processing-worker:v1 (existing)
- Env: BUILD_ID=processing-worker:v1, USE_WORKER_VERSIONING=true

# New deployment or replica: processing-workers-v2
- build-id: processing-worker:v2 (canary)
- Env: BUILD_ID=processing-worker:v2, USE_WORKER_VERSIONING=true
```

**Temporal SDK configuration (worker side):**
```java
WorkerOptions.newBuilder()
  .setBuildId("processing-worker:v1")
  .useWorkerVersioning(true)  // Enable version tracking
  .setVersioningIntent(VersioningIntent.COMPATIBLE)
  .build()
```

---

## Implementation Strategy

### Phase 1: Load Generator Service
**Goal:** Create service that generates orders and tracks state

Deliverables:
- [ ] New module: `java/load-generator/`
- [ ] LoadGeneratorService (REST API)
  - `POST /load/start` - Begin order generation
  - `POST /load/stop` - Stop and summarize
  - `GET /metrics` - Return order state metrics
- [ ] OrderGenerator (handles submission + tracking)
- [ ] Temporal queries for workflow state
- [ ] Kubernetes deployment + Ingress
- [ ] Docker image build integration

### Phase 2: Worker Versioning Setup
**Goal:** Deploy two worker versions side-by-side

Deliverables:
- [ ] Update processing-workers to set BUILD_ID env var
- [ ] Create processing-workers-v2 deployment (or use replica sets)
- [ ] Enable `useWorkerVersioning()` in worker registration
- [ ] Update Temporal config to support versioning
- [ ] Document version deployment SOP

### Phase 3: Validation Framework
**Goal:** Verify versions coexist peacefully

Deliverables:
- [ ] WorkflowValidator service (queries + asserts)
- [ ] Checks for workflow failures, data loss, state corruption
- [ ] Metrics collection (completion rates by version)
- [ ] Test script: `scripts/validate-worker-versions.sh`
- [ ] Run-through documentation for team

### Phase 4: Demo & Runbook
**Goal:** Document reproducible demo, transition SOP

Deliverables:
- [ ] Script: `scripts/demo-worker-versions.sh`
- [ ] Runbook: `docs/worker-versioning-runbook.md`
- [ ] Metrics dashboard (Grafana or CLI summary)
- [ ] Post-mortem template for issues

### Critical Files / Modules

**To Create:**
- `java/load-generator/pom.xml` - Maven module
- `java/load-generator/src/main/java/com/acme/loadgen/LoadGeneratorApplication.java` - Spring Boot entry
- `java/load-generator/src/main/java/com/acme/loadgen/services/OrderGeneratorService.java` - Load generation logic
- `java/load-generator/src/main/java/com/acme/loadgen/controllers/LoadController.java` - REST API
- `java/load-generator/src/main/resources/application.yaml` - Configuration
- `k8s/base/load-generator/deployment.yaml` - Kubernetes deployment
- `k8s/ingress/load-generator-ingress.yaml` - Ingress route
- `java/processing/processing-workers/src/main/java/.../WorkerVersioningSetup.java` - Version registration
- `scripts/validate-worker-versions.sh` - Validation runner
- `docs/worker-versioning-runbook.md` - SOP documentation

**To Modify:**
- `java/pom.xml` - Add load-generator module
- `java/processing/processing-workers/src/main/resources/application.yaml` - Add BUILD_ID env var
- `k8s/base/kustomization.yaml` - Add load-generator deployment
- `scripts/app-deploy.sh` - Build load-generator Docker image
- `scripts/demo-up.sh` - Deploy load-generator on startup

---

## Testing Strategy

### Unit Tests
- OrderGenerator creates valid order payloads
- Metrics accumulator correctly counts workflow states
- Configuration parsing works (BUILD_ID, LOAD_RATE, etc.)

### Integration Tests
- Load generator can submit orders via apps-api
- Temporal queries return expected workflow states
- Metrics endpoint returns valid Prometheus format

### Load / Validation Tests

**Test Scenario: Version Transition**
1. Start load generator: create 50 orders over 5 minutes (10 orders/min)
2. Let v1 workers process for 2 minutes (initial throughput baseline)
3. Deploy v2 workers, mark as compatible version
4. Continue load for 3 more minutes (new orders → v2, old orders → v1)
5. Validate:
   - [ ] Zero workflow failures before, during, after transition
   - [ ] All workflows complete within SLA (< 5 min from creation)
   - [ ] Version distribution matches deployment (30% v1, 70% v2 after transition)
   - [ ] Throughput doesn't drop (within 10% variance)
   - [ ] No state corruption or data loss

### Validation Checklist
- [ ] Load generator builds and deploys successfully
- [ ] Metrics endpoint returns valid data
- [ ] Workflows submit successfully with sustained load
- [ ] Version transition completes without workflow failures
- [ ] All in-flight workflows complete successfully
- [ ] Metrics show expected version distribution
- [ ] Documentation complete and team trained

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Load generator creates too much load, overwhelms Temporal | High | Medium | Start with low load rate (1/sec), monitor queue depth, scale incrementally |
| Workflows fail during version transition due to schema incompatibility | High | Medium | Test schema changes offline first, ensure forward compatibility, have rollback plan |
| Metrics inaccuracy masks real failures | Medium | Low | Query workflows directly (source of truth), compare metrics to actual state |
| Version transition takes too long, SLA violated | Medium | Medium | Set timeout for transition, have manual rollback procedure, document SOP |
| Workers crash during version deployment | High | Low | Use canary deployment (v2 as small replica first), monitor error logs |
| Load generator itself fails, test becomes inconclusive | Medium | High | Add health checks, monitoring, auto-restart; keep load gen separate from system under test |

---

## Dependencies

### External Dependencies
- Temporal 1.33+ (with build-id support)
- Java 21+
- Spring Boot 3.5+
- Prometheus (for metrics scraping)

### Cross-Cutting Concerns
- Load generator must use same Temporal SDK version as workers (for compatibility testing)
- apps-api must be running for order submission
- Temporal cloud/cluster must be accessible from load-gen service
- Build-id versioning requires explicit Temporal cluster support

### Rollout Blockers
- [ ] Processing workers must support BUILD_ID configuration
- [ ] Temporal cluster must support `useWorkerVersioning()`
- [ ] apps-api must be deployed and accessible

---

## Open Questions & Notes

### Questions for Tech Lead / Product

- [ ] What should V2 worker changes be? (logic change vs schema change vs just version bump?)
- [ ] How long should load test run? (5 min / 30 min / 1 hour?)
- [ ] Should we test multiple version transitions (v1→v2→v3) or just one?
- [ ] What metrics are most important for sign-off? (throughput, latency, failure count?)
- [ ] Who owns runbook updates after first demo?
- [ ] Should load generator be in prod or just for testing?

### Implementation Notes

- **Build-ID format:** Use semantic versioning in build-id name for clarity (e.g., `processing-worker:1.0.0`)
- **State queries:** Use workflow `GetState()` queries, not history (faster, less data)
- **Metrics baseline:** Run with v1 only for 2 min to establish throughput baseline before transition
- **Failure detection:** Watch for:
  - Workflows stuck in state (query returns same state after 1 min)
  - Workflow history showing exceptions
  - Task queue depth growing (backlog)
  - Worker errors in logs
- **Rollback:** If v2 shows failures, update Temporal compatibility to mark v2 incompatible, redeploy v1, monitor error rate

---

## References & Links

- [Temporal Worker Versioning Docs](https://temporal.io/blog/worker-versioning)
- [Build ID Configuration](https://docs.temporal.io/dev-guide/worker-performance#worker-versioning)
- [Current Workflow Definitions](../java/processing/processing-core/src/main/java/com/acme/processing/workflows/)
- [Deployment Runbook Template](../docs/)
