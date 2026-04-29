#!/bin/bash
# Scenario: Canceling an Order
# Step 1: Submit Order
# This creates the workflow instance with an order ready to be canceled

set -e

echo "📋 Submitting order for cancellation scenario..."
echo "Workflow ID: cancel-order-123"
echo ""

xh PUT http://localhost:8080/api/v1/commerce-app/orders/cancel-order-123 \
  customerId="cust-001" \
  order:='{"orderId":"cancel-order-123","items":[{"itemId":"shirt-001","quantity":1}],"shippingAddress":{"street":"11 Wall St","city":"New York","state":"NY","postalCode":"10005","country":"US"},"selectedShipment":{"paidPriceCents":"995","currency":"USD","deliveryDays":5}}'

echo ""
echo "✅ Order submitted successfully"
echo "Next step: Run 2-cancel-order.sh"
