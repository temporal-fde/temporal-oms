#!/usr/bin/env bash
# watch-twc-rollout.sh - observe the Temporal Worker Controller rolling out
# the processing-workers deployment.
#
# Workshop Part 2 helper. Defaults to `kubectl get -w` against the local
# KinD/k3d cluster's processing namespace. Set MODE=k9s to launch k9s instead.
#
# Usage:
#   ./scripts/watch-twc-rollout.sh
#   MODE=k9s ./scripts/watch-twc-rollout.sh
#   TWC_NAMESPACE=temporal-oms-processing TWC_NAME=processing-workers ./scripts/watch-twc-rollout.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

NAMESPACE="${TWC_NAMESPACE:-temporal-oms-processing}"
NAME="${TWC_NAME:-processing-workers}"
MODE="${MODE:-kubectl}"

case "$MODE" in
  kubectl)
    require_command kubectl
    echo "Watching TemporalWorkerDeployment ${NAME} in ${NAMESPACE} (Ctrl-C to exit)..."
    kubectl get temporalworkerdeployment "$NAME" -n "$NAMESPACE" -w
    ;;
  k9s)
    require_command k9s
    echo "Launching k9s into ${NAMESPACE}..."
    k9s -n "$NAMESPACE"
    ;;
  *)
    die "Unsupported MODE=$MODE (use 'kubectl' or 'k9s')."
    ;;
esac
