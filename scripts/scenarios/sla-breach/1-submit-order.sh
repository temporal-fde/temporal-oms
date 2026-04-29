#!/bin/bash
# Scenario: SLA Breach — ShippingAgent SLA_BREACH Path
# Step 1: Submit Order
#
# delivery_days=0 sets a same-day SLA — impossible for any carrier to meet.
# paid_price_cents=995 ($9.95) matches the normal route's workshop margin.
# No carrier delivers in 0 days, so SLA_BREACH is always triggered.
#
# The SLA rule in the system prompt reads:
#   "If no rate that costs at or below the customer paid price delivers within
#    N days, outcome MUST be SLA_BREACH."
#
# The agent must call find_alternate_warehouse before finalizing SLA_BREACH.
# Watch for it in the fulfillment namespace workflow history in Temporal UI.

set -e

echo "Submitting order with 1-day SLA and \$30 cap to trigger SLA_BREACH..."
echo "Workflow ID: sla-breach-123"
echo ""

xh PUT http://localhost:8080/api/v1/commerce-app/orders/sla-breach-123 \
  customerId="cust-002" \
  order:='{"orderId":"sla-breach-123","items":[{"itemId":"shirt-001","quantity":1}],"shippingAddress":{"street":"11 Wall St","city":"New York","state":"NY","postalCode":"10005","country":"US"},"selectedShipment":{"paidPriceCents":"995","currency":"USD","deliveryDays":0}}'

echo ""
echo "Order submitted"
echo "Next step: Run 2-capture-payment.sh"
