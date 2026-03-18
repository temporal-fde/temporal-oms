#!/bin/bash
# Scenario: Complete Invalid Order
# Step 3: Complete Manual Validation
# This resolves the validation failure through the support team workflow
# The support team has reviewed the order and provided corrections
#
# This script uses the processing-api REST service instead of temporal CLI,
# making it Kubernetes-ready and environment-agnostic.

set -e

ORDER_ID="invalid-order-123"
API_ENDPOINT="${PROCESSING_API_ENDPOINT:-http://localhost:8081}"

echo "✋ Resolving validation failure through manual correction..."
echo "Order ID: ${ORDER_ID}"
echo "API Endpoint: ${API_ENDPOINT}"
echo ""

# Call the processing-api REST endpoint to complete validation
response=$(curl -s -X POST \
  "${API_ENDPOINT}/api/v1/validations/${ORDER_ID}/complete" \
  -H "Content-Type: application/json")

# Check if the response indicates success (status field)
if echo "$response" | grep -q '"status":"accepted"'; then
  echo ""
  echo "✅ Validation corrected by support team"
  echo "Demo complete! Order can now proceed to fulfillment."
  echo "Check Temporal UI to see the complete order flow and support team interaction."
  exit 0
else
  echo ""
  echo "❌ Failed to complete validation"
  echo "Response: $response"
  exit 1
fi