#!/usr/bin/env bash
# apply-twc-processing.sh - build and roll out a new processing-workers
# version under the Temporal Worker Controller.
#
# Workshop Part 2 helper. Wraps the project-root deploy script for the chosen
# cluster runner (KinD or k3d). Run from anywhere; the script resolves repo
# root via _lib.sh.
#
# Usage:
#   ./scripts/apply-twc-processing.sh
#   VERSION=v3 RUNNER=k3d ./scripts/apply-twc-processing.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

VERSION="${VERSION:-v2}"
RUNNER="${RUNNER:-kind}"

case "$RUNNER" in
  kind|k3d) ;;
  *) die "Unsupported RUNNER=$RUNNER (use 'kind' or 'k3d')." ;;
esac

DEPLOY_SCRIPT="$ROOT_DIR/scripts/$RUNNER/deploy-processing-workers.sh"
[[ -x "$DEPLOY_SCRIPT" ]] || die "Missing deploy script: $DEPLOY_SCRIPT"

echo "Applying processing-workers ${VERSION} via ${RUNNER}..."
VERSION="$VERSION" "$DEPLOY_SCRIPT"

cat <<EOF

Done. Watch the rollout:
  $SCRIPT_DIR/watch-twc-rollout.sh
or:
  kubectl get temporalworkerdeployment processing-workers -n temporal-oms-processing -w
EOF
