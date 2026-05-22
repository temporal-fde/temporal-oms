# Exercise 02 ShippingAgent Preamble Observation Slide

## Slide

**Header:** Goals in this agent implementation

**Subheader:** The model is useful because the workflow keeps responsibilities explicit.

**Observations:**

- Simple recommendation cache: per-customer workflow state reuses recent decisions for the same origin, destination, items, and selected-shipment context.
- Explicit tool dispatch: the small dispatcher maps model tool names to typed Activities and Nexus operations, so tool execution is visible and bounded.
- Workflow before ReAct: origin, destination, cache lookup, retries, and hard gates stay in workflow code so LLM calls are spent on shipping judgment, not plumbing.
- Structured finalization: `finalize_recommendation` makes the answer typed data instead of prose that must be parsed.
- Deterministic guardrails: `MARGIN_SPIKE` and `SLA_BREACH` are rejected until alternate warehouse search has happened.

