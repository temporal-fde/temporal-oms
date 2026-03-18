# Worker Version Enablement Workflow Specification

**Application:** Enablements (new bounded context)
**Feature:** Worker Version Enablement Workflow
**Status:** Draft - Ready for Tech Lead Review
**Owner:** [Your Name]
**Created:** 2026-03-18
**Updated:** 2026-03-18

**Part of:** [Worker Version Enablement Initiative](../INDEX.md)
**Application Structure:** `java/enablements/enablements-core/`

---

## Overview

### Executive Summary

Create the **WorkerVersionEnablement workflow** as the core of the Enablements application - a self-referential Temporal workflow that demonstrates safe worker versioning by orchestrating orders through the entire system.

The workflow:
- Submits orders via apps-api (via activities)
- Processes them through processing-api (via activities)
- Tracks state progression (queries)
- Runs in two versions (v1 baseline, v2 with enhancements)
- Demonstrates build-id routing live during enablement sessions

**Why this approach:**
Using Temporal to teach Temporal versioning is the most powerful demonstration. The workflow itself shows how to coordinate async operations, maintain state, and handle versioning - the exact concepts we're teaching.

This is the foundation workflow for the Enablements application (future: additional educational workflows can follow the same pattern).

---

## Goals & Success Criteria

### Primary Goals
- Goal 1: WorkerVersionEnablementWorkflow submits orders continuously and reliably
- Goal 2: Workflow maintains real-time state queryable via `getState()` query method
- Goal 3: Workflow supports interactive control signals (pause, resume, transitionToV2)
- Goal 4: Workflow deploys v2 workers via activities during session
- Goal 5: Demonstrate safe version transition with zero order failures

### Acceptance Criteria
- [ ] Workflow deploys to enablements-workers in Kubernetes
- [ ] Can submit and process 20 orders continuously (12/min rate, ~2 min duration)
- [ ] getState() query returns accurate, real-time workflow state
- [ ] Transitionable from v1-only to v2 via transitionToV2() signal
- [ ] Zero orders fail during v1 → v2 transition
- [ ] Order version tracking (worker_version field) correctly identifies v1 vs v2 execution
- [ ] Documentation complete with demo scripts and runbook

---

## Current State (As-Is)

### What exists today?
- **Scenario scripts** create single orders manually (`submit-order.sh`, `capture-payment.sh`)
- **No continuous load** - orders created one-at-a-time for demos
- **No workflow state tracking** - rely on manual Temporal UI inspection
- **No metrics** - can't quantify throughput or completion rates
- **Manual control** - need to run scripts individually

### Pain points / gaps
- Can't test with multiple in-flight workflows
- No visibility into order completion stages without UI
- Difficult to reproduce load for performance testing
- Hard to validate system behavior under sustained load
- No metrics for dashboards or monitoring

---

## Desired State (To-Be)

### Architecture Overview

```
Enablements Application (new bounded context)
├── enablements-core/
│   └── WorkerVersionEnablementWorkflow (v1 & v2)
│       ├─ Activity: submitOrder (→ apps-api /commerce-app/orders)
│       ├─ Activity: enrichOrder (→ processing-api /processing)
│       ├─ Activity: capturePayment (→ processing-api /processing)
│       └─ Query: getState()
│
├── enablements-workers/
│   └── Worker pool running the workflow
│       • v1 build-id: enablements-worker:v1
│       • v2 build-id: enablements-worker:v2
│
└── enablements-api endpoints (in apps-api, separate controller)
    └─ EnablementsController: Query workflow state + control signals
       • GET /api/v1/enablements/worker-version/{enablement_id} - Get workflow state
       • POST /api/v1/enablements/worker-version/{enablement_id}/start - Trigger workflow
       • POST /api/v1/enablements/worker-version/{enablement_id}/pause - Pause workflow
       • POST /api/v1/enablements/worker-version/{enablement_id}/transition-to-v2 - Signal v2 transition
```

**Data Layer (Proto):**
```proto
// proto/acme/enablements/v1/worker_version_enablement.proto

// Start a worker versioning enablement demonstration
message StartWorkerVersionEnablementRequest {
  string demonstration_id = 1;      // e.g., "demo-session-2026-03-18"
  int32 order_count = 2;            // How many orders to process (e.g., 20)
  int32 submit_rate_per_min = 3;    // Orders per minute (e.g., 12)
  google.protobuf.Duration timeout = 4;  // How long to run (e.g., 5 minutes)
}

// State of an order being processed through the demonstration
message OrderStatus {
  string order_id = 1;
  enum Phase { SUBMITTED, ENRICHED, CAPTURED, COMPLETED, FAILED }
  Phase current_phase = 2;
  google.protobuf.Timestamp created_at = 3;
  google.protobuf.Timestamp updated_at = 4;
  string worker_version = 5;  // v1 or v2 (which worker version handled it)
}

// Current state of the worker versioning enablement demonstration
message WorkerVersionEnablementState {
  string demonstration_id = 1;

  // Counts
  int32 orders_submitted = 2;
  int32 orders_completed = 3;
  int32 orders_failed = 4;

  // Details
  repeated OrderStatus recent_orders = 5;  // Last N orders for visibility

  // Versioning info
  enum DemoPhase { RUNNING_V1_ONLY, TRANSITIONING_TO_V2, RUNNING_BOTH, COMPLETE }
  DemoPhase current_phase = 6;

  // Metrics
  float orders_per_minute = 7;
  float completion_rate = 8;  // completed / submitted %
}
```

### Key Capabilities
- **Continuous Submission:** Generate orders at configurable rate
- **State Tracking:** Query workflows to track progress stages
- **Metrics Exposition:** Prometheus-compatible `/metrics` endpoint
- **REST Control:** Start/stop load without code changes
- **Kubernetes Native:** ConfigMap-driven configuration, health checks

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Separate service (not embedded in worker) | Load generation is test infrastructure; keep separate from production code | Embed in processing-workers - couples test logic to production |
| State tracking via Temporal queries | Direct queries give exact, point-in-time state; no external storage needed | External database - adds complexity, eventual consistency issues |
| Metrics via Micrometer/Prometheus | Industry standard; integrates with existing Grafana stack | Custom metrics format - requires custom dashboards |
| ConfigMap-driven load rate | Enables runtime adjustment without code changes | Hardcoded rate - requires redeployment to change |

### Component Design

#### WorkerVersionEnablementWorkflow
- **Purpose:** Orchestrate orders through system while team manually controls v2 deployment, demonstrating safe worker versioning interactively
- **Interface:**
  ```java
  @WorkflowInterface
  public interface WorkerVersionEnablementWorkflow {
    @WorkflowMethod
    void startDemonstration(StartWorkerVersionEnablementRequest request);

    @QueryMethod
    WorkerVersionEnablementState getState();

    // Control signals for interactive demo
    @SignalMethod
    void pause();

    @SignalMethod
    void resume();

    @SignalMethod
    void transitionToV2();  // Team triggers this manually during session
  }
  ```
- **Workflow Logic:**
  - **Phase 1 (RUNNING_V1_ONLY):**
    - Continuously submit orders at configured rate
    - Process via apps-api and processing-api
    - Track each order's state and which version handled it
    - Wait for signal: transitionToV2()

  - **Phase 2 (On transitionToV2() signal):**
    - Trigger activities:
      - deployV2Workers() - kubectl deploy v2
      - registerCompatibility() - Temporal build-id setup
    - Update DemoPhase → TRANSITIONING_TO_V2
    - Continue order processing (now both v1 and v2 available)
    - Update DemoPhase → RUNNING_BOTH when deployment complete

  - **Responsibilities:**
    - Maintain continuous order flow (submit → enrich → capture → complete)
    - Track state: submitted, completed, failed counts
    - Record worker_version for each order (auto-detected from activity execution)
    - Respond to control signals (pause, resume, transitionToV2)
    - Provide real-time state via getState() query

#### Activities (enablements-core)
**OrderActivities:**
- `submitOrder(orderId)` → HTTP POST to apps-api `/api/v1/commerce/orders`
  - Calls standard commerce API (same as production orders)
  - Handle retry logic (exponential backoff)
  - Return: order confirmation or failure

**ProcessingActivities:**
- `enrichOrder(orderId)` → HTTP POST to processing-api `/api/v1/enrichment`
  - Calls standard processing API
- `capturePayment(orderId)` → HTTP POST to processing-api `/api/v1/payments/capture`
  - Calls standard payment capture API
- Each can fail (activity retries handled by Temporal)
- **Note:** Activities call production API paths, not special enablements paths. The workflow demonstrates using versioning with real application flows.

#### Query Handler
- **Purpose:** Expose workflow state during demo
- `getStatus()` returns:
  - Orders submitted, completed, failed counts
  - Recent order IDs and their states
  - Submission rate
  - Used by enablements-api or CLI to monitor progress

### Configuration Model

```yaml
# application.yaml
load-generation:
  rate: 1                    # orders per second
  max-concurrent: 50         # max in-flight orders
  submission-timeout: 5000   # ms to wait for api response

  # State tracking
  query-interval: 2000       # ms between workflow queries
  stuck-timeout: 300000      # ms before workflow considered stuck (5 min)

  # Apps API integration
  apps-api-endpoint: ${APPS_API_ENDPOINT:http://localhost:8080}
  apps-api-timeout: 10000    # ms

  # Temporal integration
  temporal:
    namespace: processing    # where order workflows run
    task-queue: processing
```

### Data Model

**Order Record:**
```java
class OrderRecord {
  String orderId;           // UUID
  LocalDateTime created;    // when submitted
  WorkflowState state;      // created | processing | completed | failed
  LocalDateTime lastQueried; // last state check time
  String lastError;         // if failed
}

enum WorkflowState {
  CREATED,                  // submitted, awaiting processing
  PROCESSING,               // in-flight in workflow
  COMPLETED,                // workflow finished successfully
  FAILED,                   // workflow errored or stuck
}
```

**Metrics Exposed:**
```
load_gen_orders_created_total    {counter}  # Total submitted
load_gen_orders_processing       {gauge}    # Currently in-flight
load_gen_orders_completed_total  {counter}  # Finished successfully
load_gen_orders_failed_total     {counter}  # Failed/stuck
load_gen_submission_rate_sec     {gauge}    # Current submission rate
load_gen_completion_rate_percent {gauge}    # Completed / Created %
```

### Deployment Model

**Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: load-generator
  namespace: temporal-oms-tools
spec:
  replicas: 1               # Single generator instance
  selector:
    matchLabels:
      app: load-generator
  template:
    containers:
    - name: load-gen
      image: temporal-oms/load-generator:latest
      ports:
      - containerPort: 8082
        name: http
      - containerPort: 9093
        name: metrics
      env:
      - name: SPRING_PROFILES_ACTIVE
        value: k8s
      - name: LOAD_GENERATION_RATE
        value: "1"           # orders/sec (configurable)
      - name: MAX_CONCURRENT_ORDERS
        value: "50"
      resources:
        requests:
          memory: "256Mi"
          cpu: "100m"
        limits:
          memory: "1Gi"
          cpu: "500m"
```

---

## Implementation Strategy

### Phase 1: Proto Definitions & Core Workflow
**Goal:** Define data contracts and implement workflow

Deliverables:
- [ ] Proto file: `proto/acme/enablements/v1/worker_version_enablement.proto`
  - LoadTestRequest, OrderState, LoadTestStatus messages
  - Code generation: creates Java POJOs
- [ ] Maven module: `java/enablements/enablements-core/pom.xml`
- [ ] Workflow interface: `WorkerVersionEnablementWorkflow.java`
- [ ] Implementation: `WorkerVersionEnablementWorkflowImpl.java` (v1)
  - Loop: submit order → process → track state
  - Query method: getStatus()
  - Signal methods: pause(), resume()
- [ ] Activity interfaces and implementations
  - OrderActivities: submitOrder(orderId)
  - ProcessingActivities: enrichOrder(), capturePayment()
- [ ] Unit tests (mocked HTTP calls to apps-api/processing-api)

### Phase 2: Enablements Workers
**Goal:** Deploy workflow with versioning support

Deliverables:
- [ ] Maven module: `java/enablements/enablements-workers/pom.xml`
- [ ] WorkerApplication.java (Spring Boot entry point)
- [ ] Worker registration with build-ids
  - v1 build-id: `enablements-worker:v1`
  - Configuration via env vars
- [ ] application.yaml + application-k8s.yaml
- [ ] Dockerfile
- [ ] `k8s/base/enablements/deployment-workers.yaml`
- [ ] Integration tests (real Temporal workflow execution)

### Phase 3: Enablements Controller (Optional - for monitoring API)
**Goal:** Add REST endpoints to apps-api for workflow control and monitoring

Deliverables:
- [ ] EnablementsController in `java/apps/apps-api/src/main/java/com/acme/enablements/controllers/`
  - Separate controller (not conflated with CommerceWebhookController)
  - Inject WorkflowClient (reuse from apps-api Spring config)
  - Endpoints:
    - `GET /api/v1/enablements/worker-version/{enablement_id}` - Query workflow state
    - `POST /api/v1/enablements/worker-version/{enablement_id}/start` - Start demonstration
    - `POST /api/v1/enablements/worker-version/{enablement_id}/pause` - Pause workflow
    - `POST /api/v1/enablements/worker-version/{enablement_id}/transition-to-v2` - Signal v2 transition
- [ ] Response DTOs (e.g., WorkerVersionEnablementStateDto)
- [ ] Unit tests
- [ ] **Can be deferred** if using Temporal CLI or direct workflow execution for demo

### Phase 4: Versioning & Demo Scripts
**Goal:** Create v2 workflow and demo automation

Deliverables:
- [ ] `WorkerVersionEnablementWorkflowImplV2.java`
  - Same logic as v1 (or with enhancements for teaching)
  - Registered with build-id: `enablements-worker:v2`
- [ ] Demo scripts:
  - `scripts/start-enablement-workflow.sh` - Start v1 workflow
  - `scripts/deploy-enablement-v2.sh` - Deploy v2 workers, register compatibility
  - `scripts/query-enablement-status.sh` - Monitor progress
- [ ] Talk track document: `docs/enablements/worker-versioning-talk-track.md`
- [ ] Runbook: `docs/enablements/worker-versioning-runbook.md`

### Critical Files / Modules

**Proto Definitions (New):**
- `proto/acme/enablements/v1/worker_version_enablement.proto`
  - `StartWorkerVersionEnablementRequest` message (input to workflow)
  - `OrderStatus` message (state of individual order)
  - `WorkerVersionEnablementState` message (output from workflow queries)

**To Create (enablements-core):**
- `java/enablements/enablements-core/pom.xml`
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/workflows/WorkerVersionEnablementWorkflow.java`
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/workflows/WorkerVersionEnablementWorkflowImpl.java` (v1)
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/activities/OrderActivities.java`
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/activities/ProcessingActivities.java`

**To Create (enablements-workers):**
- `java/enablements/enablements-workers/pom.xml`
- `java/enablements/enablements-workers/src/main/java/com/acme/enablements/WorkerApplication.java`
- `java/enablements/enablements-workers/src/main/resources/application.yaml`
- `java/enablements/enablements-workers/docker/Dockerfile`
- `k8s/base/enablements/deployment-workers.yaml`

**To Create (enablements controller - optional, in apps-api):**
- `java/apps/apps-api/src/main/java/com/acme/enablements/controllers/EnablementsController.java`
- `java/apps/apps-api/src/main/java/com/acme/enablements/dto/` (Response DTOs)
  - `WorkerVersionEnablementStateDto.java`
  - `EnablementResponse.java`
- Tests for EnablementsController

**To Create (Parent):**
- `java/enablements/pom.xml` (parent pom with modules: core, workers)

**To Modify:**
- `java/pom.xml` - Add enablements module
- `proto/acme/pom.xml` - Add enablements proto generation
- `k8s/base/kustomization.yaml` - Add enablements deployments
- `k8s/base/processing/kustomization.yaml` - Include enablements deployments
- `scripts/app-deploy.sh` - Build enablements images
- `java/apps/apps-api/pom.xml` - (already has Temporal SDK, no changes needed)
- `java/apps/apps-api/src/main/java/com/acme/apps/ApiApplication.java` - (already has @ComponentScan for multiple packages)

---

## Testing Strategy

### Unit Tests
- OrderSubmitter generates valid order IDs
- OrderSubmitter handles submission errors (retries, timeout)
- WorkflowStateTracker parses workflow state correctly
- MetricsCollector accumulates metrics accurately
- LoadController REST endpoints respond correctly

### Integration Tests
- Workflow connects to Temporal cluster and executes activities
- Can query real workflow state via Temporal SDK
- OrderActivities successfully call apps-api and processing-api
- ProcessingActivities successfully call processing-api (or use test doubles)
- EnablementsController (if implemented) correctly queries and signals workflows via REST API

### Demonstration Scenario

**Scenario: Worker Versioning Enablement Under Realistic Load**

1. **Initialize:** Start WorkerVersionEnablementWorkflow v1
   - Script or curl: `POST http://localhost:8080/api/v1/enablements/worker-version/demo-session-1/start` (or use Temporal SDK directly)
   - Request: 20 orders, 12/min rate, 5-minute duration
   - DemoPhase: RUNNING_V1_ONLY
   - Workflow begins submitting orders to apps-api `/api/v1/commerce/orders`

2. **Monitor:** Query workflow state every 10 seconds
   - Script or curl: `GET http://localhost:8080/api/v1/enablements/worker-version/demo-session-1` (or use Temporal SDK)
   - Verify: Orders submitting at ~12/min (from workflow activities)
   - Verify: Orders progressing through phases (enrichment, payment capture)
   - Verify: worker_version field shows "v1"

3. **Transition (at ~2 min mark):** Deploy v2 workers, mark compatible
   - Script or curl: `POST http://localhost:8080/api/v1/enablements/worker-version/demo-session-1/transition-to-v2` (sends signal to workflow)
   - Workflow activity deployV2Workers() executes kubectl deploy
   - Workflow activity registerCompatibility() sets up Temporal build-ids
   - DemoPhase transitions to: TRANSITIONING_TO_V2 → RUNNING_BOTH

4. **Observe:** Continue monitoring
   - New orders submitted after transition execute on v2 workers
   - Old orders submitted before transition continue on v1 workers
   - worker_version field shows mix: "v1" and "v2"
   - Completion rates unchanged (no failures during transition)

5. **Complete:** Wait for all orders to finish
   - Workflow final state: COMPLETE
   - All orders should be COMPLETED (0 FAILED)
   - Demonstrates: Safe worker version transition with zero downtime

**Acceptance Criteria:**
- [ ] Workflow starts and runs smoothly
- [ ] Query results provide real-time visibility (getState() returns current state)
- [ ] Orders process at configured rate (~12/min)
- [ ] DemoPhase transitions correctly reflect v1 → v2 transition
- [ ] worker_version field accurately tracks which version processed each order
- [ ] Completion rate ≥95% (at least 19/20 orders complete)
- [ ] No failures during transition (zero orders with FAILED status)
- [ ] Graceful shutdown: workflow finishes cleanly
- [ ] Demo runs as a self-contained, observable flow

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Workflow order submission fails during demo | High | Low | Test with same rate/config before live session; have fallback demo data |
| Query state() during transition shows stale data | Medium | Medium | State updates are eventual; document lag expectation (< 2 sec) |
| v2 deployment takes too long, breaks demo flow | Medium | Low | Pre-stage v2 deployment, test timing offline; use smaller order count if needed |
| Orders complete before v2 is deployed | Medium | Low | Use 20-order count with 2-min delay before deploying v2; test pacing |
| Apps-api or processing-api becomes unavailable | High | Low | Health checks before session; have secondary demo URL handy |
| Workflow crashes mid-demo | High | Low | Implement error handling and retries; monitor logs during session |

---

## Dependencies

### External Dependencies
- Spring Boot 3.5+ (web starter)
- Temporal Java SDK 1.33+
- Micrometer Prometheus (metrics)

### Cross-Cutting Concerns
- **apps-api:** Must be running for order submission
- **Temporal cluster:** Must be accessible from load-gen namespace
- **Networking:** Load-gen must reach apps-api and Temporal

### Rollout Blockers
- [ ] Temporal cluster deployed and running
- [ ] apps-api deployed and accessible
- [ ] `temporal-oms-tools` namespace exists
- [ ] KinD cluster has 256Mi headroom

---

## Open Questions & Notes

### Questions for Tech Lead / Product

- [ ] Demo duration: 5 minutes suitable for session? Or should be configurable?
- [ ] Order count: 20 orders good for demo? Or scale to show more?
- [ ] Submit rate: 12/min feels natural? Or adjust for pacing?
- [ ] Should Phase 2 transition to RUNNING_BOTH immediately after v2 deployment, or wait for explicit confirmation signal?

### Implementation Notes

- **Order ID format:** Use UUID v4 for safety (no conflicts)
- **Submission timing:** Use `CancellationScope.withTimeout()` to enforce order submission rate (12/min = submit every 5 sec)
- **DemoPhase transitions:**
  - RUNNING_V1_ONLY → TRANSITIONING_TO_V2: on `transitionToV2()` signal (team manually triggers)
  - TRANSITIONING_TO_V2 → RUNNING_BOTH: after `deployV2Workers()` and `registerCompatibility()` activities complete
  - RUNNING_BOTH → COMPLETE: after all orders submitted and timeout reached
- **Activity execution tracking:** Orders inherit worker_version from activity context (Temporal tracks which worker executed activity)
- **Workflow state size:** `WorkerVersionEnablementState` with 50 recent orders ~5KB; well within Temporal event size limits
- **Error handling:** If activity fails (apps-api down), retry with exponential backoff per Temporal defaults; continue with remaining orders

---

## References & Links

- [Worker Version Enablement Initiative](../INDEX.md)
- [Temporal Java SDK Docs](https://docs.temporal.io/dev-guide/java)
- [Micrometer Prometheus](https://micrometer.io/docs/registry/prometheus)
- [Spring Boot Health Checks](https://spring.io/guides/gs/actuator-service/)
