#!/bin/bash
set -e

# deploy-processing-workers.sh — bump the processing workers to a new version
#
# Usage:
#   VERSION=v2 ./scripts/deploy-processing-workers.sh
#
# This script is the entire "deploy a new worker version" operation.
# In a remote Worker Fleet environment this would push to a registry instead
# of loading into KinD, but the Kubernetes patch step is identical.

VERSION="${VERSION:-v2}"
IMAGE="temporal-oms/processing-workers:${VERSION}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
export KUBECONFIG=/tmp/kind-config.yaml

echo "🚀 Deploying processing workers ${VERSION}..."

# Step 1 — Build the Java artifacts.
# All modules share the root pom, so a full install ensures the worker picks up
# any changes from processing-core or the generated protobuf module.
echo "→ Building Java..."
cd java && mvn clean install -DskipTests -q && cd "$PROJECT_DIR"

# Step 2 — Build the Docker image tagged with the explicit version.
# The Temporal Worker Controller derives the Temporal build-id from this tag
# combined with a hash of the pod template spec. Using an explicit version
# (v1, v2, ...) instead of :latest ensures each deployment produces a distinct
# build-id and Temporal treats it as a new version.
echo "→ Building image ${IMAGE}..."
docker build -q -t "${IMAGE}" \
  -f java/processing/processing-workers/docker/Dockerfile \
  java/processing/processing-workers

# Step 3 — Make the image available to KinD nodes.
# KinD runs in Docker but its nodes cannot pull from the local Docker daemon
# directly — images must be explicitly loaded. In a remote environment this
# step would be replaced by `docker push` to a registry.
echo "→ Loading image into KinD cluster..."
kind load docker-image "${IMAGE}" --name temporal-oms

# Step 4 — Patch the TemporalWorkerDeployment with the new image.
# This is the trigger: the controller detects the image change, computes a new
# build-id, registers it with Temporal as a new worker version, then starts
# pods running the new image. The rollout strategy (Progressive) ramps traffic
# gradually — new workflows are pinned to the new version while existing
# workflows continue running on the previous version until they complete.
echo "→ Patching TemporalWorkerDeployment to ${IMAGE}..."
kubectl patch temporalworkerdeployment processing-workers \
  -n temporal-oms-processing \
  --type=merge \
  -p "{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"worker\",\"image\":\"${IMAGE}\"}]}}}}"

echo ""
echo "✅ processing-workers ${VERSION} deployed."
echo "   The controller will now register a new Temporal build-id and begin"
echo "   the progressive rollout. Watch the transition with:"
echo "   kubectl get temporalworkerdeployment processing-workers -n temporal-oms-processing -w"
