# Exercise 01: Safely Move Fulfillment Ownership

Source spec: [spec.md](../../../specs/workshop/exercises/01-safe-fulfillment-handoff/spec.md)  
Code solution: [SOLUTION.md](SOLUTION.md)

## Goal

Move fulfillment ownership from `processing.Order` to `apps.Order` without disrupting in-flight
orders and without using application feature flags in workflow code.

This is a live code-and-rollout exercise. You will keep order traffic running, change the code,
start new worker processes with new build IDs, and then use Temporal Worker Deployment commands to
move traffic.

You can make the `processing v2` and `apps v2` code changes separately, or make both code changes
up front. The operational rollout order stays the same:

1. Confirm `apps v1` and `processing v1` are current.
2. Start sustained order traffic.
3. Implement and start `processing v2`.
4. Promote `processing v2` to current.
5. Implement and start `apps v2`.
6. Ramp or promote `apps v2`.
7. Verify `fulfillment.Order` receives new-path traffic and Kafka handoffs stop for that path.

## Starting Assumptions

The facilitator or setup script has already started:

- Temporal server and UI.
- `apps-api`, `processing-api`, `fulfillment-api`, and integration services.
- `apps-workers v1` with `TEMPORAL_DEPLOYMENT_NAME=apps` and `TEMPORAL_WORKER_BUILD_ID=v1`.
- `processing-workers v1` with `TEMPORAL_DEPLOYMENT_NAME=processing` and
  `TEMPORAL_WORKER_BUILD_ID=v1`.
- `fulfillment-workers` and Python fulfillment workers.
- `enablements-workers` polling the `enablements` task queue.

## 1. Confirm `v1` Is Current

```bash
temporal worker deployment set-current-version \
  --deployment-name processing \
  --build-id v1 \
  --namespace processing

temporal worker deployment set-current-version \
  --deployment-name apps \
  --build-id v1 \
  --namespace apps
```

```bash
temporal worker deployment describe \
  --deployment-name processing \
  --namespace processing

temporal worker deployment describe \
  --deployment-name apps \
  --namespace apps
```

Expected result: `processing` and `apps` both show `v1` as current.

## 2. Start Sustained Traffic

Start the enablements load generator and leave it running through the rollout:

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

```bash
temporal workflow query \
  --workflow-id "${ENABLEMENT_ID}" \
  --namespace default \
  --type getState
```

Expected result: new `apps.Order` executions appear continuously in the `apps` namespace with
workflow IDs that start with `order-${ENABLEMENT_ID}`.

## 3. Observe The Legacy Path

Pick a generated order ID from Temporal UI in the `apps` namespace:

```bash
export ORDER_ID="<generated-order-id>"
curl -s "http://localhost:8071/admin/order-fulfillment/${ORDER_ID}"
```

Expected result: with `apps v1` and `processing v1`, generated orders create Kafka fulfillment
records.

## 4. Implement `processing v2`

Apply the processing changes from [SOLUTION.md](SOLUTION.md#processing-v2-code):

- Add `send_fulfillment` to the processing proto contract.
- Regenerate protobuf outputs.
- Guard the legacy Kafka handoff in `processing.OrderImpl`.
- Keep the default backward-compatible: absent `send_fulfillment` means `true`.

Build the processing worker after the code change:

```bash
cd java
mvn -pl processing/processing-workers -am -DskipTests install
cd ..
```

## 5. Start `processing v2`

Run a second processing worker process with the same deployment name and a new build ID:

```bash
TEMPORAL_DEPLOYMENT_NAME=processing \
TEMPORAL_WORKER_BUILD_ID=v2 \
java -jar java/processing/processing-workers/target/processing-workers-1.0.0-SNAPSHOT.jar \
  --server.port=8072 \
  --management.server.port=9083
```

In another terminal, confirm `v2` is polling:

```bash
temporal worker deployment describe \
  --deployment-name processing \
  --namespace processing
```

Do not stop `processing v1`. Existing pinned executions may still need it.

## 6. Promote `processing v2`

```bash
temporal worker deployment set-current-version \
  --deployment-name processing \
  --build-id v2 \
  --namespace processing
```

Expected result: new `processing.Order` executions are pinned to `processing v2`.

Why this is safe: `apps v1` still does not set `send_fulfillment`, and `processing v2` treats the
absent field as `true`, so old app traffic still publishes the legacy Kafka handoff.

## 7. Implement `apps v2`

Apply the apps changes from [SOLUTION.md](SOLUTION.md#apps-v2-code):

- Start `fulfillment.Order` through the `Fulfillment` Nexus service.
- Continue calling `processing.Order`.
- Send `send_fulfillment=false` in the processing request.
- After processing succeeds, send `fulfillment.fulfillOrder(...)`.

Build the apps worker after the code change:

```bash
cd java
mvn -pl apps/apps-workers -am -DskipTests install
cd ..
```

## 8. Start `apps v2`

Run a second apps worker process with the same deployment name and a new build ID:

```bash
TEMPORAL_DEPLOYMENT_NAME=apps \
TEMPORAL_WORKER_BUILD_ID=v2 \
java -jar java/apps/apps-workers/target/apps-workers-1.0.0-SNAPSHOT.jar \
  --server.port=8082 \
  --management.server.port=9093
```

Confirm `v2` is polling:

```bash
temporal worker deployment describe \
  --deployment-name apps \
  --namespace apps
```

Do not stop `apps v1`. Existing pinned executions may still need it.

## 9. Move Traffic To `apps v2`

For a visible mixed period, ramp `apps v2` first:

```bash
temporal worker deployment set-ramping-version \
  --deployment-name apps \
  --build-id v2 \
  --percentage 50 \
  --namespace apps
```

If you want a direct cutover instead, use `set-current-version` for `apps v2`.

Expected result during the ramp: the generator keeps submitting orders; some new `apps.Order`
executions run on `apps v1`, and some run on `apps v2`.

## 10. Inspect Proof

In Temporal UI:

- In the `apps` namespace, inspect recent `apps.Order` executions and note their Deployment
  Version.
- In the `processing` namespace, inspect the `ProcessOrderRequest` input.
- New-path processing inputs should include `options.send_fulfillment=false`.
- In the `fulfillment` namespace, confirm new-path orders create `fulfillment.Order` workflows.

For a new-path order:

```bash
export ORDER_ID="<new-path-order-id>"
curl -s "http://localhost:8071/admin/order-fulfillment/${ORDER_ID}"
```

Expected result: old-path orders have a Kafka record; new-path orders have a `fulfillment.Order`
workflow and no Kafka record.

## 11. Complete The Cutover

```bash
temporal worker deployment set-current-version \
  --deployment-name apps \
  --build-id v2 \
  --namespace apps
```

```bash
temporal worker deployment describe \
  --deployment-name processing \
  --namespace processing

temporal worker deployment describe \
  --deployment-name apps \
  --namespace apps
```

Expected result: both deployments are current on `v2`; old pinned executions continue on their
original versions until they drain.

Stop the generator when the exercise is complete:

```bash
temporal workflow terminate \
  --workflow-id "${ENABLEMENT_ID}" \
  --namespace default \
  --reason "Exercise 01 complete"
```

## Takeaway

Code changes create new worker behavior. Starting a worker with a new build ID makes that behavior
available to Temporal. Worker Deployment commands decide when new workflow executions receive that
behavior.

