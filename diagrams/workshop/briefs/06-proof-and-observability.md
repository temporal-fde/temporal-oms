# Visual 06 - Proof and Observability

**Status:** Draft visual brief
**Mermaid source:** [`../mermaid/06-proof-and-observability.mmd`](../mermaid/06-proof-and-observability.mmd)

## Job

Give participants a concrete checklist for proving the migration and the agent path are working.

## Audience Takeaway

The architecture is observable from workflow history, inputs, Search Attributes, and runtime
fixtures. Participants should leave knowing where to look for evidence.

## Demo Checklist

| Check | Expected Evidence |
|---|---|
| Legacy order still works | Kafka fulfillment record exists for old-path order. |
| New order avoids Kafka | No Kafka fulfillment record for `apps v2` order. |
| Routing slip is visible | `ProcessOrderRequest.options.send_fulfillment=false` appears in processing history/input. |
| Durable fulfillment exists | `fulfillment.Order` history shows `validateOrder`, inventory hold, `fulfillOrder`, and terminal work. |
| Agent path is visible | `ShippingAgent` history shows LLM activity calls and tool activity execution. |
| Margin/SLA cases are inspectable | `margin_leak` or `sla_breach_days` appears when the scenario triggers it. |

## Speaker Notes

Use this as the final debrief visual or as a handout slide before participants inspect the UI.
The point is to make the migration falsifiable. If the architecture is working, participants can
prove it from the system itself rather than trusting the slide deck.

This also reinforces why the target design is easier to operate: the important business and
rollout facts are visible in Temporal histories and attributes.

