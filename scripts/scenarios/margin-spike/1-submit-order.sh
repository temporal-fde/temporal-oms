#!/bin/bash
# Scenario: Margin Spike — ShippingAgent Alternate Warehouse Path
# Step 1: Submit Order
#
# paid_price_cents=1 (1 cent) guarantees every real EasyPost rate exceeds the
# customer paid price, triggering MARGIN_SPIKE in the ShippingAgent.
# The agent must call find_alternate_warehouse before finalizing — watch for it
# in the fulfillment namespace workflow history in Temporal UI.

set -e

echo "Submitting order with 1-cent paid price to trigger MARGIN_SPIKE..."
echo "Workflow ID: margin-spike-123"
echo ""

xh PUT http://localhost:8080/api/v1/commerce-app/orders/margin-spike-123 \
  customerId="cust-001" \
  order:='{"orderId":"margin-spike-123","items":[{"itemId":"shirt-001","quantity":1}],"shippingAddress":{"street":"388 Townsend St","city":"San Francisco","state":"CA","postalCode":"94107","country":"US"},"selectedShipment":{"paidPriceCents":"1","currency":"USD"}}'

echo ""
echo "Order submitted"
echo "Next step: Run 2-capture-payment.sh"
