#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

prepare_environment
require_command temporal

ENABLEMENT_ID="${ENABLEMENT_ID:-}"
if [[ -z "$ENABLEMENT_ID" && -f "$STATE_DIR/enablement_id" ]]; then
  ENABLEMENT_ID="$(cat "$STATE_DIR/enablement_id")"
fi

[[ -n "$ENABLEMENT_ID" ]] || die "No ENABLEMENT_ID provided and no saved load-generator state exists."

temporal_cli workflow terminate \
  --workflow-id "$ENABLEMENT_ID" \
  --namespace "$TEMPORAL_ENABLEMENTS_NAMESPACE" \
  --reason "Exercise 01 complete" || true

rm -f "$STATE_DIR/enablement_id"
echo "Load generator stopped: $ENABLEMENT_ID"
