#!/bin/bash
# Scenario: Complete Invalid Order
# Step 2: Capture Payment
# This captures payment for the order
# Order processing will begin and trigger validation failure

set -e

echo "💳 Capturing payment..."
echo "Order ID: invalid-order-123"
echo ""

xh POST http://localhost:8080/api/v1/payments-app/orders \
  customerId="cust-001" \
  rrn="payment-intent-456" \
  amountCents=9999 \
  metadata:='{"orderId":"invalid-order-123"}'

echo ""
echo "✅ Payment captured"
echo "⏳ Order is now processing and will trigger validation failure"
echo "Next step: Run 3-complete-validation.sh (after observing the validation failure)"