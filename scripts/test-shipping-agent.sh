#!/usr/bin/env bash
set -euo pipefail

TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-localhost:7233}"
NAMESPACE="${TEMPORAL_NAMESPACE:-fulfillment}"
WORKFLOW_ID="${WORKFLOW_ID:-cust-123}"

temporal workflow start \
  --address "$TEMPORAL_ADDRESS" \
  --namespace "$NAMESPACE" \
  --type ShippingAgent \
  --task-queue agents \
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
        "id": "adr_dest_nyc_01",
        "street1": "11 Wall St",
        "city": "New York",
        "state": "NY",
        "zip": "10005",
        "country": "US"
      }
    },
    "items": [{"sku_id": "ELEC-001", "quantity": 1}],
    "selected_shipment": {
      "paid_price": {"currency": "USD", "units": 995},
      "easypost": {
        "shipment_id": "shp_adr_wh_east_01_to_adr_dest_nyc_01",
        "selected_rate": {
          "id": "rate_wh_east_01_nyc_ground",
          "delivery_days": 3
        }
      }
    }
  }'
