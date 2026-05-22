#!/bin/bash
# Scenario: Complete Invalid Order
# Step 3: Complete Manual Validation
# This resolves the validation failure through the support team workflow
# The support team has reviewed the order and provided corrections
#
# This script uses the processing-api REST service instead of temporal CLI,
# making it Kubernetes-ready and environment-agnostic.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../_lib.sh"
scenario_resume "$SCRIPT_DIR"

API_ENDPOINT="${PROCESSING_API_ENDPOINT:-http://localhost:8070}"
MAX_ATTEMPTS="${VALIDATION_COMPLETE_MAX_ATTEMPTS:-12}"
RETRY_SECONDS="${VALIDATION_COMPLETE_RETRY_SECONDS:-5}"

echo "✋ Resolving validation failure through manual correction..."
echo "Order ID: ${ORDER_ID}"
echo "Customer ID: ${CUSTOMER_ID}"
echo "API Endpoint: ${API_ENDPOINT}"
echo ""

attempt=1
while true; do
  # Call the processing-api REST endpoint to complete validation.
  response=$(curl -s -w "\n%{http_code}" -X POST \
    "${API_ENDPOINT}/api/v1/validations/${ORDER_ID}/complete" \
    -H "Content-Type: application/json")
  http_status="${response##*$'\n'}"
  response_body="${response%$'\n'*}"

  if [ "$http_status" = "202" ]; then
    break
  fi

  if [ "$http_status" != "409" ] || [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo ""
    echo "❌ Failed to complete validation"
    echo "HTTP status: ${http_status}"
    echo "Response: ${response_body}"
    exit 1
  fi

  echo "Validation request is not ready yet; retrying in ${RETRY_SECONDS}s (${attempt}/${MAX_ATTEMPTS})..."
  sleep "$RETRY_SECONDS"
  attempt=$((attempt + 1))
done

# Check if the response indicates success. The processing API returns 202 with
# an empty body on success.
echo ""
echo "✅ Validation corrected by support team"
echo "Demo complete! Order can now proceed to fulfillment."
echo "Check Temporal UI to see the complete order flow and support team interaction."
