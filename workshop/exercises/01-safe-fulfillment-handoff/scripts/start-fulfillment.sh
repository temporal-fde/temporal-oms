#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

prepare_environment
require_command java
require_command curl
require_command uv

start_service fulfillment-workers env \
  TEMPORAL_DEPLOYMENT_NAME=fulfillment \
  TEMPORAL_WORKER_BUILD_ID=local \
  java -jar "$ROOT_DIR/java/fulfillment/fulfillment-workers/target/fulfillment-workers-1.0.0-SNAPSHOT.jar" \
  --server.port=8061 \
  --management.server.port=9072
wait_http fulfillment-workers http://127.0.0.1:9072/actuator/health

(
  cd "$ROOT_DIR/python"
  uv sync
)

start_service python-fulfillment-worker env \
  PYTHONPATH="$ROOT_DIR/python/generated:$ROOT_DIR/python/generated/pydantic:$ROOT_DIR/python/fulfillment${PYTHONPATH:+:$PYTHONPATH}" \
  TEMPORAL_FULFILLMENT_ADDRESS="$TEMPORAL_ADDRESS" \
  TEMPORAL_FULFILLMENT_NAMESPACE="$TEMPORAL_FULFILLMENT_NAMESPACE" \
  ENABLEMENTS_API_BASE_URL="$ENABLEMENTS_API_BASE_URL" \
  bash -lc 'cd python && exec uv run python -m src.worker'
wait_log python-fulfillment-worker "All workers polling"

print_runtime_summary
