# Visual 01 - Current Kafka Fulfillment Path

**Status:** Draft visual brief
**Mermaid source:** [`../mermaid/01-current-kafka-path.mmd`](../mermaid/01-current-kafka-path.mmd)

## Job

Establish the V1 baseline quickly. Participants should understand that fulfillment is currently a
fire-and-forget side effect from `processing.Order`, not a durable lifecycle.

## Audience Takeaway

V1 does get an order to a fulfillment handoff, but the handoff is not a durable fulfillment
orchestration model. Once `processing.Order` publishes to Kafka, the order lifecycle has little
visibility or control over what happens next.

## Callouts

| Gap | What to Say |
|---|---|
| No durable fulfillment state | Fulfillment state is stored in memory, so restart means state loss. |
| No compensation | Failed fulfillment cannot reliably release inventory holds. |
| No cancellation | There is no durable in-flight workflow to signal. |
| Late address validation | Address failures surface after payment and processing work. |
| Dead-end handoff | The order lifecycle cannot reason over fulfillment outcomes. |

## Speaker Notes

Start with the simplest possible explanation: `apps.Order` owns the customer-facing order lifecycle,
but V1 fulfillment ownership effectively falls out of `processing.Order` as a side effect.

Do not introduce `ShippingAgent` yet. The first problem is not "no AI"; the first problem is that
fulfillment is not modeled as a durable lifecycle.

## Slide Treatment

This should be visually plain. Use gray for the V1 path and orange callouts for the gaps. Avoid
making Kafka look like the villain; the issue is that Kafka plus in-memory state is being used as a
fulfillment lifecycle boundary.

