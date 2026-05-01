#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

run_existing_scenario "margin-spike" "$@"

echo ""
echo "Expected proof points:"
echo "  ShippingAgent calls find_alternate_warehouse before accepting MARGIN_SPIKE."
echo "  fulfillment.Order records margin_leak when the selected rate exceeds margin."

