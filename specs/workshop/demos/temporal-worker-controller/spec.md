# Demo Spec: Temporal Worker Controller Rollout

**Workshop Slot:** Post-Exercise 01 demo
**Target Timebox:** 10-15 minutes
**Demo Mode:** Instructor-led with k9s as the primary Kubernetes observation tool
**Prerequisite:** Exercise 01 has shown the manual Worker Deployment commands
**Source Material:** `java/enablements/ENABLEMENT.md`

## Purpose

Exercise 01 has participants run the Worker Deployment lifecycle directly for the fulfillment
handoff migration:

1. promote `processing v2`
2. ramp `apps v2`
3. promote `apps v2`
4. observe pinned executions and old-version drain

This demo shows the production equivalent using the existing enablements walkthrough: the Temporal
Worker Controller watches Kubernetes worker rollouts and automates a processing-worker promotion
while sustained order load is running.

The point is not to introduce a different architecture. The point is to show that TWC performs the
operational work participants just did by hand.

## Current State

The repository already has a concrete enablement walkthrough in `java/enablements/ENABLEMENT.md`
called "Safely Promoting Processing Workers Under Load." This TWC demo should be derived from that
walkthrough and updated as the Kubernetes/KinD manifests are brought current.

The repo also has a `TemporalWorkerDeployment` manifest for processing under
`k8s/processing-versioned/`.

The current application topology includes:

- `apps-api`
- `apps-workers`
- `processing-api`
- `processing-workers`
- `fulfillment-workers`
- `enablements-api`
- `enablements-workers`
- Python fulfillment workers for `agents` and `fulfillment-shipping`

This demo should depend on the updated Kubernetes/KinD manifests once that work lands. Until then,
the demo remains a planning spec, not final executable material.

## Demo Goal

Show that TWC automates Worker Deployment rollout mechanics:

- detects a new worker version from a Kubernetes rollout
- registers the new build ID
- waits for pollers
- shifts traffic according to rollout policy
- keeps in-flight pinned workflows on their original version
- sunsets old worker versions after drain

Secondary goal: show one place where `auto_upgrade` is useful. Exercise 01 rejects auto-upgrade for
order workflows because each order must keep its chosen fulfillment path. This demo can contrast
that with the long-running `support-team` workflow, where auto-upgrade can be used deliberately so
an always-running workflow stops holding old worker pods alive.

## Narrative

The talk track should explicitly connect Exercise 01's manual commands to the automated TWC flow:

| Exercise 01 manual command | TWC production behavior |
|---|---|
| `set-current-version --deployment-name processing --build-id v2` | Controller promotes or ramps the new processing Worker Deployment Version after pollers appear |
| `set-ramping-version --deployment-name apps --build-id v2 --percentage 50` | Controller applies progressive rollout steps from the `TemporalWorkerDeployment` spec |
| `set-current-version --deployment-name apps --build-id v2` | Controller completes the rollout after gates/pass conditions |
| manually stop old workers | Controller sunsets old versions after configured drain delays |

## Proposed Demo Flow

This is adapted from `java/enablements/ENABLEMENT.md`.

### Phase 1: Verify A Clean Environment

Goal: establish that the demo is starting from a known state.

1. Confirm KinD has no stale `temporal-oms` workloads.
2. Confirm the target Temporal namespaces have no active demo workflows:
   - apps namespace
   - processing namespace
   - local/default enablements namespace if the load generator runs locally

### Phase 2: Deploy The v1 Stack

Goal: get the full stack running with processing workers at `v1`.

1. Deploy the demo environment with one Kubernetes runner:

   ```bash
   OVERLAY=local ./scripts/kind/demo-up.sh
   # or
   OVERLAY=local ./scripts/k3d/demo-up.sh
   ```

   Or, for the cloud-backed version:

   ```bash
   OVERLAY=cloud ./scripts/kind/demo-up.sh
   # or
   OVERLAY=cloud ./scripts/k3d/demo-up.sh
   ```

2. Open `k9s` and point out that processing worker pods are on the `v1` deployment version.
   Keep the processing namespace in view:

   ```text
   :ctx kind-temporal-oms
   :ns temporal-oms-processing
   :pods
   ```

   Useful k9s views for this demo:
   - `:pods` — watch old and new worker pods coexist during rollout
   - `:temporalworkerdeployments` or `:twd` if the CRD alias is available — watch controller status
   - `:deploy` — inspect regular Kubernetes Deployments if needed
   - `:cm` / `:secret` — confirm config and Temporal connection resources when debugging

   If the CRD alias is not available in k9s, use the command/search prompt and enter
   `temporalworkerdeployments`.
3. Start local Temporal if the enablements workflow runs locally:

   ```bash
   temporal server start-dev
   ```

4. Start `enablements-workers` locally if it is not part of the KinD deployment yet.
   The current repo is Maven-based, so the final command should be validated during scripting.
   Likely candidates:

   ```bash
   cd java/enablements/enablements-workers
   mvn spring-boot:run
   ```

   or:

   ```bash
   java -jar java/enablements/enablements-workers/target/enablements-workers-1.0.0-SNAPSHOT.jar
   ```

### Phase 3: Generate Sustained Load

Goal: keep workflows actively starting while processing workers roll from `v1` to `v2`.

1. Tunnel from the host to the selected Kubernetes cluster:

   ```bash
   ./scripts/kind/tunnel.sh
   # or
   ./scripts/k3d/tunnel.sh
   ```

2. Start the `WorkerVersionEnablement` workflow:

   ```bash
   temporal workflow start \
     --task-queue enablements \
     --type WorkerVersionEnablement \
     --workflow-id "enablement-demo-replay-2026" \
     --namespace default \
     --input '{
       "enablementId": "demo-replay-2026",
       "orderCount": 20,
       "submitRatePerMin": 5,
       "timeout": "600s",
       "orderIdSeed": "invalid"
     }' \
     --input-meta 'encoding=json/protobuf'
   ```

3. Verify traffic is flowing:
   - apps namespace: order workflows are being created
   - processing namespace: processing workflows show `DeploymentVersion` / Worker Deployment
     Version as `v1`

### Phase 4: Promote Processing Workers To v2

Goal: trigger the TWC rollout and observe progressive promotion under load.

1. Deploy `v2` processing workers:

   ```bash
   VERSION=v2 ./scripts/kind/deploy-processing-workers.sh
   # or
   VERSION=v2 ./scripts/k3d/deploy-processing-workers.sh
   ```

2. Walk through the important lines inside the selected `deploy-processing-workers.sh`:
   - Java build
   - Docker image tag `temporal-oms/processing-workers:v2`
   - `kind load docker-image` for KinD, or `k3d image import` for k3d
   - `kubectl patch temporalworkerdeployment processing-workers ...`

3. In k9s, stay in `temporal-oms-processing` and watch `:pods`.
   The important visual is the new `processing-workers` pod coming up alongside the existing `v1`
   pod instead of replacing it abruptly.

4. In k9s, switch to the `TemporalWorkerDeployment` resource and watch controller status:

   ```text
   :temporalworkerdeployments
   ```

   or, if the alias is configured:

   ```text
   :twd
   ```

5. Watch Temporal Worker Deployment state:

   ```bash
   temporal worker deployment describe \
     --deployment-name processing \
     --namespace processing
   ```

6. In Temporal UI, show new processing workflows starting on `v2` while existing pinned workflows
   continue on `v1`.

### Phase 5: Migrate The Long-Running Support Workflow

Goal: show why old worker pods may remain alive after normal order workflows drain, and show a
case where auto-upgrade is appropriate.

1. Point out the `support-team` workflow:
   - It is long-running.
   - It waits forever and periodically continues as new only when its validation queue grows.
   - If it remains pinned to `v1`, it can keep `v1` processing pods alive indefinitely.

2. Update only this workflow to auto-upgrade:

   ```bash
   temporal workflow update-options \
     --workflow-id "support-team" \
     --versioning-override-behavior auto_upgrade \
     --namespace processing
   ```

   If using Temporal Cloud CLI environment aliases, the command may use the configured environment
   instead of `--namespace`, as in the source enablement doc:

   ```bash
   temporal workflow update-options \
     --workflow-id "support-team" \
     --versioning-override-behavior auto_upgrade \
     --env fde-oms-processing
   ```

3. Confirm `support-team` moves to `v2`.
4. In k9s `:pods`, watch old `v1` pods scale down after no pinned workflows remain.
5. Point to the manifest sunset settings:

   ```yaml
   sunset:
     scaledownDelay: 30s
     deleteDelay: 120s
   ```

### Phase 6: Tie Back To Exercise 01

Reinforce the distinction:

- Exercise 01 used manual Worker Deployment commands so participants could see the primitives.
- TWC performs those operations from Kubernetes rollout state.
- Auto-upgrade was not useful for the fulfillment handoff because each order must keep its chosen
  path.
- Auto-upgrade is useful here for `support-team` because the workflow is intentionally long-lived
  and not tied to a per-order fulfillment path.

## Commands To Plan Around

Use k9s as the primary live view:

```text
:ctx kind-temporal-oms
:ns temporal-oms-processing
:pods
:temporalworkerdeployments
```

Raw command equivalents are useful for scripts, fallback, or exact copy/paste proof:

```bash
kubectl get temporalworkerdeployments -A
kubectl describe temporalworkerdeployment <name> -n <namespace>
kubectl get pods -n <namespace> -w
```

```bash
temporal worker deployment describe \
  --deployment-name <deployment> \
  --namespace <temporal-namespace>
```

```bash
kubectl patch temporalworkerdeployment <name> \
  -n <namespace> \
  --type merge \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"worker","image":"...:v2"}]}}}}'
```

If an existing helper script is preferred, the demo can use that instead of a raw patch:

```bash
VERSION=v2 OVERLAY=local ./scripts/kind/deploy-processing-workers.sh
# or
VERSION=v2 OVERLAY=local ./scripts/k3d/deploy-processing-workers.sh
```

The final demo script should avoid requiring attendees to type these commands. This is
instructor-led, and the value is in observing the automation. k9s should be the main visual surface;
raw commands are fallback and validation aids.

## Success Criteria

- The audience can map each manual Exercise 01 Worker Deployment command to the corresponding TWC
  behavior.
- The demo shows at least one new Worker Deployment Version becoming available.
- The demo shows a ramp or promotion controlled by `TemporalWorkerDeployment` policy.
- The demo shows old executions/pods are not abruptly killed during rollout.
- The demo explains why `support-team` can be auto-upgraded while per-order fulfillment workflows
  stay pinned.
- The demo clearly separates TWC automation from application/business workflow logic.

## Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Kubernetes manifests are stale | Demo cannot run | Complete k8s/KinD topology update before scripting this demo |
| Rollout takes too long for live workshop | Timebox blown | Pre-stage images and keep traffic lightweight; use short pause/sunset durations in workshop overlay |
| Controller status is hard to read live | Audience misses the point | Use k9s as the primary view, with Temporal CLI describe and Temporal UI as supporting proof |
| k9s does not expose a friendly alias for `TemporalWorkerDeployment` | Demo friction | Use the k9s command prompt with `temporalworkerdeployments`, or fall back to `kubectl get temporalworkerdeployment ... -w` |
| Image build or KinD load fails | Demo blocked | Build/load images before workshop; use a scripted preflight |
| TWC behavior looks like magic | Weak learning transfer from Exercise 01 | Always narrate the mapping from manual commands to controller actions |
| Auto-upgrade seems to contradict Exercise 01 | Conceptual confusion | Explicitly contrast per-order fulfillment path preservation with long-running support workflow maintenance |

## Open Questions

- Should this demo keep using only `processing-workers`, as in `java/enablements/ENABLEMENT.md`,
  or add an `apps-workers` rollout after Exercise 01 is implemented?
- Should the final version run against local Temporal, Temporal Cloud, or support both overlays?
- Is `enablements-workers` local-only for this demo, or should the updated KinD topology deploy it?
- Should we keep ramp percentages short for workshop overlays, e.g. 50% then 100% with 10-second
  pauses?
- Do we want a rollback demonstration, or keep the first demo to forward rollout only?
- Which script owns image build/load/patch for the final KinD version?
- Does `temporal workflow update-options --versioning-override-behavior auto_upgrade` work against
  local dev server with the pinned Temporal CLI version, or is that part cloud-only for this demo?
