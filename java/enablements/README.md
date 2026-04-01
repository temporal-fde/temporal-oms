# Enablements

## Worker Versioning Demo

Shows how to safely deploy a new version of a Workflow on a Worker that is actively under load.
The demo runs against the `processing` bounded context only. Continuous order traffic is generated
while a new worker version is rolled out — demonstrating zero disruption to in-flight workflows.

---

## Prerequisites

**Level 3 must be fully running** before starting this demo. That means:

- KinD cluster up (`kind get clusters` shows `temporal-oms`)
- All pods healthy (`./scripts/status.sh`)
- `processing-workers` pod running and registered with Temporal Cloud
- Load flowing into the `processing` namespace

Verify the `TemporalWorkerDeployment` is healthy:

```bash
export KUBECONFIG=/tmp/kind-config.yaml
kubectl get temporalworkerdeployment processing-workers -n temporal-oms-processing
# TemporalConnectionHealthy should be True
```

---

## Key Concepts

**How versioning works:** The Temporal Worker Controller manages a single `TemporalWorkerDeployment`
resource. When you change the `image` tag, the controller:

1. Computes a new build-id from the image tag + a hash of the pod template spec
2. Registers the new build-id with Temporal
3. Starts pods with the new image
4. Waits for pollers to appear on the new build-id
5. Calls `set-current-version` — this is the moment Temporal begins routing new tasks to the new version
6. Progressively ramps traffic per the rollout strategy
7. Old pods drain — in-flight workflows complete on the version they started on

**Why explicit version tags matter:** The build-id is derived from the image tag. Using `:latest`
would produce the same build-id on every deploy and Temporal would not see a new version.
Always use `:v1`, `:v2`, etc.

> **Controller vs. raw CLI — why tasks only flow after `set-current-version`**
>
> When a worker runs with `deployment-properties` configured, Temporal tracks it as part of a Deployment. The server will not route tasks to any version of that deployment until one version is explicitly designated "current" via `set-current-version`. Workers poll successfully and show as connected — but the task queue appears empty.
>
> The Temporal Worker Controller handles this automatically. It watches the Temporal API for pollers to register against a new build-id, and once they do, it calls `set-current-version` on your behalf. This is why deploying a new image in Kubernetes just works.
>
> Without the controller (e.g. running workers locally for Level 1 development), `set-current-version` must be called manually. The `scripts/setup-temporal-namespaces.sh` script does this with `--allow-no-pollers` so it can run before workers start. If you ever see orders submitted but never progressing, a missing current version is the first thing to check:
> ```bash
> temporal worker deployment describe --deployment-name processing --namespace processing
> ```

**Rollout strategy (configured in `k8s/processing-versioned/base/temporal-worker-deployment.yaml`):**
```
50% new traffic → 30s pause → 90% new traffic → 30s pause → 100% complete
```

---

## Step 1: Generate Load

Start the load generator to submit continuous orders into the `processing` task queue.
This is what you will observe draining from v1 and routing to v2.

Start the `enablements-workers` (locally or in k8s) to register the `WorkerVersionEnablement` workflow,
then start it via the Temporal CLI or UI:

```bash
temporal workflow start \
  --type WorkerVersionEnablement \
  --task-queue enablements \
  --workflow-id demo-worker-versioning \
  --input '{"enablementId":"demo-worker-versioning","submitRatePerMin":20,"orderCount":1000}'
```

Verify orders are flowing:

```bash
temporal workflow list --namespace processing.<your-account-id>
```

---

## Step 2: Deploy v2

Use the version bump script — it builds, loads, and patches in one step:

```bash
VERSION=v2 OVERLAY=cloud ./scripts/deploy-processing-workers.sh
```

The script will:
1. Build `temporal-oms/processing-workers:v2` from source
2. Load the image into KinD (`kind load docker-image ... --name temporal-oms`)
3. Patch the `TemporalWorkerDeployment` image — this is the version trigger

Watch the rollout begin immediately:

```bash
export KUBECONFIG=/tmp/kind-config.yaml
kubectl get temporalworkerdeployment processing-workers -n temporal-oms-processing -w
```

---

## Step 3: Observe the Transition

**In kubectl** — both pod sets coexist during the transition:

```bash
kubectl get pods -n temporal-oms-processing -w
# You will see v1 pods alongside v2 pods (named with different build-id suffixes)
# v1 pods drain as their workflows complete; v2 pods take new work
```

**In k9s** — watch the `temporal-oms-processing` namespace for pod lifecycle changes.

**In the Temporal UI or CLI:**

```bash
temporal workflow list --namespace processing.<your-account-id>
# New Order workflows are pinned to v2 (new build-id)
# In-flight Order workflows on v1 continue until they complete naturally
```

Once all v1 workflows complete, the controller scales down v1 pods (after `scaledownDelay: 30s`).

---

## Key Files

| File | Purpose |
|------|---------|
| `k8s/processing-versioned/base/temporal-worker-deployment.yaml` | The `TemporalWorkerDeployment` CRD — rollout strategy, sunset config, pod template |
| `k8s/processing-versioned/overlays/cloud/temporal-connection.yaml` | Controller's connection to Temporal Cloud (uses automations API key) |
| `k8s/processing-versioned/overlays/cloud/temporal-namespace-patch.yaml` | Patches `temporalNamespace` to the fully-qualified cloud namespace |
| `scripts/deploy-processing-workers.sh` | Version bump script: build → load → patch |
| `java/processing/processing-core/src/main/resources/acme.processing.yaml` | Worker versioning config — reads `TEMPORAL_WORKER_BUILD_ID` and `TEMPORAL_DEPLOYMENT_NAME` env vars injected by the controller |

---

## Without Worker Versioning (for comparison)

The standard `k8s/base/processing/deployment-workers.yaml` (classic `Deployment`) remains intact.
To compare behavior without versioning, comment out `deployment-properties` in
`acme.processing.yaml` and deploy via the standard overlay without the
`processing-versioned` kustomize overlay.

This deploys `processing-workers` as a regular Deployment with no version-aware routing —
all workers immediately pick up the new code on restart, potentially disrupting in-flight workflows.
