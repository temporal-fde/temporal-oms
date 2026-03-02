#!/bin/bash
# Scenario: Canceling an Order
# Step 2: Cancel Order
# This executes the cancelOrder update to abort the order processing

set -e

echo "❌ Canceling order..."
echo "Workflow ID: cancel-order-123"
echo ""

temporal workflow update execute \
  --workflow-id cancel-order-123 \
  --name cancelOrder \
  --input '{"reason":"Customer requested cancellation","canceled_by":"demo-user"}' \
  --input-meta "encoding=json/protobuf" \
  --namespace apps

echo ""
echo "✅ Order cancellation processed"
echo "Demo complete! Check Temporal UI to see the order state."