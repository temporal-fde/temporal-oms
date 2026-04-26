#!/bin/bash
# Scenario: Complete Invalid Order
# Step 1: Submit Order (Invalid)
# This submits an order that will fail validation
# The order ID contains "invalid" which triggers validation failure in the system

set -e

echo "📋 Submitting INVALID order for processing..."
echo "Workflow ID: invalid-order-123"
echo "Note: This order will fail validation and require manual correction"
echo ""

xh PUT http://localhost:8080/api/v1/commerce-app/orders/invalid-order-123 \
  customerId="cust-001" \
  order:='{"orderId":"invalid-order-123","items":[{"itemId":"shirt-001","quantity":1}],"shippingAddress":{"street":"388 Townsend St","city":"San Francisco","state":"CA","postalCode":"94107","country":"US"}}'

echo ""
echo "✅ Order submitted"
echo "Next step: Run 2-capture-payment.sh"