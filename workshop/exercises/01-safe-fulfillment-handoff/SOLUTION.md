# Solution: Safely Move Fulfillment Ownership

Source spec: [spec.md](../../../specs/workshop/exercises/01-safe-fulfillment-handoff/spec.md)  
Participant guide: [README.md](README.md)

This file contains the code solution used during the exercise.

You may apply the `processing v2` and `apps v2` code changes separately, matching the exercise
steps, or apply all code changes in one pass. The safe rollout order is still:

1. Start and promote `processing v2`.
2. Start and ramp or promote `apps v2`.

Paths and code-generation commands in this file are repo-root relative. Any command that starts
with `scripts/` means the project-root `scripts/` directory, not this exercise's local `scripts/`
directory. The exercise step scripts can still be run from
`workshop/exercises/01-safe-fulfillment-handoff`.

## Processing v2 Code

### 1. Add The Routing Slip Field

Edit
[proto/acme/processing/domain/v1/workflows.proto](../../../proto/acme/processing/domain/v1/workflows.proto):

```proto
message ProcessOrderRequestExecutionOptions {
  optional int64 processing_timeout_secs = 1;
  optional acme.oms.v1.OmsProperties oms_properties = 2;
  optional bool send_fulfillment = 3;
}
```

Regenerate protobuf outputs with project-root
[scripts/generate.sh](../../../scripts/generate.sh):

```bash
scripts/generate.sh
```

If your terminal is still in the exercise directory from the participant guide, run:

```bash
../../../scripts/generate.sh
```

Do not hand-edit generated files.

### 2. Guard The Legacy Kafka Handoff

File:
[java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImpl.java](../../../java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImpl.java)

Read the routing slip after request options have been loaded or merged:

```java
boolean sendFulfillment =
    !opts.hasSendFulfillment() || opts.getSendFulfillment();
```

Use the value around the legacy Kafka handoff:

```java
if (sendFulfillment) {
    try {
        this.state = this.state.toBuilder()
                .setFulfillment(this.fulfillments.fulfillOrder(
                        FulfillOrderRequest.newBuilder()
                                .setOrder(request.getOrder())
                                .addAllItems(this.state.getEnrichment().getItemsList())
                                .build()))
                .build();
    } catch (ApplicationFailure e) {
        if (e.isNonRetryable()) {
            // permanent failure handling remains unchanged
        }
    }
}
```

The default is intentionally legacy-compatible. If `apps v1` omits `send_fulfillment`,
`processing v2` still publishes the Kafka fulfillment handoff.

Do not use `Workflow.getVersion` for this handoff. Pinned Worker Versioning keeps old executions on
old code; the routing slip records the per-order contract.

## Apps v2 Code

File:
[java/apps/apps-core/src/main/java/com/acme/apps/workflows/OrderImpl.java](../../../java/apps/apps-core/src/main/java/com/acme/apps/workflows/OrderImpl.java)

The `apps v2` behavior is:

1. Create a `Fulfillment` Nexus stub from the `order-fulfillment` endpoint in `OmsProperties`.
2. Build `StartOrderFulfillmentRequest` from the submitted order.
3. Start `fulfillment.validateOrder(...)` with `Async.function(...)`.
4. Call `processing.processOrder(...)`.
5. After processing succeeds, wait for the fulfillment validation promise.
6. Call `fulfillment.fulfillOrder(...)` with enriched items.
7. Set the routing slip when building the processing request:

```java
.setOptions(ProcessOrderRequestExecutionOptions.newBuilder()
        .setProcessingTimeoutSecs(state.getOptions().getProcessingTimeoutSecs())
        .setSendFulfillment(false)
        .build())
```

That final field is the duplicate-handoff guard. `apps v2` is not complete until new processing
workflow inputs visibly include `send_fulfillment=false`.

## Worker Deployment Properties

Both worker configs must use Temporal Worker Deployment properties. The build ID is runtime
configuration, not a source edit.

Apps config:
[java/apps/apps-core/src/main/resources/acme.apps.yaml](../../../java/apps/apps-core/src/main/resources/acme.apps.yaml)

```yaml
deployment-properties:
  use-versioning: true
  default-versioning-behavior: PINNED
  deployment-name: ${TEMPORAL_DEPLOYMENT_NAME:apps}
  build-id: ${TEMPORAL_WORKER_BUILD_ID:local}
```

Processing config:
[java/processing/processing-core/src/main/resources/acme.processing.yaml](../../../java/processing/processing-core/src/main/resources/acme.processing.yaml)

```yaml
deployment-properties:
  use-versioning: true
  default-versioning-behavior: PINNED
  deployment-name: ${TEMPORAL_DEPLOYMENT_NAME:processing}
  build-id: ${TEMPORAL_WORKER_BUILD_ID:local}
```

Rules:

- Same Temporal task queue across versions.
- Same `TEMPORAL_DEPLOYMENT_NAME` across versions of one service.
- Different `TEMPORAL_WORKER_BUILD_ID` for each worker version.
- Unique local HTTP and management ports only because multiple JVMs run on one machine.

## Build And Run Commands

The participant guide uses exercise-specific scripts for these steps. The commands below are the
manual equivalent that those scripts wrap.

Build processing after applying `processing v2`:

```bash
cd java
mvn -pl processing/processing-workers -am -DskipTests install
cd ..
```

Run `processing v2`:

```bash
TEMPORAL_DEPLOYMENT_NAME=processing \
TEMPORAL_WORKER_BUILD_ID=v2 \
java -jar java/processing/processing-workers/target/processing-workers-1.0.0-SNAPSHOT.jar \
  --server.port=8072 \
  --management.server.port=9083
```

Build apps after applying `apps v2`:

```bash
cd java
mvn -pl apps/apps-workers -am -DskipTests install
cd ..
```

Run `apps v2`:

```bash
TEMPORAL_DEPLOYMENT_NAME=apps \
TEMPORAL_WORKER_BUILD_ID=v2 \
java -jar java/apps/apps-workers/target/apps-workers-1.0.0-SNAPSHOT.jar \
  --server.port=8082 \
  --management.server.port=9093
```

## Traffic Generator

The exercise uses the existing enablements load generator instead of one-off scenario scripts.

```bash
export ENABLEMENT_ID="safe-handoff-$(date +%Y%m%d%H%M%S)"

temporal workflow start \
  --task-queue enablements \
  --type WorkerVersionEnablement \
  --workflow-id "${ENABLEMENT_ID}" \
  --namespace default \
  --input "{\"enablementId\":\"${ENABLEMENT_ID}\",\"orderCount\":1000,\"submitRatePerMin\":12,\"timeout\":\"900s\",\"orderIdSeed\":\"order\"}" \
  --input-meta 'encoding=json/protobuf'
```

Generated order IDs follow:

```text
{order_id_seed}-{enablement_id}-{timestamp_millis}
```

For this exercise, order IDs start with `order-${ENABLEMENT_ID}`.

## Verification

Minimum acceptance checks:

- `processing v2` with no `send_fulfillment` option still calls `Fulfillments.fulfillOrder`.
- `processing v2` with `send_fulfillment=false` skips `Fulfillments.fulfillOrder`.
- `apps v2` creates a `ProcessOrderRequest` whose options include `send_fulfillment=false`.
- A new-path order creates a `fulfillment.Order` execution.
- A new-path order does not create a Kafka fulfillment record.
- Old pinned `apps.Order` and `processing.Order` executions complete on their original build IDs.
