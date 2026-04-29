#!/bin/bash
# Scenario: SLA Breach — ShippingAgent SLA_BREACH Path
# Step 2: Capture Payment
#
# Payment triggers order processing. Once enriched, fulfillment.Order calls
# ShippingAgent via Nexus. Watch the fulfillment namespace in Temporal UI:
#
#   get_carrier_rates       — fetches fixture-backed rates under the workshop margin
#   get_location_events     — origin + destination SCRM (concurrent)
#   finalize_recommendation — REJECTED (find_alternate_warehouse not called yet)
#   find_alternate_warehouse — returns empty (no alternate in seed data)
#   finalize_recommendation — ACCEPTED with outcome=SLA_BREACH
#
# SLA_BREACH: no fixture-backed rate can satisfy the same-day delivery SLA.

set -e

echo "Capturing payment for sla-breach-123..."
echo ""

xh POST http://localhost:8080/api/v1/payments-app/orders \
  customerId="cust-002" \
  rrn="payment-sla-breach" \
  amountCents=9999 \
  metadata:='{"orderId":"sla-breach-123"}'

echo ""
echo "Payment captured — order is now processing"
echo ""
echo "Watch Temporal UI (fulfillment namespace) for:"
echo "  ShippingAgent workflow ID: cust-002"
echo "  Outcome: SLA_BREACH after find_alternate_warehouse returns empty"
echo ""
echo "Note: delivery_days=0 with paid_price_cents=995 — fixture rates stay under"
echo "the workshop margin, but none can satisfy same-day delivery."
