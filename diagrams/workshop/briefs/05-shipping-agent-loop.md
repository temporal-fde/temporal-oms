# Visual 05 - ShippingAgent Loop

**Status:** Draft visual brief
**Mermaid source:** [`../mermaid/05-shipping-agent-loop.mmd`](../mermaid/05-shipping-agent-loop.mmd)

## Job

Explain how agentic behavior is attached to the durable fulfillment path without letting the agent
own final business decisions.

## Audience Takeaway

The agent is a long-running Temporal workflow. Claude chooses tool calls, Temporal runs those tools
as activities, and the result is a recommendation that `fulfillment.Order` evaluates.

## Key Concepts to Emphasize

| Concept | Workshop Explanation |
|---|---|
| Long-running workflow | The agent caches repeated recommendations per customer. |
| Tool calls as activities | LLM tool use maps to visible, durable Temporal activity execution. |
| Concurrent tools | Multiple LLM tool calls in one response can run as concurrent activities. |
| Structured finalization | `finalize_recommendation` avoids fragile JSON text parsing. |
| Guardrails in workflow code | The workflow rejects premature `MARGIN_SPIKE` or `SLA_BREACH` without alternate warehouse lookup. |
| Recommendation boundary | The agent recommends; `fulfillment.Order` decides. |

## Speaker Notes

This is the safest place to use the phrase "agentic workflow." The agent is not a chatbot bolted to
the side of the system. It is a Temporal workflow whose probabilistic step is wrapped in durable,
observable control flow.

Be explicit that `fulfillment.Order` receives a `ShippingRecommendation`, not an instruction it
blindly follows.
