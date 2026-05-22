#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_lib.sh"

scenario_run_steps "$SCRIPT_DIR" "$@" -- \
  "1-submit-order.sh" \
  "2-capture-payment.sh"
