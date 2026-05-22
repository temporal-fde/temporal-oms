#!/bin/bash
# Scenario: Canceling an Order
# Step 2: Cancel Order
# This executes the cancelOrder update to abort the order processing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_lib.sh"
scenario_resume "$SCRIPT_DIR"

echo "❌ Canceling order..."
echo "Workflow ID: ${ORDER_ID}"
echo "Customer ID: ${CUSTOMER_ID}"
echo ""

temporal workflow update execute \
  --workflow-id "${ORDER_ID}" \
  --name cancelOrder \
  --input '{"reason":"Customer requested cancellation","canceled_by":"demo-user"}' \
  --input-meta "encoding=json/protobuf" \
  --namespace apps

echo ""
echo "✅ Order cancellation processed"
echo "Demo complete! Check Temporal UI to see the order state."
