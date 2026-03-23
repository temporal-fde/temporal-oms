#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Configure kubectl for KinD
export KUBECONFIG=/tmp/kind-config.yaml

# Default to local overlay if not specified
OVERLAY="${OVERLAY:-local}"

echo "📦 Building and deploying applications (${OVERLAY} Temporal)..."

# Build Java (from root to ensure shared modules like oms are rebuilt and installed)
echo "→ Building Java projects..."
cd java
mvn clean install -DskipTests -q
cd "$PROJECT_DIR"

# Build Docker images and load into KinD
echo "→ Building Docker images..."
docker build -q -t temporal-oms/apps-api:latest \
  -f java/apps/apps-api/docker/Dockerfile java/apps/apps-api

docker build -q -t temporal-oms/apps-worker:latest \
  -f java/apps/apps-workers/docker/Dockerfile java/apps/apps-workers

docker build -q -t temporal-oms/processing-api:latest \
  -f java/processing/processing-api/docker/Dockerfile java/processing/processing-api

docker build -q -t temporal-oms/processing-workers:v1 \
  -f java/processing/processing-workers/docker/Dockerfile java/processing/processing-workers

# Load images into KinD cluster
echo "→ Loading images into KinD..."
kind load docker-image temporal-oms/apps-api:latest --name temporal-oms
kind load docker-image temporal-oms/apps-worker:latest --name temporal-oms
kind load docker-image temporal-oms/processing-api:latest --name temporal-oms
kind load docker-image temporal-oms/processing-workers:v1 --name temporal-oms

# Deploy to Kubernetes
echo "→ Deploying to KinD..."
kubectl apply -k "k8s/overlays/${OVERLAY}" >/dev/null
kubectl apply -k "k8s/processing-versioned/overlays/${OVERLAY}" >/dev/null
kubectl apply -f k8s/ingress/apps-api-ingress.yaml >/dev/null
kubectl apply -f k8s/ingress/processing-api-ingress.yaml >/dev/null

# Restart apps pods to pick up new images (processing pods are managed by the controller)
echo "→ Restarting apps pods..."
kubectl delete pods -n temporal-oms-apps --all 2>/dev/null || true

# Wait for pods to start
sleep 8

echo "✅ Applications deployed!"
echo ""
./scripts/status.sh
