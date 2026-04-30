#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"
. "$PROJECT_DIR/scripts/_lib/java-tools.sh"

export KUBECONFIG=/tmp/kind-config.yaml

OVERLAY="${OVERLAY:-local}"
PROCESSING_WORKER_MODE="${PROCESSING_WORKER_MODE:-versioned}"

echo "📦 Building and deploying applications to KinD (${OVERLAY} Temporal)..."

echo "→ Building Java projects..."
JAVAC_EXECUTABLE="$(resolve_javac_executable)"
(cd java && mvn -Djavac.executable="$JAVAC_EXECUTABLE" clean install -DskipTests -q)

echo "→ Building Docker images..."
docker build -q -t temporal-oms/apps-api:latest \
  -f java/apps/apps-api/docker/Dockerfile java/apps/apps-api

docker build -q -t temporal-oms/apps-worker:latest \
  -f java/apps/apps-workers/docker/Dockerfile java/apps/apps-workers

docker build -q -t temporal-oms/processing-api:latest \
  -f java/processing/processing-api/docker/Dockerfile java/processing/processing-api

docker build -q -t temporal-oms/processing-workers:latest -t temporal-oms/processing-workers:v1 \
  -f java/processing/processing-workers/docker/Dockerfile java/processing/processing-workers

docker build -q -t temporal-oms/enablements-api:latest \
  -f java/enablements/enablements-api/docker/Dockerfile java/enablements/enablements-api

docker build -q -t temporal-oms/enablements-workers:latest \
  -f java/enablements/enablements-workers/docker/Dockerfile java/enablements/enablements-workers

docker build -q -t temporal-oms/fulfillment-workers:latest \
  -f java/fulfillment/fulfillment-workers/docker/Dockerfile java/fulfillment/fulfillment-workers

docker build -q -t temporal-oms/fulfillment-python-worker:latest \
  -f python/fulfillment/Dockerfile python

echo "→ Loading images into KinD..."
kind load docker-image temporal-oms/apps-api:latest --name temporal-oms
kind load docker-image temporal-oms/apps-worker:latest --name temporal-oms
kind load docker-image temporal-oms/processing-api:latest --name temporal-oms
kind load docker-image temporal-oms/processing-workers:latest --name temporal-oms
kind load docker-image temporal-oms/processing-workers:v1 --name temporal-oms
kind load docker-image temporal-oms/enablements-api:latest --name temporal-oms
kind load docker-image temporal-oms/enablements-workers:latest --name temporal-oms
kind load docker-image temporal-oms/fulfillment-workers:latest --name temporal-oms
kind load docker-image temporal-oms/fulfillment-python-worker:latest --name temporal-oms

echo "→ Deploying to KinD..."
kubectl apply -k "k8s/overlays/${OVERLAY}" >/dev/null
if [ "$PROCESSING_WORKER_MODE" = "versioned" ]; then
  kubectl delete deployment processing-workers -n temporal-oms-processing --ignore-not-found >/dev/null
  kubectl apply -k "k8s/processing-versioned/overlays/${OVERLAY}" >/dev/null
else
  kubectl delete temporalworkerdeployment processing-workers -n temporal-oms-processing --ignore-not-found >/dev/null
fi
kubectl apply -f k8s/ingress/apps-api-ingress.yaml >/dev/null
kubectl apply -f k8s/ingress/processing-api-ingress.yaml >/dev/null

echo "→ Restarting pods..."
for ns in temporal-oms-apps temporal-oms-processing temporal-oms-enablements temporal-oms-fulfillment; do
  kubectl delete pods -n "$ns" --all 2>/dev/null || true
done

sleep 8

echo "✅ Applications deployed to KinD!"
echo ""
scripts/kind/status.sh
