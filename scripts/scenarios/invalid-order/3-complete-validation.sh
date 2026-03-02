#!/bin/bash
# Scenario: Complete Invalid Order
# Step 3: Complete Manual Validation
# This resolves the validation failure through the support team workflow
# The support team has reviewed the order and provided corrections

set -e

echo "✋ Resolving validation failure through manual correction..."
echo "Order ID: invalid-order-123"
echo ""

temporal workflow update execute \
  --workflow-id support-team \
  --name completeOrderValidation \
  --input '"invalid-order-123"' \
  --namespace processing

echo ""
echo "✅ Validation corrected by support team"
echo "Demo complete! Order can now proceed to fulfillment."
echo "Check Temporal UI to see the complete order flow and support team interaction."