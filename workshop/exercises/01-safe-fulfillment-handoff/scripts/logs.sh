#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

prepare_environment

name="${1:-}"
if [[ -z "$name" ]]; then
  echo "Available logs:"
  find "$LOG_DIR" -maxdepth 1 -type f -name '*.log' -exec basename {} .log \; | sort
  echo ""
  echo "Usage: $0 <service-name>"
  exit 0
fi

log="$(log_file_for "$name")"
[[ -f "$log" ]] || die "No log found for '$name'. Expected: $log"

tail -n 120 -f "$log"
