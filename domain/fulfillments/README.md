# Fulfillments Bounded Context

> Planned, not yet implemented.


## Ubiquitous Language

- **Fulfillment** - Process of finding inventory and arranging shipping
- **AI Agent** - LLM-powered workflow using Pydantic plugin
- **Shipping Rate** - Cost and speed of shipping option
- **Inventory Service** - External service for finding closest item provider
- **Allocation** - Assignment of inventory to an order

## Responsibilities

- Find fastest and cheapest shipping rates using LLM
- Locate closest inventory provider for each item
- Allocate inventory to orders
- Generate Kafka messages for order-fulfillment topic
- Optimize shipping costs and delivery times

## NOT Responsible For

- Order orchestration (apps namespace)
- Order processing (processing namespace)
- Fraud detection (risk namespace)
- Payment processing

## Integration Points

- **Apps** - Nexus: Receives fulfillment requests
- **Processing** - Nexus: Triggered by payment completion
- **Inventory Service** - Activity: Find closest provider
- **Kafka** - Output: order-fulfillment topic

## Key Aggregates

- Order Fulfillment (Aggregate Root)