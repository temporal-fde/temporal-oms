#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

RUN_DIR="$ROOT_DIR/.workshop/run"
LOG_DIR="$ROOT_DIR/.workshop/logs"

pid_is_running() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

service_status() {
  local name="$1"
  local pid_file="$RUN_DIR/$name.pid"
  local pid=""
  if [[ -f "$pid_file" ]]; then
    pid="$(cat "$pid_file" 2>/dev/null || true)"
  fi

  if pid_is_running "$pid"; then
    printf "%-28s %-10s pid %s\n" "$name" "running" "$pid"
  else
    printf "%-28s %-10s %s\n" "$name" "stopped" "$LOG_DIR/$name.log"
  fi
}

service_is_running() {
  local name="$1"
  local pid_file="$RUN_DIR/$name.pid"
  local pid=""
  if [[ -f "$pid_file" ]]; then
    pid="$(cat "$pid_file" 2>/dev/null || true)"
  fi
  pid_is_running "$pid"
}

echo "Temporal"
if temporal --disable-config-file --disable-config-env --address "$TEMPORAL_ADDRESS" \
  operator cluster health --command-timeout 5s >/dev/null 2>&1; then
  echo "  ready at $TEMPORAL_ADDRESS"
else
  echo "  not reachable at $TEMPORAL_ADDRESS"
fi

echo ""
echo "Local services managed by scripts/local-up.sh"
printf "%-28s %-10s %s\n" "SERVICE" "STATUS" "DETAIL"
for name in \
  enablements-api \
  fulfillment-api \
  processing-api \
  apps-api \
  apps-workers \
  processing-workers \
  fulfillment-workers \
  enablements-workers \
  python-fulfillment-worker
do
  service_status "$name"
done

echo ""
if service_is_running "python-fulfillment-worker" \
  && [[ -f "$LOG_DIR/python-fulfillment-worker.log" ]] \
  && grep -q "All workers polling" "$LOG_DIR/python-fulfillment-worker.log"; then
  echo "Python fulfillment worker: agents and fulfillment-shipping are polling"
else
  echo "Python fulfillment worker: polling confirmation not found in $LOG_DIR/python-fulfillment-worker.log"
fi

echo ""
echo "Worker Deployment state"
for entry in "apps:apps" "processing:processing"; do
  deployment="${entry%%:*}"
  namespace="${entry##*:}"
  echo ""
  echo "$deployment / namespace $namespace"
  temporal --disable-config-file --disable-config-env --address "$TEMPORAL_ADDRESS" \
    worker deployment describe \
    --name "$deployment" \
    --namespace "$namespace" \
    2>/dev/null || echo "  not available"
done
