# Processing Bounded Context

## Ubiquitous Language

- **Order Processing** - Enriching order items and coordinating payment completion
- **PIMS (Product Information Management System)** - External system for product enrichment
- **SKU ID** - Stock Keeping Unit identifier
- **Brand Code** - Product brand identifier
- **Payment Completion** - Signal that payment has been successfully processed

## Responsibilities

- Enrich order items with SKU ID and Brand Code from PIMS
- Wait for payment completion via Update
- Trigger fulfillment workflow via Nexus when payment is complete
- Trigger fraud check via Nexus when payment is complete
- Rate-limit PIMS API calls (150 RPS)

## NOT Responsible For

- Order orchestration (apps namespace)
- Fulfillment execution (fulfillments namespace)
- Payment processing

## Integration Points

- **Apps** - Nexus: Receives Order creation, sends notifications
- **Fulfillments** - Nexus: Trigger fulfillment
- **PIMS API** - Activity: Enrich product data 
- **Support Team** - Support manually corrects order items
- **Commerce App** - Activity for validating orders and sending original orders via Webhooks.

## Key Aggregates

- Order Workflow (Aggregate Root)