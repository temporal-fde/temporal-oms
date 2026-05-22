# Visual 04 - Final Fulfillment Order Architecture

**Status:** Draft visual brief
**Mermaid source:** [`../mermaid/04-final-fulfillment-order-architecture.mmd`](../mermaid/04-final-fulfillment-order-architecture.mmd)

## Job

Show the desired end state once fulfillment ownership has moved into `apps.Order` and
`fulfillment.Order`.

## Audience Takeaway

`fulfillment.Order` is the durable orchestration boundary for fulfillment. It owns validation,
inventory lifecycle, shipping recommendation application, label creation, inventory deduction, and
delivery status handling.

## Key Points

| Moment | Why It Matters |
|---|---|
| `validateOrder` runs early | Address validation and inventory hold can happen while processing runs. |
| `processing.Order` no longer sends fulfillment | Processing stays focused on validation and enrichment. |
| `fulfillment.Order` waits for `fulfillOrder` | The workflow is started early but does not ship until processing succeeds. |
| ShippingAgent recommends | Probabilistic reasoning is isolated in the agent. |
| `fulfillment.Order` decides | Business policy stays deterministic and auditable. |
| Delivery status is signaled | Fulfillment has a real lifecycle close instead of a one-way handoff. |

## Speaker Notes

This diagram should feel like the "aha" moment after the rollout visual. The final state is not
just V1 with Kafka swapped for Nexus. The ownership boundary changed: `apps.Order` coordinates the
order lifecycle, and `fulfillment.Order` owns durable fulfillment state.

Keep the ShippingAgent box small here. The next visual expands it.

