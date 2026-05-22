#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

run_existing_scenario "sla-breach" "$@"

echo ""
echo "Expected proof points:"
echo "  ShippingAgent calls find_alternate_warehouse before accepting SLA_BREACH."
echo "  fulfillment.Order records sla_breach_days when the selected option misses the promised delivery window."

