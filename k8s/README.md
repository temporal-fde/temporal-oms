# Kubernetes Deployment with Kustomize

This directory contains a Kustomize-based deployment structure that supports both local (Temporal server on localhost) and cloud (Temporal Cloud) environments, deployed to KinD (Kubernetes in Docker).

## Directory Structure

```
k8s/
├── base/                          # Base resources (Deployments, Services, Namespaces)
│   ├── namespaces/
│   ├── apps/
│   └── processing/
├── overlays/
│   ├── local/                     # Local Temporal configuration
│   │   ├── configmap/             # Temporal connection: host.docker.internal:7233
│   │   ├── secrets/               # Temporal API key stub for local
│   │   └── kustomization.yaml
│   └── cloud/                     # Temporal Cloud configuration
│       ├── configmap/             # Temporal connection: Temporal Cloud address
│       ├── secrets/               # Temporal API key from Temporal Cloud
│       └── kustomization.yaml
```

## Quick Start

For complete deployment instructions including API key setup, prerequisites, and troubleshooting, see [../DEPLOYMENT.md](../DEPLOYMENT.md).

### Deploy to Local Temporal (localhost:7233)

```bash
# 1. Start local Temporal server
temporal server start-dev &

# 2. Deploy to KinD
OVERLAY=local ./scripts/demo-up.sh

# 3. Verify
./scripts/status.sh
```

**Deployment details:**
- Kubernetes: KinD cluster named `temporal-oms`
- Namespaces: `temporal-oms-apps`, `temporal-oms-processing`
- Temporal namespaces: `apps`, `processing`
- Temporal connection: `host.docker.internal:7233` (reaches host's localhost)

### Deploy to Temporal Cloud

```bash
# 1. Configure API keys
# See DEPLOYMENT.md for detailed Temporal Cloud API key setup

# 2. Deploy to KinD
OVERLAY=cloud ./scripts/demo-up.sh

# 3. Verify
./scripts/status.sh
```

**Deployment details:**
- Kubernetes: KinD cluster named `temporal-oms`
- Namespaces: `temporal-oms-apps`, `temporal-oms-processing`
- Temporal connection: `us-east-1.aws.api.temporal.io:7233` (or your Temporal Cloud host)
- TLS: Enabled with API key authentication

## How Configuration Works

### Spring Boot merges three YAML sources (in order):

1. **Base app config** (`classpath:acme.apps.yaml`, `classpath:acme.processing.yaml`)
   - Workflows, activities, task queues
   - Non-sensitive defaults

2. **Temporal config** (ConfigMap from overlay)
   - Temporal namespace name
   - Temporal connection target (host:port)
   - TLS settings
   - **Non-sensitive, environment-specific**

3. **Temporal secret** (Secret from overlay)
   - Temporal API key (Temporal Cloud only)
   - **Sensitive data only**

Later sources override earlier ones. Overlay configs are mounted at:
- ConfigMap: `/etc/config/temporal/temporal-config.yaml`
- Secret: `/etc/config/temporal-secret/temporal-secret.yaml`

These are imported via Spring profile `k8s` which activates `application-k8s.yaml` (only when running in Kubernetes).

## Configuration Overlays

### Local Overlay (host.docker.internal)

```yaml
# k8s/overlays/local/configmap/temporal-apps.yaml
spring:
  temporal:
    namespace: apps
    connection:
      target: host.docker.internal:7233
      tls:
        enabled: false
```

Connects directly to your machine's localhost:7233 via KinD's `host.docker.internal` network alias.

### Cloud Overlay (Temporal Cloud)

```yaml
# k8s/overlays/cloud/configmap/temporal-apps.yaml
spring:
  temporal:
    namespace: fde-oms-apps.account-id
    connection:
      target: us-east-1.aws.api.temporal.io:7233
      tls-server-name: us-east-1.aws.api.temporal.io
      tls:
        enabled: true
```

API key loaded from Kubernetes Secret (not shown here for security).

## Updating Configuration

### Local changes
Edit `k8s/overlays/local/configmap/temporal-*.yaml`, then redeploy:
```bash
OVERLAY=local ./scripts/app-deploy.sh
```

### Cloud changes
1. Update API keys in secret files: `k8s/overlays/cloud/secrets/temporal-*-api-key.yaml`
2. Update ConfigMap: `k8s/overlays/cloud/configmap/temporal-*.yaml`
3. Redeploy:
```bash
OVERLAY=cloud ./scripts/app-deploy.sh
```

## Troubleshooting

**Workers can't connect to Temporal:**
```bash
# Check pod logs
kubectl logs -n temporal-oms-apps -l app=apps-worker

# Check mounted config
kubectl exec -it <pod-name> -n temporal-oms-apps -- cat /etc/config/temporal/temporal-config.yaml

# Verify KinD cluster is running
kind get clusters
kubectl get pods -A
```

**Connection refused errors:**
- **For local overlay**: Ensure `temporal server start-dev` is running on your host
- **For cloud overlay**: Verify API key is correct and TLS is enabled

**TLS handshake failures:**
- Check that `tls.enabled: true` is set in cloud overlay
- Verify `tls-server-name` matches the connection target hostname
- Check API key format is valid JWT token

**For more troubleshooting:**
See [../DEPLOYMENT.md](../DEPLOYMENT.md) — Troubleshooting section
