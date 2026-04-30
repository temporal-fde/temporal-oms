# ACME Order Management System (OMS)

A Java-based Order Management System demonstrating Temporal workflow orchestration across bounded contexts — apps and processing — connected via Nexus.

> **Business requirements and architecture scope:** [PROJECT_REQUIREMENTS_DOCUMENT.md](PROJECT_REQUIREMENTS_DOCUMENT.md)

---

## Steps to Temporal Maturity

Start at Level 1 and work up. Each level builds on the previous.

| Level | Description | What you need |
|-------|-------------|---------------|
| **1** | Run locally — no Kubernetes | Java, Maven, Docker, Temporal CLI |
| **2** | KinD or k3d cluster with local Temporal | Level 1 + KinD or k3d, Helm, kubectl, k9s |
| **3** | KinD or k3d cluster connected to Temporal Cloud | Level 2 + Temporal Cloud account, namespaces, service accounts, API keys |
| **4** | Worker Versioning Enablement (live demo) | Level 3 running + load generation |

---

## Tool Prerequisites

All tool versions are pinned in [`.tool-versions`](.tool-versions). Install with [asdf](https://asdf-vm.com/):

```bash
asdf install
```

| Tool | Purpose |
|------|---------|
| `java` (OpenJDK 21) | Build and run Java services |
| `maven` 3.9+ | Java build tool |
| `nodejs` | Web tooling |
| `kind` | Local Kubernetes cluster |
| `k3d` | Lightweight local Kubernetes cluster |
| `k9s` | Kubernetes cluster UI |
| `temporal` CLI | Namespace, workflow, and Nexus management |
| `kubectl` | Kubernetes control plane |
| `helm` | Install Temporal Worker Controller |
| `yq` | YAML parsing used in deploy scripts |
| `buf` | Protocol Buffer code generation |
| `docker` | Container runtime (Docker Desktop) |
| `xh` | HTTP client for demo scenarios (or use `curl`) |

---

## Level 1 — Run Locally (No Kubernetes)

Fastest path to a working system. All services run as local JVM processes against a local Temporal server.

> **Important:** The workers use Worker Versioning (Temporal Deployments). Without the Temporal Worker Controller in the environment, you must call `set-current-version` manually before tasks will be dispatched — `scripts/setup-temporal-namespaces.sh` handles this. See [GETTING_STARTED.md](GETTING_STARTED.md) for the full explanation.

→ **[GETTING_STARTED.md](GETTING_STARTED.md)** — local setup, demo scenarios, troubleshooting
→ **[DEVELOPMENT.md](DEVELOPMENT.md)** — protobuf changes, workflow modifications, debugging, testing

---

## Level 2 — Kubernetes Deployment with Local Temporal

Full stack in a local Kubernetes cluster. Choose one runner and use that directory consistently.

```bash
./scripts/kind/infra-up.sh
./scripts/kind/app-deploy.sh

# or
./scripts/k3d/infra-up.sh
./scripts/k3d/app-deploy.sh
```

→ **[DEPLOYMENT.md](DEPLOYMENT.md)** for full prerequisites, verification, and troubleshooting.

---

## Level 3 — Kubernetes + Temporal Cloud

### Step 1: Set Up Temporal Cloud (Manual, One-Time)

#### a) Create Two Namespaces

In [Temporal Cloud](https://cloud.temporal.io) → Namespaces, create:

| Namespace | Purpose |
|-----------|---------|
| `apps` | Order orchestration and data collection |
| `processing` | Order validation, enrichment, and fulfillment |

Your fully-qualified namespace names will be `<namespace-name>.<account-id>`.

#### b) Create Service Accounts and API Keys

In Temporal Cloud → Settings → Identities, create three service accounts:

| Service Account | Role | Used by |
|----------------|------|---------|
| `acme-apps-service-account` | Developer | `apps` Spring workers |
| `acme-processing-service-account` | Developer | `processing` Spring workers |
| `acme-automations-service-account` | Developer or Admin | Temporal Worker Controller |

> **Why a separate automations account?** The Worker Controller calls Temporal's Worker Deployment API to register build-ids and manage traffic ramp. This requires broader permissions than a standard worker connection. Keep it separate so it can be rotated independently.

For each service account, generate an API key. Copy the values — they are shown only once.

#### c) Create Nexus Endpoints

In Temporal Cloud → Nexus, create:

| Endpoint name | Target namespace | Target task queue |
|--------------|----------------|-----------------|
| `oms-processing-v1` | `processing` | `processing` |
| `oms-apps-v1` | `apps` | `apps` |

Or use the script (requires your cloud address):

```bash
TEMPORAL_ADDRESS=<your-region>.aws.api.temporal.io:7233 \
  ./scripts/setup-temporal-namespaces.sh
```

#### d) Note Your Region Endpoint

Find your region in Temporal Cloud → Namespaces → (select namespace) → Connection:

```
<your-region>.aws.api.temporal.io:7233
```

### Step 2: Create Local Secret Files

Copy the templates and fill in your API keys. These files are gitignored — never commit them.

```bash
cp config/acme.apps.secret.template.yaml        config/acme.apps.secret.yaml
cp config/acme.processing.secret.template.yaml  config/acme.processing.secret.yaml
cp config/acme.automations.secret.template.yaml config/acme.automations.secret.yaml
```

Edit each file and replace `<TEMPORAL CLOUD API KEY>` with the corresponding service account's API key.

### Step 3: Update Cloud ConfigMaps

In `k8s/overlays/cloud/configmap/`, update the Temporal namespace and endpoint values to match your account. Look for `<your-account-id>` and `<your-region>` placeholders.

### Step 4: Deploy

```bash
OVERLAY=cloud ./scripts/kind/infra-up.sh    # Creates KinD cluster, installs controller, applies secrets
OVERLAY=cloud ./scripts/kind/app-deploy.sh  # Builds images, deploys apps

# or
OVERLAY=cloud ./scripts/k3d/infra-up.sh
OVERLAY=cloud ./scripts/k3d/app-deploy.sh
```

→ **[CLOUD.md](CLOUD.md)** for verification steps and troubleshooting.

---

## Level 4 — Worker Versioning Enablement

Demonstrates zero-downtime worker version rollouts against a live order stream. The Temporal Worker Controller progressively shifts traffic from the old worker version to the new one while in-flight workflows drain cleanly.

**Requires:** Level 3 running with load flowing.

→ **[java/enablements/README.md](java/enablements/README.md)**

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/kind/infra-up.sh` | Create KinD cluster, install Temporal Worker Controller, apply cloud secrets |
| `scripts/k3d/infra-up.sh` | Create k3d cluster, install Temporal Worker Controller, apply cloud secrets |
| `scripts/kind/app-deploy.sh` | Build Docker images, load into KinD, deploy all applications |
| `scripts/k3d/app-deploy.sh` | Build Docker images, import into k3d, deploy all applications |
| `scripts/kind/deploy-processing-workers.sh` | Bump processing workers in KinD to a new version (`VERSION=v2`) |
| `scripts/k3d/deploy-processing-workers.sh` | Bump processing workers in k3d to a new version (`VERSION=v2`) |
| `scripts/kind/demo-up.sh` | Run KinD infra-up + app-deploy in one step |
| `scripts/k3d/demo-up.sh` | Run k3d infra-up + app-deploy in one step |
| `scripts/kind/infra-down.sh` | Tear down the KinD cluster |
| `scripts/k3d/infra-down.sh` | Tear down the k3d cluster |
| `scripts/kind/status.sh` | Show pod status across namespaces in KinD |
| `scripts/k3d/status.sh` | Show pod status across namespaces in k3d |
| `scripts/setup-temporal-namespaces.sh` | Create Temporal namespaces and Nexus endpoints |
| `scripts/kind/tunnel.sh` | Port-forward APIs for local access through KinD |
| `scripts/k3d/tunnel.sh` | Port-forward APIs for local access through k3d |

→ **[scripts/README.md](scripts/README.md)** for detailed usage.
