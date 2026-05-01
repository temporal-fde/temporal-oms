# Visual 02 - Motivation Gap Map

**Status:** Draft visual brief
**Mermaid source:** [`../mermaid/02-motivation-gap-map.mmd`](../mermaid/02-motivation-gap-map.mmd)

## Job

Translate the V1 pains into concrete architectural requirements. This is the bridge between
"current state is fragile" and "the target state needs Temporal workflows, Nexus, Worker Versioning,
and an agent."

## Audience Takeaway

Each architectural move solves a specific gap. The final design is not a rip-and-replace for its own
sake; it is a set of targeted changes around durability, ownership, decisioning, and visibility.

## Message Map

| Gap | Architectural Response |
|---|---|
| Kafka plus `HashMap` loses fulfillment state | `fulfillment.Order` becomes the durable lifecycle. |
| Fulfillment cannot be cancelled or compensated | Signals and detached inventory release are modeled in the workflow. |
| Address issues surface late | `apps.Order` starts `fulfillment.Order` early with `validateOrder`. |
| Rates are stale by the time the order ships | `fulfillment.Order` revalidates shipping during fulfillment. |
| Carrier choice ignores disruption and warehouse context | `ShippingAgent` reasons across rates, inventory origin, and location events. |
| Margin and SLA issues are hard to inspect | `margin_leak` and `sla_breach_days` become visible workflow attributes. |

## Speaker Notes

This is where the workshop can make a pragmatic point: the architecture changes are separable.
Durability and ownership move into `fulfillment.Order`; shipping optimization moves into the
agent; rollout safety comes from Worker Versioning.

That separation matters because it keeps the AI part from becoming the owner of business rules.

