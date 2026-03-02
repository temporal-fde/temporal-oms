# Apps Bounded Context

## Ubiquitous Language

- **CompleteOrder** - The top-level orchestration workflow that coordinates order completion across all domains
- **Order Aggregate** - The root aggregate representing an order's lifecycle
- **UpdateWithStart** - Temporal pattern for accumulating data from multiple sources
- **Nexus Operation** - Cross-namespace communication mechanism

## Responsibilities

- Orchestrate order completion across multiple namespaces
- Accumulate data from commerce-app and payments-app webhooks
- Coordinate creation of Orders in processing, risk, and fulfillments namespaces
- Manage order cancellation across all domains
- Track customer orders via Search Attributes

## NOT Responsible For

- Order processing logic (processing namespace)
- Fulfillment operations (fulfillments namespace)
- Payment processing details
- Item enrichment

## Integration Points

- **Processing** - Nexus: Start Order workflow
- **Risk** - Nexus: Start fraud check workflow
- **Fulfillments** - Nexus: Start fulfillment workflow
- **External APIs** - REST endpoints for commerce-app and payments-app webhooks

## Key Aggregates

- CompleteOrder Workflow (Aggregate Root)

## Events Published

- OrderCreated
- OrderCancelled
- OrderCompleted

## Events Subscribed

- CommerceDataSubmitted (from webhook)
- PaymentDataSubmitted (from webhook)
