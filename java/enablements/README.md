# Enablements

## Worker Versioning Demo

Shows how to safely deploy a new version of a Workflow on a Worker that is actively under load.
The demo runs against the `processing` bounded context only. Continuous order traffic is generated
while a new worker version is rolled out — demonstrating zero disruption to in-flight workflows.

---

## Prerequisites

### 1. Temporal Worker Controller installed in KinD

```bash
helm install temporal-worker-controller \
  oci://docker.io/temporalio/temporal-worker-controller \
  --namespace temporal-worker-controller-system \
  --create-namespace
```

Verify CRDs are registered:
```bash
kubectl get crd | grep temporal.io
# Should show: temporalconnections.temporal.io
#              temporalworkerdeployments.temporal.io
```

### 2. Processing namespace and config exists

The namespace, configmaps, and secrets are deployed as part of the main k8s overlay:
```bash
kubectl apply -k k8s/overlays/local
```

### 3. Processing worker image built and loaded

Tag with an explicit version — the controller derives the Temporal build-id from the image tag, so
`:latest` would produce the same build-id on every deploy and the controller would not register a
new version.

```bash
cd java
mvn install -pl processing/processing-workers -am -DskipTests
docker build -t temporal-oms/processing-workers:v1 processing/processing-workers
kind load docker-image temporal-oms/processing-workers:v1
```

---

## Setup: Deploy the TemporalWorkerDeployment

Apply the versioned processing workers (TemporalConnection + TemporalWorkerDeployment):

```bash
kubectl apply -k k8s/processing-versioned/overlays/local
```

This creates a single `TemporalWorkerDeployment` resource named `processing-workers`. The controller
spins up pods and registers this version with Temporal.

Verify:
```bash
kubectl get temporalworkerdeployments -n temporal-oms-processing
kubectl get pods -n temporal-oms-processing -l app=processing-workers
```

---

## Step 1: Start the Enablement Workflow

Start the `enablements-workers` locally (or in k8s) to register the `WorkerVersionEnablement` workflow.

Then start the workflow via the Temporal UI or CLI:

```bash
temporal workflow start \
  --type WorkerVersionEnablement \
  --task-queue enablements \
  --workflow-id demo-001 \
  --input '{
    "enablementId": "demo-001",
    "submitRatePerMin": 20,
    "orderCount": 1000
  }' \
  --input-meta "encoding=json/protobuf"
```

This workflow continuously submits orders to the `processing` task queue at `submitRatePerMin` orders/minute.

Verify orders are flowing:
```bash
temporal workflow query --workflow-id demo-001 --query-type getState
```

---

## Step 2: Build and Load the v2 Worker Image

Make your code change to the processing worker, then build and load the v2 image:

```bash
cd java
mvn install -pl processing/processing-workers -am -DskipTests
docker build -t temporal-oms/processing-workers:v2 processing/processing-workers
kind load docker-image temporal-oms/processing-workers:v2
```

---

## Step 3: Deploy v2 Directly via kubectl

Update the `TemporalWorkerDeployment` image. The controller detects the change, starts new pods with
the v2 image, registers the new build-id with Temporal, and shifts new workflow executions to v2.

```bash
kubectl patch temporalworkerdeployment processing-workers \
  -n temporal-oms-processing \
  --type='merge' \
  -p='{"spec": {"template": {"spec": {"containers": [{"name": "worker", "image": "temporal-oms/processing-workers:v2"}]}}}}'
```

Alternatively, update `k8s/processing-versioned/temporal-worker-deployment.yaml` with the new image
tag and re-apply:

```bash
kubectl apply -k k8s/processing-versioned/overlays/local
```

Watch the rollout:
```bash
kubectl get temporalworkerdeployments -n temporal-oms-processing -w
kubectl get pods -n temporal-oms-processing -l app=processing-workers -w
```

---

## Step 4: Observe the Transition

**In the Temporal UI / CLI**, observe that:
- Existing in-flight `Order` workflow executions complete on the **v1** worker (pinned by `PINNED` versioning behavior)
- New `Order` workflow executions are routed to the **v2** worker

**In kubectl**, both pod sets coexist during the transition:
```bash
kubectl get pods -n temporal-oms-processing -l app=processing-workers
# Old v1 pods drain, new v2 pods serve new workflows
```

Once all in-flight v1 workflows complete, the controller scales down v1 pods (after `scaledownDelay: 5m`).

---

## Key Configuration

| File | Purpose |
|------|---------|
| `k8s/processing-versioned/temporal-worker-deployment.yaml` | The `TemporalWorkerDeployment` CRD — update image here to deploy a new version |
| `k8s/processing-versioned/temporal-connection-local.yaml` | TemporalConnection for local KinD |
| `k8s/processing-versioned/temporal-connection-cloud.yaml` | TemporalConnection for Temporal Cloud |
| `java/processing/processing-core/src/main/resources/acme.processing.yaml` | Worker versioning config (`deployment-name: processing`, `build-id: ${TEMPORAL_WORKER_BUILD_ID:1.0.0}`) |

---

## Without Worker Versioning (for comparison)

The standard `deployment-workers.yaml` (classic `Deployment`) remains intact for running the processing
workers **without** versioning enabled. To compare, comment out `deployment-properties` in
`acme.processing.yaml` and deploy via the standard overlay:

```bash
kubectl apply -k k8s/overlays/local
```

This deploys `processing-workers` as a regular Deployment with no version-aware routing.
