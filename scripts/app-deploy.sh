#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "📦 Building and deploying applications..."

# Build Java
echo "→ Building Java projects..."
cd java/apps
mvn clean package -DskipTests -q
cd "$PROJECT_DIR"

cd java/processing
mvn clean package -DskipTests -q
cd "$PROJECT_DIR"

# Build Docker images in Minikube context
echo "→ Building Docker images..."
eval $(minikube docker-env)

docker build -q -t temporal-oms/apps-api:latest \
  -f java/apps/apps-api/docker/Dockerfile java/apps/apps-api

docker build -q -t temporal-oms/apps-workers:latest \
  -f java/apps/apps-workers/docker/Dockerfile java/apps/apps-workers

docker build -q -t temporal-oms/processing-workers:latest \
  -f java/processing/processing-workers/docker/Dockerfile java/processing/processing-workers

# Deploy to Kubernetes
echo "→ Deploying to Minikube..."
kubectl apply -k k8s/overlays/local >/dev/null

# Set up secrets for processing namespace
kubectl create secret generic temporal-api-key -n temporal-oms-processing \
  --from-literal=dummy=true --dry-run=client -o yaml | kubectl apply -f - >/dev/null 2>&1 || true

kubectl get secret temporal-api-key -n temporal-oms-apps -o yaml | \
  sed 's/namespace: temporal-oms-apps/namespace: temporal-oms-processing/' | \
  kubectl apply -f - >/dev/null 2>&1 || true

# Delete old pods to force image pull
echo "→ Restarting pods..."
kubectl delete pods -n temporal-oms-apps --all 2>/dev/null || true
kubectl delete pods -n temporal-oms-processing --all 2>/dev/null || true

# Wait for pods to start
sleep 8

echo "✅ Applications deployed!"
echo ""
./scripts/status.sh
