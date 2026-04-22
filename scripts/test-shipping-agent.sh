#!/usr/bin/env bash
set -euo pipefail

TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-localhost:7233}"
NAMESPACE="${TEMPORAL_NAMESPACE:-fulfillment}"
WORKFLOW_ID="${WORKFLOW_ID:-test-shipping-agent-001}"

temporal workflow start \
  --address "$TEMPORAL_ADDRESS" \
  --namespace "$NAMESPACE" \
  --type ShippingAgent \
  --task-queue fulfillment \
  --workflow-id "$WORKFLOW_ID" \
  --input '{"customer_id": "cust-123"}'

temporal workflow update execute \
  --address "$TEMPORAL_ADDRESS" \
  --namespace "$NAMESPACE" \
  --workflow-id "$WORKFLOW_ID" \
  --name calculate_shipping_options \
  --input '{
    "order_id": "order-001",
    "customer_id": "cust-123",
    "to_address": {
      "easypost": {
        "street1": "417 Montgomery St",
        "street2": "Floor 5",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94104",
        "country": "US"
      }
    },
    "items": [{"sku_id": "SKU-001", "quantity": 1}],
    "transit_days_sla": 3
  }'
