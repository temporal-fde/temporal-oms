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
5. Implement `apps v2`.
6. Start fulfillment-side workers for the new path.
7. Start and ramp or promote `apps v2`.
8. Verify `fulfillment.Order` receives new-path traffic and Kafka handoffs stop for that path.

## Starting Assumptions And Setup

The only workshop state assumed before this exercise is steps 1 and 2 in
[WORKSHOP.md](../../../WORKSHOP.md): you have access to keys and `.env.local` is present in your
Codespace.

Do not assume any local services are already running. Start Temporal, set up namespaces, then start
the explicit service list below.

Run the exercise from its directory:

```bash
cd workshop/exercises/01-safe-fulfillment-handoff
```

The `scripts/` directory contains the step runners for this exercise. They start foreground
Java services and Python workers as background processes, write logs under
`.workshop/exercises/01-safe-fulfillment-handoff/logs`, and write PID files under the matching
`run` directory. Temporal CLI commands are shown directly in the steps because they are the
important rollout mechanics.

Start Temporal server in its own terminal and leave it running:

```bash
temporal server start-dev \
  --ip 0.0.0.0 \
  --port 7233 \
  --ui-ip 0.0.0.0 \
  --ui-port 8233
```

Set up namespaces and Nexus endpoints:

```bash
../../../scripts/setup-temporal-namespaces.sh
```

## Initial Services

Start only the services needed for baseline order traffic and the enablements load generator:

- `apps-api`
- `apps-workers v1`
- `processing-api`
- `processing-workers v1`
- `enablements-api`
- `enablements-workers`

Do not start fulfillment workers yet. The legacy path should prove that orders are flowing through
`apps v1 -> processing -> Kafka fulfillment` before `apps v2` starts using `fulfillment.Order`.

```bash
./scripts/start-initial-services.sh
```

`start-initial-services.sh` builds Java, starts the six initial services, and waits for readiness.
It does not run Worker Deployment commands.

Useful runtime commands:

```bash
./scripts/status.sh
./scripts/logs.sh apps-workers-v1
./scripts/stop.sh
```

## 1. Confirm `v1` Is Current

Set both deployments to `v1`, then confirm the state:

```bash
temporal worker deployment set-current-version \
  --deployment-name processing \
  --build-id v1 \
  --namespace processing \
  --yes

temporal worker deployment set-current-version \
  --deployment-name apps \
  --build-id v1 \
  --namespace apps \
  --yes
```

```bash
temporal worker deployment describe \
  --name processing \
  --namespace processing

temporal worker deployment describe \
  --name apps \
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

> Only edit the processing proto contract and the **processing** OrderImplV1 Java file in this
> step. The apps context will change shortly.

Apply the **processing** changes from [SOLUTION.md](SOLUTION.md#processing-v2-code). This is a
guided copy/paste change. When that solution section is complete, come back here and continue with
Step 5.

- Add `send_fulfillment` to the
  [processing proto contract](../../../proto/acme/processing/domain/v1/workflows.proto).
- Regenerate protobuf outputs with the
  [project-root generate script](../../../scripts/generate.sh).
- Guard the legacy Kafka handoff in
  [processing OrderImplV1.java](../../../java/processing/processing-core/src/main/java/com/acme/processing/workflows/OrderImplV1.java).
- Keep the default backward-compatible: absent `send_fulfillment` means `true`.

The solution file shows repo-root paths. Keep this terminal in the exercise directory for the
scripts, but make code edits against the repo-root files it names.

## 5. Start `processing v2`

Build and run a second processing worker process with the same deployment name and a new build ID:

```bash
./scripts/start-processing-v2.sh
```

Confirm `processing v2` is polling:

```bash
temporal worker deployment describe \
  --name processing \
  --namespace processing
```

Do not stop `processing v1`. Existing pinned executions may still need it.

## 6. Promote `processing v2`

```bash
temporal worker deployment set-current-version \
  --deployment-name processing \
  --build-id v2 \
  --namespace processing \
  --yes
```

```bash
temporal worker deployment describe \
  --name processing \
  --namespace processing
```

Expected result: new `processing.Order` executions are pinned to `processing v2`.

Why this is safe: `apps v1` still does not set `send_fulfillment`, and `processing v2` treats the
absent field as `true`, so old app traffic still publishes the legacy Kafka handoff.

## 7. Implement `apps v2`

Apply the **apps** changes from [SOLUTION.md](SOLUTION.md#apps-v2-code) in
[apps OrderImplV1.java](../../../java/apps/apps-core/src/main/java/com/acme/apps/workflows/OrderImplV1.java).
The fulfillment wiring helpers are already in the class. The coding activity is calling those
helpers from the workflow path and setting `send_fulfillment=false` on the processing request.
When that solution section is complete, come back here and continue with Step 8:

- Start `fulfillment.Order` through the `Fulfillment` Nexus service.
- Continue calling `processing.Order`.
- Send `send_fulfillment=false` in the processing request.
- After processing succeeds, send `fulfillment.fulfillOrder(...)`.

## 8. Start Fulfillment Workers For The New Path

Do this after the legacy path is proven and before any `apps v2` worker receives traffic. The
initial service list intentionally left fulfillment stopped so the baseline generator shows
`apps v1 -> processing -> Kafka fulfillment`.

```bash
./scripts/start-fulfillment.sh
```

Expected result: Java fulfillment workers are healthy and the Python worker logs
`All workers polling`.

You do not need to start `fulfillment-api` for this exercise. The new path reaches
`fulfillment.Order` through the `oms-fulfillment-v1` Nexus endpoint.

## 9. Start `apps v2`

Build and run a second apps worker process with the same deployment name and a new build ID:

```bash
./scripts/start-apps-v2.sh
```

Confirm `apps v2` is polling:

```bash
temporal worker deployment describe \
  --name apps \
  --namespace apps
```

Do not stop `apps v1`. Existing pinned executions may still need it.

## 10. Move Traffic To `apps v2`

For a visible mixed period, ramp `apps v2` first:

```bash
temporal worker deployment set-ramping-version \
  --deployment-name apps \
  --build-id v2 \
  --percentage 50 \
  --namespace apps \
  --yes
```

OR, If you want a direct cutover instead:

```bash
temporal worker deployment set-current-version \
  --deployment-name apps \
  --build-id v2 \
  --namespace apps \
  --yes
```

Expected result during the ramp: the generator keeps submitting orders; some new `apps.Order`
executions run on `apps v1`, and some run on `apps v2`.

## 11. Inspect Proof

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

## 12. Complete The Cutover

```bash
temporal worker deployment set-current-version \
  --deployment-name apps \
  --build-id v2 \
  --namespace apps \
  --yes
```

```bash
temporal worker deployment describe \
  --name processing \
  --namespace processing

temporal worker deployment describe \
  --name apps \
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

Stop exercise services when you are done:

```bash
./scripts/stop.sh
```

## Takeaway

Code changes create new worker behavior. Starting a worker with a new build ID makes that behavior
available to Temporal. Worker Deployment commands decide when new workflow executions receive that
behavior.
