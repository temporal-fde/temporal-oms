#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

prepare_environment

printf "%-30s %-10s %s\n" "SERVICE" "STATUS" "DETAIL"
for name in "${service_names[@]}"; do
  if service_is_running "$name"; then
    printf "%-30s %-10s pid %s\n" "$name" "running" "$(service_pid "$name")"
  else
    printf "%-30s %-10s %s\n" "$name" "stopped" "$(log_file_for "$name")"
  fi
done

if [[ -f "$STATE_DIR/enablement_id" ]]; then
  echo ""
  echo "Saved load generator: $(cat "$STATE_DIR/enablement_id")"
fi
