#!/bin/bash
# Scenario: Complete Valid Order
# Step 2: Capture Payment
# This captures payment and triggers order processing
# The order will pass validation and proceed to enrichment and fulfillment

set -e

echo "💳 Capturing payment..."
echo "Order ID: valid-order-123"
echo ""

xh POST http://localhost:8080/api/v1/payments-app/orders \
  customerId="cust-001" \
  rrn="payment-intent-789" \
  amountCents=9999 \
  metadata:='{"orderId":"valid-order-123"}'

echo ""
echo "✅ Payment captured"
echo "🚀 Order is now processing and will automatically pass validation"
echo ""
echo "Demo complete! The order is moving through the workflow:"
echo "  1. Order validated ✓"
echo "  2. Order enriched (inventory lookup, brand codes, etc.)"
echo "  3. Order fulfilled (shipped)"
echo ""
echo "Check Temporal UI to see the complete automated order flow."