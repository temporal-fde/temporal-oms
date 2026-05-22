#!/bin/bash
# Scenario: Complete Valid Order
# Step 1: Submit Order (Valid)
# This submits an order that will pass all validation
# The order ID does NOT contain "invalid", so it will pass validation checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_lib.sh"
scenario_begin "$SCRIPT_DIR"

ORDER_JSON="$(scenario_order_json "11 Wall St" "New York" "NY" "10005" "995" "5")"

echo "📋 Submitting VALID order for processing..."
echo "Workflow ID: ${ORDER_ID}"
echo "Customer ID: ${CUSTOMER_ID}"
echo "Note: This order will pass validation and proceed automatically"
echo "Run context: ${SCENARIO_CONTEXT_FILE}"
echo ""

xh PUT "http://localhost:8080/api/v1/commerce-app/orders/${ORDER_ID}" \
  customerId="${CUSTOMER_ID}" \
  order:="${ORDER_JSON}"

echo ""
echo "✅ Order submitted"
echo "Next step: Run 2-capture-payment.sh"
