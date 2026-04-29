#!/bin/bash
# Scenario: Complete Valid Order
# Step 1: Submit Order (Valid)
# This submits an order that will pass all validation
# The order ID does NOT contain "invalid", so it will pass validation checks

set -e

echo "📋 Submitting VALID order for processing..."
echo "Workflow ID: valid-order-123"
echo "Note: This order will pass validation and proceed automatically"
echo ""

xh PUT http://localhost:8080/api/v1/commerce-app/orders/valid-order-123 \
  customerId="cust-001" \
  order:='{"orderId":"valid-order-123","items":[{"itemId":"shirt-001","quantity":1}],"shippingAddress":{"street":"11 Wall St","city":"New York","state":"NY","postalCode":"10005","country":"US"},"selectedShipment":{"paidPriceCents":"995","currency":"USD","deliveryDays":5}}'

echo ""
echo "✅ Order submitted"
echo "Next step: Run 2-capture-payment.sh"
