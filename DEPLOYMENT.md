# Temporal OMS - Minikube Deployment Guide

> WIP - Not yet ready 

## Prerequisites

### Install Required Tools

```bash
# Minikube
brew install minikube

# kubectl
brew install kubectl

# Helm
brew install helm

# Docker Desktop (already installed)
```

## Setup Steps

### 1. Install Cert-Manager

```bash
# Install cert-manager (required by OpenTelemetry Operator)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=5m
```

### 2. Start Minikube

```bash
# Start with sufficient resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

### 3. Install OpenTelemetry Operator

```bash
# Add OpenTelemetry Operator repo
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

# Install OpenTelemetry Operator
kubectl create namespace opentelemetry-operator-system

helm install opentelemetry-operator \
  open-telemetry/opentelemetry-operator \
  --namespace opentelemetry-operator-system \
  --set manager.collectorImage.repository=otel/opentelemetry-collector-k8s
```

**Verify installation:**
```bash
kubectl get pods -n opentelemetry-operator-system
```

### 4. Install Temporal Worker Controller

```bash
# Create namespace for temporal-worker-controller
kubectl create namespace temporal-worker-controller-system

# Install via Helm
helm install temporal-worker-controller \
  oci://docker.io/temporalio/temporal-worker-controller \
  --namespace temporal-worker-controller-system

# Verify installation
kubectl get pods -n temporal-worker-controller-system
kubectl get crd | grep temporal
```

**Expected CRDs:**
- `temporalconnections.temporal.io`
- `temporalworkerdeployments.temporal.io`

### 5. Install Temporal Server

```bash
# Add Temporal Helm repo
helm repo add temporalio https://go.temporal.io/helm-charts
helm repo update

# Create temporal namespace
kubectl create namespace temporal

# Install Temporal
helm install temporal temporalio/temporal \
  --namespace temporal \
  --set server.replicaCount=1 \
  --set cassandra.config.cluster_size=1 \
  --set prometheus.enabled=true \
  --set grafana.enabled=true \
  --set web.enabled=true
```

**Wait for Temporal to be ready:**
```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=temporal -n temporal --timeout=5m
```

### 6. Create Temporal Namespaces

```bash
# Port-forward to Temporal frontend
kubectl port-forward -n temporal svc/temporal-frontend 7233:7233 &

# Create namespaces using Temporal CLI
temporal operator namespace create apps
temporal operator namespace create processing
temporal operator namespace create risk
temporal operator namespace create fulfillments

# Verify namespaces
temporal operator namespace list
```

### 7. Build Docker Images

```bash
# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build apps-api image
cd java
mvn clean package -pl apps
docker build -t temporal-oms/apps-api:latest -f apps/docker/Dockerfile.api apps/

# Build apps-worker image
docker build -t temporal-oms/apps-worker:latest -f apps/docker/Dockerfile.worker apps/

# Build processing-worker image
mvn clean package -pl processing
docker build -t temporal-oms/processing-worker:latest -f processing/docker/Dockerfile processing/

# Verify images
docker images | grep temporal-oms
```

### 7.1 Configure Secrets (Local Development)

Before deploying, set up your local secret files:

```bash
cd ../../  # Back to project root

# Copy secret templates to create local files
cp config/temporal.secret.template.yaml config/temporal.secret.yaml

# Edit and fill in actual values
# For local Minikube: can use placeholder values
vim config/temporal.secret.yaml

# Verify files were created and are ignored by git
ls -la config/*.secret.yaml
git status  # Should not show .secret.yaml files
```

**For Kubernetes deployment,** populate the K8s secret manifests:

```bash
# Generate base64-encoded content for temporal secrets
base64 -i config/temporal.secret.yaml | pbcopy

# Edit the manifest and paste into the data section
vim k8s/secrets/temporal-secrets.yaml

# Note: Use .gitignore'd populated manifests locally,
# not the .template versions
```

### 8. Deploy Application

```bash
# Create namespaces
kubectl apply -f k8s/namespace.yaml

# Create ConfigMaps (one per namespace)
kubectl apply -f k8s/configmap.yaml

# Apply K8s Secret objects (from populated manifests)
kubectl apply -f k8s/secrets/temporal-secrets.yaml
kubectl apply -f k8s/secrets/acme-apps-secret.yaml
kubectl apply -f k8s/secrets/acme-processing-secret.yaml

# Deploy Apps service (API + Worker) in temporal-oms-apps namespace
kubectl apply -f k8s/apps/deployment-api.yaml
kubectl apply -f k8s/apps/temporal-worker.yaml

# Deploy Processing worker in temporal-oms-processing namespace
kubectl apply -f k8s/processing/temporal-worker.yaml
```

### 9. Verify Deployment

```bash
# Check all pods in both namespaces
kubectl get pods -n temporal-oms-apps
kubectl get pods -n temporal-oms-processing

# Check TemporalWorkerDeployment CRDs
kubectl get temporalworkerdeployments -n temporal-oms-apps
kubectl get temporalworkerdeployments -n temporal-oms-processing

# Check logs
kubectl logs -n temporal-oms-apps -l app=apps-api
kubectl logs -n temporal-oms-apps -l app=apps-worker
kubectl logs -n temporal-oms-processing -l app=processing-worker

# Verify secrets are mounted (infrastructure validation only)
POD=$(kubectl get pods -n temporal-oms-apps -l app=apps-api -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD -n temporal-oms-apps -- ls -la /etc/config/secrets/
kubectl exec -it $POD -n temporal-oms-apps -- head -3 /etc/config/secrets/acme/acme.apps.secret.yaml

# Verify K8s Secrets exist
kubectl get secrets -n temporal-oms-apps
kubectl get secrets -n temporal-oms-processing
```

**Note:** The verification above only checks that files are mounted. Application-specific integration testing (how each language loads and uses the secrets) is deferred to component-specific specs.

## Accessing Services

### API Swagger UI

```bash
# Get API URL
minikube service apps-api -n temporal-oms-apps --url

# Or use port-forward
kubectl port-forward -n temporal-oms-apps svc/apps-api 8080:80

# Access Swagger UI (MANDATORY per stack-api-rest)
open http://localhost:8080/docs
```

### Temporal UI

```bash
# Port-forward to Temporal UI
kubectl port-forward -n temporal svc/temporal-web 8233:8233

# Access Temporal UI
open http://localhost:8233
```

## Worker Versioning Workflow

### Initial Deployment (v1.0.0)

Already deployed above with buildId "1.0.0"

### Rolling Update to v1.1.0

```bash
# 1. Build new images with updated code
eval $(minikube docker-env)
cd java
mvn clean package -pl apps
docker build -t temporal-oms/apps-worker:1.1.0 -f apps/docker/Dockerfile.worker apps/

# 2. Update buildId in worker manifests
# Edit k8s/apps/temporal-worker.yaml:
#   spec.buildId: "1.1.0"
#   template.metadata.labels.version: "1.1.0"
#   template.spec.containers[0].env BUILD_ID: "1.1.0"

# 3. Apply update
kubectl apply -f k8s/apps/temporal-worker.yaml

# 4. Watch rollout
kubectl get temporalworkerdeployments -n temporal-oms -w

# The Temporal Worker Controller will:
# - Start new workers with buildId "1.1.0"
# - Register new version with Temporal
# - New workflows use v1.1.0
# - Existing workflows continue on v1.0.0
# - Gradually drain v1.0.0 workers
```

### Check Worker Versions

```bash
# Via Temporal CLI
temporal task-queue describe --task-queue apps

# Via Temporal UI
# Navigate to: Workflows -> Task Queues -> apps
```

## Development Workflow

### Make Code Changes

```bash
# 1. Edit Java code
vim java/apps/src/main/java/com/acme/apps/workflows/OrderImpl.java

# 2. Rebuild
cd java
mvn clean package -pl apps

# 3. Rebuild Docker image
eval $(minikube docker-env)
docker build -t temporal-oms/apps-worker:latest -f apps/docker/Dockerfile.worker apps/

# 4. Restart workers (triggers new deployment)
kubectl rollout restart temporalworkerdeployment/apps-worker -n temporal-oms-apps

# 5. Watch rollout
kubectl rollout status temporalworkerdeployment/apps-worker -n temporal-oms-apps
```

### View Logs

```bash
# API logs
kubectl logs -f -n temporal-oms-apps -l app=apps-api

# Apps worker logs
kubectl logs -f -n temporal-oms-apps -l app=apps-worker

# Processing worker logs
kubectl logs -f -n temporal-oms-processing -l app=processing-worker

# All workers in apps namespace
kubectl logs -f -n temporal-oms-apps -l component=worker
# All workers in processing namespace
kubectl logs -f -n temporal-oms-processing -l component=worker
```

### Test the API

```bash
# Get API URL
API_URL=$(minikube service apps-api -n temporal-oms-apps --url)

# Submit commerce order
curl -X PUT "$API_URL/api/v1/commerce-app/orders/order-001" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-commerce-key-12345" \
  -d '{
    "customerId": "customer-123",
    "order": {
      "orderId": "order-001",
      "items": [
        {"itemId": "item-1", "quantity": 2}
      ],
      "shippingAddress": {
        "street": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "postalCode": "94105",
        "country": "US"
      }
    }
  }'

# Check Swagger UI
open "$API_URL/docs"
```

## Cleanup

### Remove Application

```bash
kubectl delete namespace temporal-oms-apps
kubectl delete namespace temporal-oms-processing
```

### Remove Temporal

```bash
helm uninstall temporal -n temporal
kubectl delete namespace temporal
```

### Remove Operators

```bash
helm uninstall temporal-worker-controller -n temporal-worker-controller-system
kubectl delete namespace temporal-worker-controller-system

helm uninstall opentelemetry-operator -n opentelemetry-operator-system
kubectl delete namespace opentelemetry-operator-system
```

### Stop Minikube

```bash
minikube stop
minikube delete  # Complete removal
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status (replace namespace with temporal-oms-apps or temporal-oms-processing)
kubectl describe pod <pod-name> -n temporal-oms-apps

# Check events
kubectl get events -n temporal-oms-apps --sort-by='.lastTimestamp'
```

### Image Pull Errors

```bash
# Ensure using Minikube's Docker daemon
eval $(minikube docker-env)

# Verify images exist
docker images | grep temporal-oms

# imagePullPolicy should be "Never" for local images
```

### Worker Not Registering

```bash
# Check worker logs (replace namespace with temporal-oms-apps or temporal-oms-processing)
kubectl logs -n temporal-oms-apps -l app=apps-worker

# Check Temporal connectivity
kubectl exec -it -n temporal-oms-apps <worker-pod> -- sh
wget -O- http://temporal-frontend.temporal.svc.cluster.local:7233
```

### Temporal Namespace Not Found

```bash
# Create namespace via Temporal CLI
kubectl port-forward -n temporal svc/temporal-frontend 7233:7233 &
temporal operator namespace create apps --address localhost:7233
```

## Architecture

### Kubernetes Namespaces

| K8s Namespace | Components | Description |
|---------------|-----------|-------------|
| temporal-oms-apps | apps-api, apps-worker, web | Application services and workflows |
| temporal-oms-processing | processing-worker | Order processing workflows |

### Services Deployed

| Service | Type | Port | K8s Namespace | Description |
|---------|------|------|---------------|-------------|
| apps-api | Deployment | 8080 | temporal-oms-apps | REST API for webhooks |
| apps-worker | TemporalWorkerDeployment | 9090 | temporal-oms-apps | CompleteOrder workflows |
| processing-worker | TemporalWorkerDeployment | 9090 | temporal-oms-processing | Order processing workflows |
| web | Deployment | 3000 | temporal-oms-apps | Frontend web UI |

### Temporal Namespaces

| Temporal Namespace | Task Queue | Workers | K8s Namespace | Description |
|-------------------|-----------|---------|---------------|-------------|
| apps | apps | 2 | temporal-oms-apps | Application orchestration |
| processing | processing | 2 | temporal-oms-processing | Order processing |

### Resource Allocation

| Service | Memory Request | Memory Limit | CPU Request | CPU Limit | K8s Namespace |
|---------|----------------|--------------|-------------|-----------|---|
| apps-api | 512Mi | 1Gi | 250m | 1000m | temporal-oms-apps |
| apps-worker | 512Mi | 2Gi | 250m | 2000m | temporal-oms-apps |
| web | 256Mi | 512Mi | 100m | 500m | temporal-oms-apps |
| processing-worker | 512Mi | 2Gi | 250m | 2000m | temporal-oms-processing |

**Total Resources:**
- Memory: ~6Gi
- CPU: ~1.8 cores

## Skills Applied

This deployment follows patterns from:
- ✅ **deployment-kubernetes-local** - Minikube setup, TemporalWorker CRD, OpenTelemetry
- ✅ **stack-temporal** - Worker versioning, graceful shutdown, resource tuning
- ✅ **stack-api-rest** - Swagger UI at /docs, health checks
- ✅ **patterns** - Bounded contexts as separate workers

## References

- Temporal Worker Controller: https://github.com/temporalio/temporal-worker-controller
- OpenTelemetry Operator: https://github.com/open-telemetry/opentelemetry-operator
- Minikube: https://minikube.sigs.k8s.io/
- Temporal Helm Charts: https://github.com/temporalio/helm-charts
