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

Create the **WorkerVersionEnablement workflow** as a local enablement tool - a Temporal workflow that runs on the user's host and calls the OMS APIs (running in K8s/KinD), demonstrating safe worker versioning.

The workflow:
- Runs locally (not in K8s) - invoked via Temporal CLI or local Java execution
- Acts as an external caller - submits orders to the OMS (apps-api, processing-api running in K8s)
- Works with both local K8s (Minikube/KinD) and cloud Temporal
- Tracks only its own execution state (which version is active, submission rate, demo phase)
- Does NOT duplicate OMS state tracking (orders, completion, failures)
- Supports interactive control signals (transitionToV2) to trigger version changes
- Demonstrates build-id routing live during enablement sessions

**Why this approach:**
Using Temporal to demonstrate Temporal versioning is powerful, but the key insight is: the enablement workflow is just a *caller* of the OMS. It submits orders (like any client would) and lets the OMS do its job. The workflow demonstrates that:
1. Worker versions don't affect external callers (orders submitted successfully)
2. The OMS continues processing regardless of version transitions
3. No failures or dropped orders during the transition

This clarity separates "how we invoke the system" (enablement workflow running locally) from "how the system works" (OMS application running in K8s).

---

## Goals & Success Criteria

### Primary Goals
- Goal 1: WorkerVersionEnablementWorkflow calls OMS APIs continuously (submit → enrich → capture)
- Goal 2: Workflow tracks only its own execution state, not order details (OMS owns that)
- Goal 3: Workflow supports interactive control signals (pause, resume, transitionToV2)
- Goal 4: Workflow triggers v2 worker deployment via activities during session
- Goal 5: Demonstrate safe version transition with zero workflow or OMS failures

### Acceptance Criteria
- [ ] Workflow deploys to enablements-workers in Kubernetes
- [ ] Workflow submits 20 orders at ~12/min to the OMS
- [ ] getState() query returns accurate workflow execution state (phase, submission count, rate, versions)
- [ ] Transitionable from RUNNING_V1_ONLY to RUNNING_BOTH via transitionToV2() signal
- [ ] OMS processes all submitted orders without failures (0 FAILED orders in the OMS)
- [ ] Order completion confirmed via OMS APIs, not workflow state (workflow doesn't track that)
- [ ] Demo scripts and documentation complete

---

## Current State (As-Is)

### What exists today?
- **Scenario scripts** create single orders manually (`submit-order.sh`, `capture-payment.sh`)
- **No continuous ordering** - orders created one-at-a-time for demos
- **No coordinated load generation** - can't trigger version transitions while orders are in flight
- **Manual testing only** - can't easily show "orders flowing during version change"
- **No version transition demo** - can't show v1 → v2 switch safely in action

### Pain points / gaps
- Can't demonstrate version transitions under realistic load
- Hard to show that worker versions don't affect external callers (order clients)
- Difficult to validate system behavior when worker code changes
- No repeatable scenario for enablement/training sessions
- No clear separation between "demo infrastructure" and "production application"

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

// Current state of the worker versioning enablement demonstration
// (Order tracking is the responsibility of the OMS application, not this workflow)
message WorkerVersionEnablementState {
  string demonstration_id = 1;

  // Workflow execution state
  enum DemoPhase { RUNNING_V1_ONLY, TRANSITIONING_TO_V2, RUNNING_BOTH, COMPLETE }
  DemoPhase current_phase = 2;

  // Activity metrics
  int32 orders_submitted_count = 3;    // How many times submitOrder() was called
  float orders_per_minute = 4;         // Current submission rate
  repeated string active_versions = 5; // ["v1"] or ["v1", "v2"] depending on phase

  // Versioning info
  string last_transition_at = 6;       // ISO8601 timestamp when transitionToV2 was signaled
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
    - Call OMS APIs continuously: submitOrder → enrichOrder → capturePayment
    - Track only workflow execution state (phase, submission count, rate)
    - Respond to control signals (pause, resume, transitionToV2)
    - Provide real-time workflow state via getState() query (not order tracking—that's the OMS app's job)

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
- **Purpose:** Expose workflow execution state during demo (not order tracking—that's the OMS app's job)
- `getState()` returns:
  - Current demo phase (RUNNING_V1_ONLY, TRANSITIONING_TO_V2, RUNNING_BOTH, COMPLETE)
  - Orders submitted count (how many times submitOrder() was called)
  - Current submission rate (orders/min)
  - Active worker versions (v1 only, or both v1+v2)
  - **Note:** Order tracking (completion, failure, state progression) is the OMS app's responsibility—query apps-api or processing-api for that

### Configuration Model

```yaml
# application.yaml (for enablements-workers)
enablements:
  # Submission rate
  order-rate: 12                 # orders per minute (configurable for demo pacing)
  submission-timeout: 5000       # ms to wait for submitOrder api response

  # OMS API integration
  apps-api-endpoint: ${APPS_API_ENDPOINT:http://localhost:8080}
  processing-api-endpoint: ${PROCESSING_API_ENDPOINT:http://localhost:8081}
  api-timeout: 10000             # ms per API call

  # Temporal integration
  temporal:
    namespace: apps              # where enablement workflow runs (apps namespace, since enablement is external caller)
    task-queue: enablements      # task queue for enablement workflows
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

**Local Execution (Not Kubernetes):**
The enablement workflow runs on the user's local machine and calls the OMS APIs in K8s/KinD. No Kubernetes deployment needed.

**Invocation (from local host):**

**Option 1: Via Temporal CLI (requires temporal CLI installed)**
```bash
temporal workflow start \
  --workflow-id demo-session-1 \
  --namespace apps \
  --type WorkerVersionEnablementWorkflow \
  --task-queue enablements \
  --input '{"demonstration_id":"demo-session-1","order_count":20,"submit_rate_per_min":12,"timeout":"5m"}'
```

**Option 2: Via local Java execution**
```bash
cd java/enablements/enablements-core
mvn exec:java -Dexec.mainClass="com.acme.enablements.LocalEnablementRunner" \
  -Dexec.args="demo-session-1 20 12 5m"
```

**Option 3: Via optional EnablementsController in apps-api**
```bash
curl -X POST http://localhost:8080/api/v1/enablements/worker-version/demo-session-1/start \
  -H "Content-Type: application/json" \
  -d '{"order_count":20,"submit_rate_per_min":12,"timeout":"5m"}'
```

**Configuration:**
- OMS APIs: `APPS_API_ENDPOINT` (default: http://localhost:8080 or tunneled Traefik)
- Processing API: `PROCESSING_API_ENDPOINT` (default: http://localhost:8081 or tunneled)
- Temporal: `TEMPORAL_TARGET` (default: localhost:7233 for local, or cloud Temporal)

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

### Phase 2: Local Workflow Execution
**Goal:** Enable running the workflow from local host

Deliverables:
- [ ] LocalEnablementRunner.java - Main entry point to run workflow locally
  - Takes arguments: demonstration_id, order_count, submit_rate_per_min, timeout
  - Configures WorkflowClient for local or remote Temporal
  - Starts WorkerVersionEnablementWorkflow and tracks execution
- [ ] Configuration via environment variables:
  - `TEMPORAL_TARGET`: Temporal server address (local or cloud)
  - `APPS_API_ENDPOINT`: OMS apps-api URL
  - `PROCESSING_API_ENDPOINT`: OMS processing-api URL
- [ ] Maven configuration: `java/enablements/enablements-core/pom.xml` includes exec plugin
- [ ] Shell script: `scripts/run-enablement.sh` (optional - simplifies invocation)
- [ ] Integration tests (local Temporal workflow execution against real K8s APIs)

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
  - `WorkerVersionEnablementState` message (output from workflow queries—workflow execution state only, not order tracking)

**To Create (enablements-core):**
- `java/enablements/enablements-core/pom.xml`
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/workflows/WorkerVersionEnablementWorkflow.java`
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/workflows/WorkerVersionEnablementWorkflowImpl.java` (v1)
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/activities/OrderActivities.java`
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/activities/ProcessingActivities.java`

**To Create (local execution):**
- `java/enablements/enablements-core/src/main/java/com/acme/enablements/LocalEnablementRunner.java`
  - Main entry point (public static void main) to run workflow locally
  - Configures WorkflowClient, starts workflow, monitors execution
- `scripts/run-enablement.sh` (optional - convenience wrapper)
  - Sets env vars, calls LocalEnablementRunner with arguments

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
- `java/apps/apps-api/pom.xml` - (if implementing EnablementsController in apps-api for remote invocation)
- `java/apps/apps-api/src/main/java/com/acme/apps/ApiApplication.java` - (if implementing controller)

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

2. **Monitor Workflow State:** Query workflow state every 10 seconds
   - Script or curl: `GET http://localhost:8080/api/v1/enablements/worker-version/demo-session-1` (or use Temporal SDK)
   - Verify: Workflow submitting at ~12/min
   - Verify: DemoPhase is RUNNING_V1_ONLY
   - Verify: active_versions shows ["v1"]

3. **Monitor OMS:** In parallel, watch the OMS application
   - Orders appearing in apps-api `/orders` endpoint
   - Orders progressing through enrichment and payment capture in processing-api
   - Temporal UI shows: OrderSubmissionWorkflow, EnrichmentWorkflow, PaymentWorkflow (the real business workflows)

4. **Transition (at ~2 min mark):** Deploy v2 workers, mark compatible
   - Script or curl: `POST http://localhost:8080/api/v1/enablements/worker-version/demo-session-1/transition-to-v2` (sends signal to workflow)
   - Workflow activity deployV2Workers() executes kubectl deploy
   - Workflow activity registerCompatibility() sets up Temporal build-ids
   - DemoPhase transitions to: TRANSITIONING_TO_V2 → RUNNING_BOTH

5. **Observe Transition:** Continue monitoring
   - Workflow state: DemoPhase = RUNNING_BOTH, active_versions = ["v1", "v2"]
   - OMS continues processing orders (submit/enrich/capture)
   - Orders submitted before transition continue on v1 workers
   - Orders submitted after transition may execute on v2 workers (build-id routing)
   - **Key point:** No failures, no dropped orders—the OMS app is unaffected by the version change

5. **Complete:** Workflow reaches timeout/completion
   - Workflow final state: COMPLETE
   - Demonstrates: Safe worker version transition with zero downtime
   - OMS has processed all submitted orders (verify via OMS app, not workflow)

**Acceptance Criteria:**
- [ ] Workflow starts and runs smoothly
- [ ] getState() query returns accurate workflow execution state
- [ ] Workflow submits orders at configured rate (~12/min)
- [ ] DemoPhase transitions correctly (RUNNING_V1_ONLY → TRANSITIONING_TO_V2 → RUNNING_BOTH → COMPLETE)
- [ ] active_versions correctly reflects current versioning state
- [ ] No workflow failures during version transition
- [ ] OMS processes all submitted orders (0 FAILED in the OMS, not the workflow)
- [ ] Graceful shutdown: workflow finishes cleanly
- [ ] Demo clearly shows: enablement calls OMS, OMS handles everything else

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Workflow order submission fails during demo | High | Low | Test with same rate/config before live session; have fallback demo order flow |
| v2 deployment takes too long, breaks demo flow | Medium | Low | Pre-stage v2 deployment, test timing offline; use smaller order count if needed |
| Apps-api or processing-api becomes unavailable | High | Low | Health checks before session; verify OMS services running |
| Workflow crashes mid-demo | High | Low | Implement error handling and retries in activities; monitor Temporal logs during session |
| Order failures in OMS (not workflow's fault) | Medium | Medium | Not the workflow's responsibility, but communicate that to team; demo focuses on version transition, not order success |

---

## Dependencies

### External Dependencies
- Spring Boot 3.5+ (web starter)
- Temporal Java SDK 1.33+
- Micrometer Prometheus (metrics)

### Cross-Cutting Concerns
- **apps-api:** Must be running in K8s (for order submission)
- **Temporal cluster:** Must be running (local K8s, or cloud Temporal)
- **Networking:** Local machine must reach Temporal, apps-api, and processing-api (via tunnel or direct)

### Rollout Blockers
- [ ] Temporal cluster deployed and running (K8s or cloud)
- [ ] `apps` namespace in Temporal created
- [ ] apps-api deployed in K8s and accessible from local machine
- [ ] processing-api deployed in K8s and accessible from local machine
- [ ] Tunnel or port-forwarding setup (if using local K8s)

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
