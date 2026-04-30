# Temporal OMS - Deployment Guide

This guide covers deploying the Temporal OMS application to **KinD (Kubernetes in Docker)**,
**k3d**, or **running locally** without Kubernetes.

The Kubernetes scripts are split by cluster runtime:

- `scripts/kind/*` - KinD implementation.
- `scripts/k3d/*` - k3d implementation.
- `scripts/*.sh` - backwards-compatible KinD aliases.

## Quick Start

### Option 1: Deploy to KinD with Cloud Temporal

```bash
# Ensure Temporal Cloud credentials are set up (see below)
OVERLAY=cloud ./scripts/kind/demo-up.sh

# Check status
./scripts/kind/status.sh

# Port-forward API access (in another terminal)
./scripts/kind/tunnel.sh

# Test the API
curl http://localhost:8080/api/v1/commerce-app/clothing

# Tear down
./scripts/kind/demo-down.sh
```

### Option 2: Deploy to k3d with Cloud Temporal

```bash
# Ensure Temporal Cloud credentials are set up (see below)
OVERLAY=cloud ./scripts/k3d/demo-up.sh

# Check status
./scripts/k3d/status.sh

# Port-forward API access
./scripts/k3d/tunnel.sh

# Tear down
./scripts/k3d/demo-down.sh
```

### Option 3: Deploy to k3d with Local Temporal

```bash
# Start your local Temporal server first and bind it to all interfaces for k3d pods
temporal server start-dev --ip 0.0.0.0 --ui-ip 0.0.0.0

# Deploy with local overlay
OVERLAY=local ./scripts/k3d/demo-up.sh

# Check status
./scripts/k3d/status.sh

# Port-forward API access
./scripts/k3d/tunnel.sh

# Tear down
./scripts/k3d/demo-down.sh
```

### Option 4: Deploy to KinD with Local Temporal

```bash
# Start your local Temporal server first (on port 7233)
temporal server start-dev &

# Deploy with local overlay
OVERLAY=local ./scripts/kind/demo-up.sh

# Check status
./scripts/kind/status.sh

# Port-forward API access
./scripts/kind/tunnel.sh

# Tear down
./scripts/kind/demo-down.sh
```

### Option 5: Run Everything Locally (No Kubernetes)

```bash
# Start Temporal server
temporal server start-dev &

# In another terminal, build and run the apps
cd java/apps
mvn spring-boot:run

# Test
curl http://localhost:8080/api/v1/commerce-app/clothing
```

---

## Prerequisites

### Required Tools

Install using asdf (recommended) or your preferred package manager:

```bash
# Using asdf
asdf plugin add java https://github.com/halcyon/asdf-java.git
asdf plugin add maven https://github.com/asdf-community/asdf-maven.git
asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git
asdf plugin add kind https://github.com/johnlayton/asdf-kind.git
asdf plugin add k3d https://github.com/spencergilbert/asdf-k3d.git

# Install versions from .tool-versions
asdf install

# Or install manually
brew install java maven nodejs kind k3d kubectl
```

### System Resources

- **Minikube alternative**: Using KinD or k3d requires Docker
- **Memory**: 4GB minimum (8GB recommended)
- **Disk**: 5GB free space

---

## Setup Instructions

### 1. Temporal Cloud API Key Setup

If deploying to **Temporal Cloud** (OVERLAY=cloud), API keys are managed through gitignored local config files. They are never written to committed files.

See **[README.md — Level 3](README.md)** for the full one-time Temporal Cloud setup (namespaces, service accounts, API keys, Nexus endpoints).

Once you have your API keys, copy the templates and fill them in:

```bash
cp config/acme.apps.secret.template.yaml        config/acme.apps.secret.yaml
cp config/acme.processing.secret.template.yaml  config/acme.processing.secret.yaml
cp config/acme.automations.secret.template.yaml config/acme.automations.secret.yaml
```

`scripts/kind/infra-up.sh` and `scripts/k3d/infra-up.sh` read these files at deploy time and create
the Kubernetes secrets imperatively. Nothing with a real key ever touches a committed file.

See **[CLOUD.md](CLOUD.md)** for the full secret-to-Kubernetes mapping and troubleshooting.

### 2. Local Temporal Setup (OVERLAY=local)

```bash
# Install Temporal CLI (if not already installed)
brew install temporal

# Start local Temporal server (in background or separate terminal).
# Binding to 0.0.0.0 lets KinD/k3d pods reach it through host.docker.internal.
temporal server start-dev --ip 0.0.0.0 --ui-ip 0.0.0.0

# Verify it's running
temporal workflow list
# Note: Listens on port 7233 by default
```

> **Worker Versioning and `set-current-version`**
>
> When running with `OVERLAY=local`, the apps and processing workers start with Worker Versioning enabled. The **Temporal Worker Controller** handles version promotion automatically: it watches for pollers to appear on a new build-id, then calls `set-current-version` itself. You never need to run it manually when the controller is present.
>
> This is why tasks route correctly after deploy without any extra steps — the controller is the bridge between a new image landing in Kubernetes and Temporal knowing to route work to it.
>
> If workers are running **without the Temporal Worker Controller in the environment** (e.g. Level 1, running directly on your machine), you must call `set-current-version` yourself. This is what `scripts/setup-temporal-namespaces.sh` does. If you skip it, workers will connect and poll but the server will dispatch no tasks — workflows stall silently. See [GETTING_STARTED.md](GETTING_STARTED.md) for details.

### 3. Build and Deploy to Kubernetes

#### Step 3a: Deploy Complete Environment

```bash
# For Temporal Cloud deployment
OVERLAY=cloud ./scripts/kind/demo-up.sh
OVERLAY=cloud ./scripts/k3d/demo-up.sh

# OR for Local Temporal deployment
OVERLAY=local ./scripts/kind/demo-up.sh
OVERLAY=local ./scripts/k3d/demo-up.sh
```

This script:
1. Creates the selected cluster (if not exists)
2. Builds Docker images
3. Loads or imports images into the selected cluster
4. Creates namespaces
5. Installs Traefik ingress
6. Deploys applications with ConfigMaps and Secrets

#### Step 3b: Verify Deployment

```bash
# Check all pods are running
./scripts/kind/status.sh
# or
./scripts/k3d/status.sh

# Should show:
# - apps-api: Running (2 replicas)
# - apps-worker: Running (2 replicas)
# - processing-worker: Running (2 replicas)
# - selected cluster: temporal-oms (running)
```

#### Step 3c: Access the API

```bash
# In one terminal, port-forward
./scripts/kind/tunnel.sh
# or
./scripts/k3d/tunnel.sh

# In another terminal, test the API
curl http://localhost:8080/api/v1/commerce-app/clothing

# Or visit Swagger UI
open http://localhost:8080/api/docs
```

---

## Configuration Details

### Environment Overlays

#### Local Overlay (OVERLAY=local)

- **Temporal Target**: `host.docker.internal:7233`
- **API Key**: Not required (empty)
- **TLS**: Disabled
- **Use Case**: Local development with localhost Temporal

**Config Files:**
- `k8s/overlays/local/configmap/temporal-apps.yaml`
- `k8s/overlays/local/configmap/temporal-processing.yaml`
- `k8s/overlays/local/secrets/temporal-apps-api-key.yaml` (empty stub)

#### Cloud Overlay (OVERLAY=cloud)

- **Temporal Target**: Your region endpoint (e.g. `us-east-1.aws.api.temporal.io:7233`)
- **API Key**: Required — sourced from gitignored `config/*.secret.yaml` files at deploy time
- **TLS**: Enabled
- **Namespace**: Your fully-qualified Temporal Cloud namespace (e.g., `apps.<account-id>`)

**Config Files:**
- `k8s/overlays/cloud/configmap/` — Temporal address, namespace, TLS settings (committed, no secrets)
- `config/acme.apps.secret.yaml` — Apps worker API key (gitignored, created from template)
- `config/acme.processing.secret.yaml` — Processing worker API key (gitignored, created from template)
- `config/acme.automations.secret.yaml` — Temporal Worker Controller API key (gitignored, created from template)

Kubernetes secrets are created imperatively by `scripts/kind/infra-up.sh` or
`scripts/k3d/infra-up.sh` from those files. No secrets are committed.

### Spring Boot Configuration

The applications use Spring profiles to load configuration:

1. **application.yaml** (classpath): Base configuration
2. **application-k8s.yaml** (classpath): Kubernetes-specific imports
3. **Mounted ConfigMap**: `temporal-config.yaml` at `/etc/config/temporal/`
4. **Mounted Secret**: `temporal-secret.yaml` at `/etc/config/temporal-secret/`

Environment variable:
```bash
SPRING_PROFILES_ACTIVE=k8s  # Activates k8s profile
```

This ensures configuration files are only imported when running in Kubernetes, not during local development.

---

## Development Workflow

### Making Code Changes

```bash
# 1. Edit code
vim java/apps/src/main/java/com/acme/apps/...

# 2. Redeploy (rebuilds images and restarts pods)
OVERLAY=cloud ./scripts/kind/app-deploy.sh
# or
OVERLAY=local ./scripts/k3d/app-deploy.sh

# 3. Check status
./scripts/kind/status.sh
# or
./scripts/k3d/status.sh

# 4. View logs
export KUBECONFIG=/tmp/kind-config.yaml
kubectl logs -n temporal-oms-apps -l app=apps-worker --tail=50
```

### Debugging

```bash
# Enable KUBECONFIG for all commands. Use /tmp/k3d-config.yaml for k3d.
export KUBECONFIG=/tmp/kind-config.yaml

# Check all pods and their status
kubectl get pods -A

# View logs from all pods
export KUBECONFIG=/tmp/kind-config.yaml
for pod in $(kubectl get pods -n temporal-oms-apps -o name); do
  echo "=== $pod ===" && \
  kubectl logs -n temporal-oms-apps $pod --tail=30
done

# Shell into a pod
kubectl exec -it -n temporal-oms-apps <pod-name> -- /bin/bash

# Check mounted secrets
kubectl exec -n temporal-oms-apps <pod-name> -- cat /etc/config/temporal-secret/temporal-secret.yaml
```

---

## Running Locally (Without Kubernetes)

For local development without Kubernetes:

```bash
# Terminal 1: Start Temporal
temporal server start-dev

# Terminal 2: Start apps-api
cd java/apps/apps-api
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.profiles.active=local"

# Terminal 3: Start apps-workers
cd java/apps/apps-workers
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.profiles.active=local"

# Terminal 4: Start processing-workers
cd java/processing/processing-workers
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.profiles.active=local"

# Terminal 5: Test the API
curl http://localhost:8080/api/v1/commerce-app/clothing
```

**Notes:**
- Each service runs on its configured port (apps-api: 8080, workers: internal only)
- No configuration mounting needed - classpath configuration is used
- Logs appear in the terminal where you started each service

---

## Common Commands

### Check Cluster Status

```bash
./scripts/kind/status.sh
./scripts/k3d/status.sh
```

### Redeploy Applications (keep cluster running)

```bash
OVERLAY=cloud ./scripts/kind/app-deploy.sh
OVERLAY=local ./scripts/k3d/app-deploy.sh
```

### Full Teardown and Restart

```bash
./scripts/kind/demo-down.sh
sleep 5
OVERLAY=cloud ./scripts/kind/demo-up.sh

./scripts/k3d/demo-down.sh
sleep 5
OVERLAY=local ./scripts/k3d/demo-up.sh
```

### View Logs

```bash
export KUBECONFIG=/tmp/kind-config.yaml
# or
export KUBECONFIG=/tmp/k3d-config.yaml

# Apps API
kubectl logs -n temporal-oms-apps -l app=apps-api --tail=50

# All workers
kubectl logs -n temporal-oms-apps -l app=apps-worker --tail=50
kubectl logs -n temporal-oms-processing -l app=processing-worker --tail=50
```

### Port Forward (for API access)

```bash
./scripts/kind/tunnel.sh
./scripts/k3d/tunnel.sh
# Then access: http://localhost:8080/api/
```

---

## Troubleshooting

### "Connection refused" to Temporal

**For OVERLAY=cloud:**
1. Verify API key is correct in secret files
2. Check `spring.temporal.connection.tls.enabled: true` in ConfigMap
3. Verify namespace matches Temporal Cloud (e.g., `fde-oms-apps.account-id`)

**For OVERLAY=local:**
1. Ensure temporal server is running: `temporal workflow list`
2. Check pods can reach `host.docker.internal:7233`: `kubectl exec <pod> -- nc -zv host.docker.internal 7233`

### Pods in CrashLoopBackOff

```bash
# Check logs
kubectl logs -n temporal-oms-apps <pod-name>

# Check pod events
kubectl describe pod -n temporal-oms-apps <pod-name>

# Common issues:
# - Missing ConfigMap/Secret
# - TLS handshake failure (check api-key format)
# - Network connectivity (check target host/port)
```

### Images not loading or importing

```bash
# Ensure KUBECONFIG is set for your shell. Use /tmp/k3d-config.yaml for k3d.
export KUBECONFIG=/tmp/kind-config.yaml

# Check images in KinD
kind load docker-image temporal-oms/apps-api:latest --name temporal-oms

# Check images in k3d
k3d image import temporal-oms/apps-api:latest --cluster temporal-oms

# Or just redeploy
OVERLAY=cloud ./scripts/kind/app-deploy.sh
OVERLAY=local ./scripts/k3d/app-deploy.sh
```

### Docker context issues

```bash
# Reset to default Docker context
docker context use default

# Verify Docker is working
docker ps

# Then deploy
OVERLAY=cloud ./scripts/kind/demo-up.sh
OVERLAY=local ./scripts/k3d/demo-up.sh
```

---

## Architecture Overview

### Deployment Structure

```
KinD or k3d Cluster (temporal-oms)
├── temporal-oms-apps namespace
│   ├── apps-api (2 replicas) - REST API
│   └── apps-worker (2+ replicas) - Workflow workers
├── temporal-oms-processing namespace
│   └── processing-worker (2+ replicas) - Processing workers
└── traefik namespace
    └── Traefik Ingress Controller
```

### Configuration Flow

```
Application → Spring Boot Profile (k8s)
           ↓
        application-k8s.yaml (imports mounted files)
           ↓
        /etc/config/temporal/temporal-config.yaml (ConfigMap)
        /etc/config/temporal-secret/temporal-secret.yaml (Secret)
           ↓
        Temporal Client Configuration
           ↓
        Connect to Temporal (Cloud or Local)
```

---

## Scripts Reference

| Script | Purpose | Example |
|--------|---------|---------|
| `scripts/kind/demo-up.sh` | Full KinD environment setup | `OVERLAY=cloud ./scripts/kind/demo-up.sh` |
| `scripts/k3d/demo-up.sh` | Full k3d environment setup | `OVERLAY=local ./scripts/k3d/demo-up.sh` |
| `scripts/kind/app-deploy.sh` | Rebuild and redeploy apps to KinD | `OVERLAY=cloud ./scripts/kind/app-deploy.sh` |
| `scripts/k3d/app-deploy.sh` | Rebuild and redeploy apps to k3d | `OVERLAY=local ./scripts/k3d/app-deploy.sh` |
| `scripts/kind/status.sh` | Check KinD deployment status | `./scripts/kind/status.sh` |
| `scripts/k3d/status.sh` | Check k3d deployment status | `./scripts/k3d/status.sh` |
| `scripts/*.sh` | Backwards-compatible KinD aliases | `OVERLAY=cloud ./scripts/demo-up.sh` |

---

## Next Steps

1. **First time setup**: Follow the "Quick Start" section above
2. **Make changes**: Edit Java code and run `./scripts/kind/app-deploy.sh` or `./scripts/k3d/app-deploy.sh`
3. **Test workflows**: Submit orders via API or scenarios
4. **Monitor**: Check logs with `kubectl logs` commands
5. **Deploy to production**: Adapt the deployment for your cloud provider (GKE, EKS, AKS, etc.)

---

## References

- [KinD Documentation](https://kind.sigs.k8s.io/)
- [k3d Documentation](https://k3d.io/)
- [Temporal Cloud API Keys](https://docs.temporal.io/cloud/api-keys)
- [Spring Boot Configuration](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.external-config)
- [Kubectl Documentation](https://kubernetes.io/docs/reference/kubectl/)
