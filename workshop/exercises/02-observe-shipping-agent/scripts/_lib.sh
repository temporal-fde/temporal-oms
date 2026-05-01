#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXERCISE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-127.0.0.1:7233}"
TEMPORAL_UI_URL="${TEMPORAL_UI_URL:-http://localhost:8233}"

scenario_context_file() {
  local scenario="$1"
  local state_dir="${SCENARIO_STATE_DIR:-${TMPDIR:-/tmp}/fde-temporal-oms-scenarios}"
  echo "${state_dir}/${scenario}.env"
}

load_scenario_context() {
  local scenario="$1"
  local context_file
  context_file="$(scenario_context_file "$scenario")"
  if [[ -f "$context_file" ]]; then
    # shellcheck disable=SC1090
    source "$context_file"
  fi
}

print_lookup_hints() {
  local scenario="$1"
  load_scenario_context "$scenario"

  echo ""
  echo "Temporal UI: ${TEMPORAL_UI_URL}"
  echo ""
  if [[ -n "${ORDER_ID:-}" ]]; then
    echo "Order workflow ID: ${ORDER_ID}"
    echo "  apps namespace:        apps.Order / ${ORDER_ID}"
    echo "  fulfillment namespace: fulfillment.Order / ${ORDER_ID}"
  else
    echo "Order workflow ID: not found. Check $(scenario_context_file "$scenario")"
  fi

  if [[ -n "${CUSTOMER_ID:-}" ]]; then
    echo "ShippingAgent workflow ID: ${CUSTOMER_ID}"
    echo "  fulfillment namespace: ShippingAgent / ${CUSTOMER_ID}"
  else
    echo "ShippingAgent workflow ID: not found. Check $(scenario_context_file "$scenario")"
  fi

  echo ""
  echo "Useful fulfillment visibility queries:"
  echo "  margin_leak > 0"
  echo "  margin_leak >= 500"
  echo "  sla_breach_days > 0"
  echo "  margin_leak > 0 OR sla_breach_days > 0"
}

run_existing_scenario() {
  local scenario="$1"
  shift || true

  (
    cd "$ROOT_DIR"
    "./scripts/scenarios/${scenario}/run.sh" --yes "$@"
  )
  print_lookup_hints "$scenario"
}

