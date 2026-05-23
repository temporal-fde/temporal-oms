#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

prepare_environment
require_command temporal

ENABLEMENT_ID="${ENABLEMENT_ID:-safe-handoff-$(date +%Y%m%d%H%M%S)}"
ORDER_COUNT="${ORDER_COUNT:-1000}"
SUBMIT_RATE_PER_MIN="${SUBMIT_RATE_PER_MIN:-12}"
GENERATOR_TIMEOUT="${GENERATOR_TIMEOUT:-900s}"
ORDER_ID_SEED="${ORDER_ID_SEED:-order}"

echo "$ENABLEMENT_ID" >"$STATE_DIR/enablement_id"

temporal_cli workflow start \
  --task-queue enablements \
  --type WorkerVersionEnablement \
  --workflow-id "$ENABLEMENT_ID" \
  --namespace "$TEMPORAL_ENABLEMENTS_NAMESPACE" \
  --input "{\"enablementId\":\"${ENABLEMENT_ID}\",\"orderCount\":${ORDER_COUNT},\"submitRatePerMin\":${SUBMIT_RATE_PER_MIN},\"timeout\":\"${GENERATOR_TIMEOUT}\",\"orderIdSeed\":\"${ORDER_ID_SEED}\"}" \
  --input-meta 'encoding=json/protobuf'

cat <<EOF

Load generator started.
  ENABLEMENT_ID=$ENABLEMENT_ID
  Order IDs start with ${ORDER_ID_SEED}-${ENABLEMENT_ID}

Query state:
  temporal workflow query --workflow-id "$ENABLEMENT_ID" --namespace "$TEMPORAL_ENABLEMENTS_NAMESPACE" --type getState
EOF
