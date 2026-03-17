# Kubernetes Deployment with Kustomize

This directory contains a Kustomize-based deployment structure that supports both local (Minikube) and cloud (Temporal Cloud) environments.

## Directory Structure

```
k8s/
├── base/                          # Base resources (Deployments, Services, Namespaces)
│   ├── namespaces/
│   ├── apps/
│   └── processing/
├── overlays/
│   ├── local/                     # Local Minikube configuration
│   │   ├── configmap/             # Temporal connection: localhost:7233
│   │   ├── secrets/               # Temporal API key for local
│   │   └── kustomization.yaml
│   └── cloud/                     # Cloud Temporal configuration
│       ├── configmap/             # Temporal connection: cloud address
│       ├── secrets/               # Temporal API key for cloud
│       └── kustomization.yaml
```

## Usage

### Deploy to Local Minikube

```bash
kubectl apply -k k8s/overlays/local
```

**Deployment details:**
- Namespaces: `temporal-oms-apps`, `temporal-oms-processing`
- Temporal namespaces: `apps`, `processing`
- Temporal address: `temporal-frontend.temporal.svc.cluster.local:7233` → localhost:7233

### Deploy to Cloud

**Before deploying:**
1. Update `k8s/overlays/cloud/configmap/temporal-apps.yaml` — replace `<TEMPORAL_CLOUD_HOST>`
2. Update `k8s/overlays/cloud/configmap/temporal-processing.yaml` — replace `<TEMPORAL_CLOUD_HOST>`
3. Update `k8s/overlays/cloud/secrets/temporal-api-key.yaml` — replace `<YOUR_TEMPORAL_CLOUD_API_KEY>`

**Then deploy:**
```bash
kubectl apply -k k8s/overlays/cloud
```

**Deployment details:**
- Namespaces: `temporal-oms-apps`, `temporal-oms-processing`
- Temporal namespaces: `fde-oms-apps.sdvdw`, `fde-oms-processing.sdvdw`
- Temporal address: Your Temporal Cloud host

## How Configuration Works

### Spring Boot merges three YAML sources (in order):

1. **Base app config** (`classpath:acme.apps.yaml`, `classpath:acme.processing.yaml`)
   - Workflows, activities, task queues
   - Non-sensitive defaults

2. **Temporal config** (ConfigMap from overlay)
   - Temporal namespace name
   - Temporal connection target (host:port)
   - **Non-sensitive, environment-specific**

3. **Temporal secret** (Secret from overlay)
   - Temporal API key
   - **Sensitive data only**

Later sources override earlier ones. Both overlay configs mounted at:
- ConfigMap: `/etc/config/temporal/temporal-config.yaml`
- Secret: `/etc/config/temporal-secret/temporal-secret.yaml`

## Local Minikube Setup

To run with Temporal on your localhost:

1. **Start Temporal locally**
   ```bash
   temporal server start-dev
   ```

2. **Create namespaces** (if needed)
   ```bash
   temporal operator namespace create apps
   temporal operator namespace create processing
   ```

3. **Create bridge service** (already done)
   ```bash
   kubectl create namespace temporal
   kubectl apply -f k8s/overlays/local/temporal-bridge-service.yaml
   ```

4. **Deploy workers**
   ```bash
   kubectl apply -k k8s/overlays/local
   ```

The ExternalName Service routes `temporal-frontend.temporal.svc.cluster.local:7233` → `host.docker.internal:7233` → your host's localhost:7233.

## Updating Configuration

### Local changes
Edit `k8s/overlays/local/configmap/temporal-*.yaml`, then:
```bash
kubectl apply -k k8s/overlays/local
```

### Cloud changes
Edit `k8s/overlays/cloud/configmap/temporal-*.yaml` or `k8s/overlays/cloud/secrets/temporal-api-key.yaml`, then:
```bash
kubectl apply -k k8s/overlays/cloud
```

## Troubleshooting

**Workers can't connect to Temporal:**
```bash
# Check service
kubectl get svc -n temporal

# Check mounted config
kubectl exec -it <pod-name> -n temporal-oms-apps -- cat /etc/config/temporal/temporal-config.yaml

# Check logs
kubectl logs -n temporal-oms-apps -l app=apps-worker
```

**Config not merging:**
- Verify `spring.config.import` in `application.yaml`
- Check that files mount to correct paths
- Review Spring Boot startup logs
