#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Configure kubectl for KinD
export KUBECONFIG=/tmp/kind-config.yaml

# Default to local overlay if not specified
OVERLAY="${OVERLAY:-local}"

echo "📦 Building and deploying applications (${OVERLAY} Temporal)..."

# Build Java
echo "→ Building Java projects..."
cd java/apps
mvn clean package -DskipTests -q
cd "$PROJECT_DIR"

cd java/processing
mvn clean package -DskipTests -q
cd "$PROJECT_DIR"

# Build Docker images and load into KinD
echo "→ Building Docker images..."
docker build -q -t temporal-oms/apps-api:latest \
  -f java/apps/apps-api/docker/Dockerfile java/apps/apps-api

docker build -q -t temporal-oms/apps-worker:latest \
  -f java/apps/apps-workers/docker/Dockerfile java/apps/apps-workers

docker build -q -t temporal-oms/processing-worker:latest \
  -f java/processing/processing-workers/docker/Dockerfile java/processing/processing-workers

# Load images into KinD cluster
echo "→ Loading images into KinD..."
kind load docker-image temporal-oms/apps-api:latest --name temporal-oms
kind load docker-image temporal-oms/apps-worker:latest --name temporal-oms
kind load docker-image temporal-oms/processing-worker:latest --name temporal-oms

# Deploy to Kubernetes
echo "→ Deploying to KinD..."
kubectl apply -k "k8s/overlays/${OVERLAY}" >/dev/null
kubectl apply -f k8s/ingress/apps-api-ingress.yaml >/dev/null

# Delete old pods to force image pull
echo "→ Restarting pods..."
kubectl delete pods -n temporal-oms-apps --all 2>/dev/null || true
kubectl delete pods -n temporal-oms-processing --all 2>/dev/null || true

# Wait for pods to start
sleep 8

echo "✅ Applications deployed!"
echo ""
./scripts/status.sh
