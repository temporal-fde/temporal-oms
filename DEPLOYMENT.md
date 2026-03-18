# Temporal OMS - Deployment Guide

This guide covers deploying the Temporal OMS application to **KinD (Kubernetes in Docker)** or **running locally** without Kubernetes.

## Quick Start

### Option 1: Deploy to KinD with Cloud Temporal

```bash
# Ensure Temporal Cloud credentials are set up (see below)
OVERLAY=cloud ./scripts/demo-up.sh

# Check status
./scripts/status.sh

# Port-forward API access (in another terminal)
./scripts/tunnel.sh

# Test the API
curl http://localhost:8080/api/v1/commerce-app/clothing

# Tear down
./scripts/demo-down.sh
```

### Option 2: Deploy to KinD with Local Temporal

```bash
# Start your local Temporal server first (on port 7233)
temporal server start-dev &

# Deploy with local overlay
OVERLAY=local ./scripts/demo-up.sh

# Check status
./scripts/status.sh

# Port-forward API access
./scripts/tunnel.sh

# Tear down
./scripts/demo-down.sh
```

### Option 3: Run Everything Locally (No Kubernetes)

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

# Install versions from .tool-versions
asdf install

# Or install manually
brew install java maven nodejs kind kubectl
```

### System Resources

- **Minikube alternative**: Using KinD requires Docker
- **Memory**: 4GB minimum (8GB recommended)
- **Disk**: 5GB free space

---

## Setup Instructions

### 1. Temporal Cloud API Key Setup

If deploying to **Temporal Cloud** (OVERLAY=cloud):

#### Step 1a: Get Your API Key

1. Log in to [Temporal Cloud Console](https://cloud.temporal.io)
2. Navigate to **Settings → API Keys**
3. Create or copy your API key (JWT format)
4. Note your Namespace and Account ID

#### Step 1b: Configure Temporal CLI

```bash
# Get your cloud environment configuration
temporal env get --env your-env-name

# This shows:
# - address: us-east-1.aws.api.temporal.io:7233 (or your region)
# - namespace: your-namespace.account-id
# - api-key: eyJhbGc... (JWT token)
```

#### Step 1c: Store API Key in Secret Template

Create/update `k8s/overlays/cloud/secrets/temporal-apps-api-key.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: temporal-apps-api-key
  namespace: temporal-oms-apps
type: Opaque
stringData:
  temporal-secret.yaml: |
    spring.temporal.connection.api-key: "eyJhbGc..."
```

Create/update `k8s/overlays/cloud/secrets/temporal-processing-api-key.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: temporal-processing-api-key
  namespace: temporal-oms-processing
type: Opaque
stringData:
  temporal-secret.yaml: |
    spring.temporal.connection.api-key: "eyJhbGc..."
```

**Important:** These files contain secrets and should NOT be committed to git. They're already in `.gitignore`.

#### Step 1d: Verify Cloud Configuration

```bash
# Test connection to Temporal Cloud from your machine
temporal workflow list --env your-env-name

# This should show your workflows (even if empty)
```

### 2. Local Temporal Setup (Optional)

If deploying to **local Temporal** (OVERLAY=local):

```bash
# Install Temporal CLI (if not already installed)
brew install temporal

# Start local Temporal server (in background or separate terminal)
temporal server start-dev

# Verify it's running
temporal workflow list

# Note: Runs on localhost:7233 by default
```

No additional configuration needed for local overlay - it's configured in `k8s/overlays/local/configmap/`.

### 3. Build and Deploy to KinD

#### Step 3a: Deploy Complete Environment

```bash
# For Temporal Cloud deployment
OVERLAY=cloud ./scripts/demo-up.sh

# OR for Local Temporal deployment
OVERLAY=local ./scripts/demo-up.sh
```

This script:
1. Creates KinD cluster (if not exists)
2. Builds Docker images
3. Loads images into KinD
4. Creates namespaces
5. Installs Traefik ingress
6. Deploys applications with ConfigMaps and Secrets

#### Step 3b: Verify Deployment

```bash
# Check all pods are running
./scripts/status.sh

# Should show:
# - apps-api: Running (2 replicas)
# - apps-worker: Running (2 replicas)
# - processing-worker: Running (2 replicas)
# - KinD cluster: temporal-oms (running)
```

#### Step 3c: Access the API

```bash
# In one terminal, port-forward
./scripts/tunnel.sh

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

- **Temporal Target**: `us-east-1.aws.api.temporal.io:7233` (or your region)
- **API Key**: Required (from Temporal Cloud)
- **TLS**: Enabled
- **Namespace**: Your Temporal Cloud namespace (e.g., `fde-oms-apps.account-id`)

**Config Files:**
- `k8s/overlays/cloud/configmap/temporal-apps.yaml`
- `k8s/overlays/cloud/configmap/temporal-processing.yaml`
- `k8s/overlays/cloud/secrets/temporal-apps-api-key.yaml` (contains JWT)
- `k8s/overlays/cloud/secrets/temporal-processing-api-key.yaml` (contains JWT)

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
OVERLAY=cloud ./scripts/app-deploy.sh

# 3. Check status
./scripts/status.sh

# 4. View logs
export KUBECONFIG=/tmp/kind-config.yaml
kubectl logs -n temporal-oms-apps -l app=apps-worker --tail=50
```

### Debugging

```bash
# Enable KUBECONFIG for all commands
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
./scripts/status.sh
```

### Redeploy Applications (keep cluster running)

```bash
OVERLAY=cloud ./scripts/app-deploy.sh
```

### Full Teardown and Restart

```bash
./scripts/demo-down.sh
sleep 5
OVERLAY=cloud ./scripts/demo-up.sh
```

### View Logs

```bash
export KUBECONFIG=/tmp/kind-config.yaml

# Apps API
kubectl logs -n temporal-oms-apps -l app=apps-api --tail=50

# All workers
kubectl logs -n temporal-oms-apps -l app=apps-worker --tail=50
kubectl logs -n temporal-oms-processing -l app=processing-worker --tail=50
```

### Port Forward (for API access)

```bash
./scripts/tunnel.sh
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

### Images not loading

```bash
# Ensure KUBECONFIG is set for your shell
export KUBECONFIG=/tmp/kind-config.yaml

# Check images in KinD
kind load docker-image temporal-oms/apps-api:latest --name temporal-oms

# Or just redeploy
OVERLAY=cloud ./scripts/app-deploy.sh
```

### Docker context issues

```bash
# Reset to default Docker context
docker context use default

# Verify Docker is working
docker ps

# Then deploy
OVERLAY=cloud ./scripts/demo-up.sh
```

---

## Architecture Overview

### Deployment Structure

```
KinD Cluster (temporal-oms)
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
| `demo-up.sh` | Full environment setup | `OVERLAY=cloud ./scripts/demo-up.sh` |
| `demo-down.sh` | Complete teardown | `./scripts/demo-down.sh` |
| `app-deploy.sh` | Rebuild and redeploy apps only | `OVERLAY=cloud ./scripts/app-deploy.sh` |
| `status.sh` | Check deployment status | `./scripts/status.sh` |
| `tunnel.sh` | Port-forward API access | `./scripts/tunnel.sh` |
| `infra-up.sh` | Create KinD cluster only | `./scripts/infra-up.sh` |
| `infra-down.sh` | Delete KinD cluster | `./scripts/infra-down.sh` |

---

## Next Steps

1. **First time setup**: Follow the "Quick Start" section above
2. **Make changes**: Edit Java code and run `./scripts/app-deploy.sh`
3. **Test workflows**: Submit orders via API or scenarios
4. **Monitor**: Check logs with `kubectl logs` commands
5. **Deploy to production**: Adapt the deployment for your cloud provider (GKE, EKS, AKS, etc.)

---

## References

- [KinD Documentation](https://kind.sigs.k8s.io/)
- [Temporal Cloud API Keys](https://docs.temporal.io/cloud/api-keys)
- [Spring Boot Configuration](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.external-config)
- [Kubectl Documentation](https://kubernetes.io/docs/reference/kubectl/)
