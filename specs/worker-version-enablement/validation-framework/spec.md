# Validation Framework Specification

**Feature Name:** Worker Versioning Validation & Testing Framework
**Status:** Draft - Ready for Tech Lead Review
**Owner:** [Your Name]
**Created:** 2026-03-18
**Updated:** 2026-03-18

**Part of:** [Worker Version Enablement Initiative](../INDEX.md)
**Depends on:** [Load Generation Service](../load-generation/spec.md), [Version Deployment](../version-deployment/spec.md)

---

## Overview

### Executive Summary

Build an automated validation framework that verifies worker versions can transition safely without workflow failures, data loss, or state corruption. The framework:

- Runs during version transitions (v1 → v2)
- Queries workflows for state integrity and completion
- Detects failures, stuck workflows, and data anomalies
- Collects metrics (completion rates, version distribution)
- Produces pass/fail report with evidence

This provides objective proof that Temporal's versioning mechanism works as expected and is safe for production use.

---

## Goals & Success Criteria

### Primary Goals
- Goal 1: Detect workflow failures during version transitions
- Goal 2: Verify state integrity (no data loss, no corruption)
- Goal 3: Confirm version routing (new → v2, old → v1)
- Goal 4: Measure transition health (throughput, completion rate)
- Goal 5: Generate reproducible test report for team

### Acceptance Criteria
- [ ] Validation framework can run against live workflows
- [ ] Detects failures (workflow state = FAILED)
- [ ] Detects stuck workflows (no state change > N minutes)
- [ ] Detects data loss (missing/corrupted state fields)
- [ ] Reports version distribution by workflow
- [ ] Tracks completion rate before/after transition
- [ ] Test scenario completes with pass/fail verdict
- [ ] Report includes metrics, logs, and recommendations

---

## Current State (As-Is)

### What exists today?
- **Scenario scripts** (invalid-order, cancel-order) test single workflows
- **Manual Temporal UI inspection** for workflow verification
- **No automated validation** of version transitions
- **No health metrics** for transitions (unknown if successful)
- **No failure detection** - rely on manual observation

### Pain points / gaps
- Can't quantify success of version transition
- Difficult to catch silent failures (workflows stuck, data loss)
- No metrics for dashboards or alerting
- Manual process doesn't scale (can't test multiple scenarios)
- Hard to compare "before/after" transition health

---

## Desired State (To-Be)

### Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│         Validation Framework                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ WorkflowValidator Service                          │  │
│  │ • Query Temporal SDK for workflow state            │  │
│  │ • Detect failures, stuck workflows, data issues   │  │
│  │ • Collect metrics (completion, version, rate)     │  │
│  └─────────────────────────────────────────────────────┘  │
│                      ↓                                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Assertions & Health Checks                         │  │
│  │ • Assert: zero failures                            │  │
│  │ • Assert: all workflows completed                  │  │
│  │ • Assert: no data corruption                       │  │
│  │ • Assert: version distribution matches expected    │  │
│  └─────────────────────────────────────────────────────┘  │
│                      ↓                                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Report Generation                                  │  │
│  │ • Metrics summary (throughput, completion)         │  │
│  │ • Failure details (if any)                         │  │
│  │ • Version distribution breakdown                   │  │
│  │ • Pass/fail verdict                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
         ↓
    Consumes: Temporal SDK (queries)
    Consumes: Load Generator metrics
    Produces: Test report (JSON/HTML)
```

### Key Capabilities
- **Workflow State Inspection:** Query workflows to get current state, history, failure reasons
- **Failure Detection:** Identify workflows with errors, exceptions, timeouts
- **Stuck Workflow Detection:** Find workflows that haven't progressed in N minutes
- **Data Integrity Checks:** Verify workflow state mutations are consistent
- **Metrics Aggregation:** Collect completion rates, throughput, version distribution
- **Report Generation:** Pass/fail verdict with evidence and recommendations

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Validation runs as separate script (not service) | Test infrastructure separate from production; easy to iterate and debug | Continuous validation service - adds complexity, harder to control test scenarios |
| Query Temporal SDK directly (no intermediate DB) | Source of truth; real-time; no sync issues | External state tracking - eventual consistency issues |
| Assertions not exceptions (collect all failures) | See complete picture before failing; better diagnostics | Fail-fast - miss secondary issues |
| Report format: JSON + human summary | Structured data for parsing, human-readable for team | Binary format or only text - less useful for analysis |

### Component Design

#### WorkflowValidator
- **Purpose:** Query Temporal for workflow state
- **Responsibilities:**
  - Query all workflows in task queue
  - Extract state (created, processing, completed, failed)
  - Get workflow history (check for errors/exceptions)
  - Identify version assignment (build-id)
  - Detect stuck workflows (no progress > N min)
- **Interfaces:**
  - Consumes: Temporal SDK (WorkflowClient, workflow queries)
  - Exposes: Workflow snapshot list with state, history, version

#### HealthChecker
- **Purpose:** Validate state consistency and absence of failures
- **Responsibilities:**
  - Assert: no workflows in FAILED state
  - Assert: no stuck workflows
  - Assert: all expected workflows present
  - Assert: workflow state transitions valid
  - Assert: no data corruption (check key fields)
- **Interfaces:**
  - Consumes: WorkflowValidator results
  - Exposes: Pass/fail verdict with failure list

#### MetricsCollector
- **Purpose:** Aggregate transition health metrics
- **Responsibilities:**
  - Count workflows by state and version
  - Calculate completion rate: completed / (created + processing)
  - Measure throughput: orders / minute
  - Track version distribution: % v1 vs v2
  - Compare before/after metrics
- **Interfaces:**
  - Consumes: WorkflowValidator results
  - Exposes: Metrics summary (JSON)

#### ReportGenerator
- **Purpose:** Create human + machine-readable report
- **Responsibilities:**
  - Format metrics summary
  - Summarize failures (if any)
  - Provide pass/fail verdict
  - Generate recommendations
  - Include workflow version breakdown
- **Interfaces:**
  - Consumes: HealthChecker + MetricsCollector
  - Produces: Report (JSON + text)

### Validation Model

**Health Criteria:**

```
PASS if:
  ✓ Zero workflow failures (no exceptions in history)
  ✓ Zero stuck workflows (all progressing or completed)
  ✓ Zero data corruption (state fields present and valid)
  ✓ Version distribution correct (new → v2, old → v1)
  ✓ Completion rate ≥ 95% (within SLA)
  ✓ Throughput maintained within 10% variance

FAIL if:
  ✗ Any workflow in FAILED state
  ✗ Any workflow stuck > 5 minutes
  ✗ Any missing/corrupted state fields
  ✗ Version mismatch (new workflow on v1, old on v2)
  ✗ Completion rate < 95%
  ✗ Throughput drop > 10%
```

### Configuration Model

```yaml
validation:
  # Workflow query settings
  task-queue: processing
  namespace: processing

  # Timeout thresholds
  stuck-threshold-minutes: 5      # workflow unchanged for 5 min
  completion-sla-minutes: 5       # order should complete in 5 min

  # Health criteria
  min-completion-rate: 0.95       # 95% must complete
  max-throughput-variance: 0.10   # ±10% acceptable

  # Metrics collection
  baseline-period: 60             # seconds before transition
  transition-period: 300          # seconds during/after transition

  # Report
  output-format: json+text        # JSON for parsing, text for humans
  include-failure-details: true   # detailed failure info in report
```

### Data Model

**Workflow Snapshot:**
```java
class WorkflowSnapshot {
  String orderId;                    // workflow ID
  WorkflowState state;               // created | processing | completed | failed
  String buildId;                    // v1 | v2 (version routing)
  LocalDateTime created;
  LocalDateTime lastUpdated;
  List<String> errors;               // if any exceptions in history
  boolean isStuck;                   // no progress > threshold
  boolean hasDataCorruption;         // invalid state fields
}
```

**Validation Report:**
```json
{
  "verdict": "PASS",
  "timestamp": "2026-03-18T15:30:00Z",
  "transition": {
    "from_version": "v1",
    "to_version": "v2",
    "duration_seconds": 300
  },
  "metrics": {
    "total_workflows": 100,
    "by_state": {
      "created": 5,
      "processing": 10,
      "completed": 85,
      "failed": 0
    },
    "by_version": {
      "v1": {"count": 50, "state": "completed"},
      "v2": {"count": 50, "state": "mixed"}
    },
    "completion_rate": 0.99,
    "throughput": {
      "before_transition": 10.5,
      "after_transition": 10.2,
      "variance": -0.03
    }
  },
  "failures": [],
  "stuck_workflows": [],
  "recommendations": []
}
```

---

## Implementation Strategy

### Phase 1: WorkflowValidator
**Goal:** Query Temporal and collect workflow state

Deliverables:
- [ ] WorkflowValidator service
- [ ] Temporal SDK client integration
- [ ] Workflow query logic (state, history, stuck detection)
- [ ] Unit tests (mock Temporal responses)

### Phase 2: HealthChecker & MetricsCollector
**Goal:** Validate state and collect metrics

Deliverables:
- [ ] HealthChecker with assertions
- [ ] MetricsCollector (aggregation logic)
- [ ] Failure detection
- [ ] Data corruption detection
- [ ] Unit tests (mock workflow data)

### Phase 3: ReportGenerator
**Goal:** Create human + machine-readable report

Deliverables:
- [ ] Report formatting (JSON + text)
- [ ] Pass/fail verdict logic
- [ ] Recommendations generation
- [ ] HTML report option (nice-to-have)

### Phase 4: Test Script & Integration
**Goal:** Run validation against live system

Deliverables:
- [ ] `scripts/validate-worker-versions.sh` (orchestrates validation)
- [ ] Integration test with real Temporal cluster
- [ ] Example report
- [ ] Documentation (how to run, interpret results)

### Critical Files / Modules

**To Create:**
- `java/validation-framework/` (new module) OR add to load-generator?
  - `ValidationFramework.java` (main entry point)
  - `WorkflowValidator.java`
  - `HealthChecker.java`
  - `MetricsCollector.java`
  - `ReportGenerator.java`
  - `WorkflowSnapshot.java`
  - `ValidationReport.java`
- `scripts/validate-worker-versions.sh`
- `docs/validation-framework-guide.md`

**To Modify:**
- `java/pom.xml` (add validation-framework module if separate)
- Load-generator module (if validation code embedded there)

---

## Testing Strategy

### Unit Tests
- WorkflowValidator parses Temporal responses correctly
- HealthChecker correctly identifies failures, stuck workflows
- MetricsCollector calculates rates accurately
- ReportGenerator formats output correctly

### Integration Tests
- Can query real Temporal cluster workflows
- Detects known failures (workflows with exceptions)
- Detects known stuck workflows (no progress)
- Report format is valid JSON

### Validation Test Scenario

**Test: Full Version Transition Validation**
1. Load generator submits 50 orders (baseline)
2. Collect metrics: throughput, completion rate
3. Deploy v2 workers
4. Load generator submits 50 more orders
5. Wait for all workflows to complete (5 min SLA)
6. Run validation framework:
   - Query all 100 workflows
   - Check for failures, stuck workflows, data issues
   - Collect metrics (before/after transition)
   - Generate report
7. Verify report shows:
   - PASS verdict (all criteria met)
   - Zero failures
   - 50 workflows on v1, 50 on v2
   - Completion rate ≥ 95%
   - Throughput stable

**Acceptance Criteria:**
- [ ] Validation framework completes without errors
- [ ] Report format valid JSON + human-readable
- [ ] Report shows correct workflow counts and versions
- [ ] All workflows accounted for (v1 + v2 = total)
- [ ] Zero unexpected failures
- [ ] Metrics show version distribution accurately
- [ ] Recommendations provided if issues detected

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Temporal queries timeout or fail | High | Low | Set reasonable query timeouts (30 sec per workflow); retry logic; handle timeouts gracefully |
| Validation logic has false positives (marks PASS incorrectly) | High | Medium | Conservative assertions (fail rather than pass on ambiguity); comprehensive unit tests |
| Report doesn't capture all failures | Medium | Medium | Query full workflow history, not just state; include error logs in report |
| Validation takes too long (>5 min for 100 workflows) | Medium | Low | Batch queries, use pagination; set timeout for full validation (e.g., 10 min max) |
| Metrics calculations incorrect | Medium | Low | Unit test metrics logic with known inputs; manual spot-check calculations |

---

## Dependencies

### External Dependencies
- Temporal Java SDK 1.33+
- Java 21+

### Cross-Cutting Concerns
- **Load Generation:** Provides orders for testing (from load-generation spec)
- **Worker Versioning:** Must have v1 and v2 configured (from version-deployment spec)
- **Temporal Cluster:** Must be running and queryable

### Rollout Blockers
- [ ] Load generation service deployed
- [ ] Worker versions (v1, v2) deployed
- [ ] Temporal cluster healthy

---

## Open Questions & Notes

### Questions for Tech Lead / Product

- [ ] Separate validation module or embed in load-generator?
- [ ] Report format: JSON only, or HTML dashboard too?
- [ ] Failure threshold: Fail on first issue or collect all and report?
- [ ] Should validation be part of CI/CD pipeline later?

### Implementation Notes

- **Query performance:** Batch workflows in groups of 10-20 (avoid timeout)
- **Stuck detection:** Use last update timestamp from workflow state, not history
- **Data corruption:** Check key fields (order ID, completion status, amounts)
- **Version verification:** Use Temporal workflow metadata (if available) or infer from history
- **Report output:** Both JSON (for automation) and text (for human review)

---

## References & Links

- [Worker Version Enablement Initiative](../INDEX.md)
- [Load Generation Service](../load-generation/spec.md)
- [Version Deployment Setup](../version-deployment/spec.md)
- [Temporal Workflow Queries](https://docs.temporal.io/concepts/what-is-a-query)
- [Temporal Workflow History](https://docs.temporal.io/concepts/what-is-a-workflow-history)
