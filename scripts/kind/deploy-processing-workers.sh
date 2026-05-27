#!/bin/bash
set -e

# deploy-processing-workers.sh — bump the processing workers to a new version
#
# Usage:
#   VERSION=v2 ./scripts/kind/deploy-processing-workers.sh

VERSION="${VERSION:-v2}"
IMAGE="temporal-oms/processing-workers:${VERSION}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"
. "$PROJECT_DIR/scripts/_lib/java-tools.sh"
export KUBECONFIG=/tmp/kind-config.yaml

echo "🚀 Deploying processing workers ${VERSION} to KinD..."

echo "→ Building Java..."
JAVAC_EXECUTABLE="$(resolve_javac_executable)"
(cd java && mvn -Djavac.executable="$JAVAC_EXECUTABLE" clean install -DskipTests -q)

echo "→ Building image ${IMAGE}..."
docker build -q -t "${IMAGE}" \
  -f java/processing/processing-workers/docker/Dockerfile \
  java/processing/processing-workers

echo "→ Loading image into KinD cluster..."
kind load docker-image "${IMAGE}" --name temporal-oms

echo "→ Patching WorkerDeployment to ${IMAGE}..."
kubectl patch workerdeployment processing-workers \
  -n temporal-oms-processing \
  --type=json \
  -p "[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/image\",\"value\":\"${IMAGE}\"}]"

echo ""
echo "✅ processing-workers ${VERSION} deployed to KinD."
echo "   Watch the rollout with:"
echo "   kubectl get workerdeployment processing-workers -n temporal-oms-processing -w"
