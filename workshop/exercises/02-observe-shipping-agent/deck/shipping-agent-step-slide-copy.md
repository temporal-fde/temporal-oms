# Exercise 02 ShippingAgent Step Slide Copy

## Slide 1

**Exercise frame:** Before Step 1

**Header:** Today we are observing an agent inside fulfillment

**Subheader:** The exercise is not "watch the LLM." It is "trace the reliability harness around the LLM."

**Facilitator setup:**

- Exercise 01 moved new orders to `apps.Order -> fulfillment.Order`.
- Exercise 02 zooms into the AI-assisted shipping recommendation.
- `ShippingAgent` recommends.
- `fulfillment.Order` decides, records, prints the label, and deducts inventory.

**Prompt:**

- By the end, what proof would convince you the model helped without owning the whole business process?

## Slide 2

**Exercise frame:** Before Step 1

**Header:** The key design question

**Subheader:** What should be deterministic workflow, and what should be LLM reasoning?

**Deterministic workflow should own:**

- Request validation.
- Durable state.
- Retries and timeouts.
- Tool dispatch.
- Non-negotiable process gates.
- Search Attributes and audit trail.

**LLM reasoning should own:**

- Cost, speed, SLA, and risk tradeoff.
- Which optional facts to gather next.
- The structured shipping recommendation.
- The explanation attached to that recommendation.

**Facilitator line:**

- If the business cannot tolerate the model skipping a step, that step belongs in workflow code.

## Slide 3

**Exercise activity:** 1. Pick a scenario

**Header:** Pick the failure mode you want to inspect

**Subheader:** Each track is a different way to observe the same boundary.

**Scenario tracks:**

- Normal decision: the recommendation completes without `margin_leak` or `sla_breach_days`.
- Margin discovery: 1-cent paid shipping forces `MARGIN_SPIKE`.
- SLA discovery: same-day promise forces `SLA_BREACH`.

**Interesting topic in this step:**

- We are not asking everyone to generate every possible outcome.
- The workshop uses repeatable scenarios so each table can inspect one agent path deeply.
- The debrief recombines the paths into one shared architecture model.

**Ask participants:**

- Which business risk is your scenario designed to expose?

## Slide 4

**Exercise activity:** 1. Pick a scenario

**Header:** The first launch story is discovery

**Subheader:** Before changing the approval process, list the exact orders with shipping risk.

**Why these scenarios exist:**

- Margin track answers: are fulfillment-time rates worse than checkout assumptions?
- SLA track answers: are we missing promised delivery windows?
- Normal track answers: does the agent stay out of the way when there is no exception?

**Interesting topic in this step:**

- The agent launch starts as observability, not immediate automation of new approvals.
- That keeps the business process stable while making hidden shipping risk inspectable.

**Proof to look for later:**

- `margin_leak`
- `sla_breach_days`
- recommendation outcome in `ShippingAgent`

## Slide 5

**Exercise activity:** 2. Trace the order path

**Header:** Follow the order before inspecting the agent

**Subheader:** Start with the deterministic orchestration path.

**Path to trace:**

- `apps.Order` with workflow ID `ORDER_ID`
- `processing.Order` with workflow ID `ORDER_ID`
- `fulfillment.Order` with workflow ID `ORDER_ID`
- `ShippingAgent` with workflow ID `CUSTOMER_ID`

**Interesting topic in this step:**

- `ShippingAgent` is not a per-order child workflow.
- It is a long-running per-customer workflow.
- `fulfillment.Order` calls it through Nexus and receives a recommendation.

**Ask participants:**

- Which workflow owns the order lifecycle?
- Which workflow owns the advisory conversation?

## Slide 6

**Exercise activity:** 2. Trace the order path

**Header:** Why the agent is keyed by customer

**Subheader:** The workflow ID choice tells you what state the agent is allowed to remember.

**Decision made:**

- The Nexus handler uses UpdateWithStart.
- The `ShippingAgent` workflow ID is `CUSTOMER_ID`.
- Existing customer agents are reused.
- The cache key includes resolved origin, destination, items, and selected shipment context.

**Interesting topic in this step:**

- Per-customer agent state supports cache reuse across similar shipping requests.
- It does not make the agent the owner of order completion.
- The order still completes through `fulfillment.Order`.

**Proof:**

- `fulfillment.Order` ID is `ORDER_ID`.
- `ShippingAgent` ID is `CUSTOMER_ID`.

## Slide 7

**Exercise activity:** 2. Trace the order path

**Header:** Nexus is the language boundary

**Subheader:** Java fulfillment calls a Python agent as a domain operation.

**Decision made:**

- Java `fulfillment.Order` uses a Nexus service stub.
- The Python Nexus handler starts or reuses `ShippingAgent`.
- The Nexus request ID becomes the Update ID for idempotent retries.
- The current operation timeout is 120 seconds.

**Interesting topic in this step:**

- Nexus keeps the caller from knowing Python implementation details.
- UpdateWithStart keeps the agent workflow durable and reusable.
- The 120-second timeout matters later when discussing human approval.

**Ask participants:**

- Is this operation a quick recommendation, or a long-running approval process?

## Slide 8

**Exercise activity:** 3. Inspect the agent boundary

**Header:** Now inspect the harness, not just the answer

**Subheader:** The workflow history shows how the recommendation was produced.

**Find these events:**

- `build_system_prompt` LocalActivity.
- `call_llm` Activity.
- `get_carrier_rates` tool activity.
- `get_location_events` tool activity, when present.
- `find_alternate_warehouse`, for margin or SLA tracks.
- `finalize_recommendation`.

**Interesting topic in this step:**

- Temporal makes the agent loop observable.
- The model call is one event in a larger durable process.
- Tool results and rejection results are part of the audit trail.

## Slide 9

**Exercise activity:** 3. Inspect the agent boundary

**Header:** Pre-resolve facts before asking for judgment

**Subheader:** The first LLM turn should reason with concrete context.

**Decision made:**

- Workflow resolves inventory origin before the LLM loop.
- Workflow verifies destination before the LLM loop when needed.
- The task text includes EasyPost IDs, coordinates, timezone, items, and selected shipment context.

**Interesting topic in this step:**

- Address and inventory lookup are factual prerequisites.
- Keeping them deterministic reduces model wandering.
- The model spends reasoning budget on shipping tradeoffs, not basic plumbing.

**Ask participants:**

- Which facts were already known before `call_llm` happened?

## Slide 10

**Exercise activity:** 3. Inspect the agent boundary

**Header:** The prompt guides; the workflow enforces

**Subheader:** Business guidance and business invariants are not the same thing.

**Prompt guidance:**

- Margin rule.
- SLA rule.
- Rule priority.
- Risk rule.
- Mandatory actions for margin and SLA exceptions.

**Workflow enforcement:**

- Validate update input.
- Dispatch only declared tools.
- Require structured `finalize_recommendation`.
- Reject `MARGIN_SPIKE` or `SLA_BREACH` until alternate warehouse has been checked.

**Interesting topic in this step:**

- Prompt text tells the model what good behavior looks like.
- Workflow code defines what behavior is acceptable.

## Slide 11

**Exercise activity:** 3. Inspect the agent boundary

**Header:** Watch the deterministic gate

**Subheader:** The model can recommend a negative outcome, but it cannot skip the alternate-warehouse check.

**What to look for in margin or SLA tracks:**

- The model tries or prepares to finalize `MARGIN_SPIKE` or `SLA_BREACH`.
- If `find_alternate_warehouse` has not happened, workflow appends a `REJECTED` tool result.
- The model calls `find_alternate_warehouse`.
- A later `finalize_recommendation` is accepted.

**Interesting topic in this step:**

- The recommendation is probabilistic.
- The prerequisite is deterministic.
- This is the central harness pattern in the exercise.

**Facilitator line:**

- The workflow does not need to choose the best rate to enforce the process contract.

## Slide 12

**Exercise activity:** 3. Inspect the agent boundary

**Header:** What happens if we get the boundary wrong?

**Subheader:** The failure mode depends on which side owns too much.

**Too much LLM authority:**

- Mandatory checks become prompt compliance.
- Exceptions can be finalized before alternatives are checked.
- Business decisions may only exist in prose.
- Retries can repeat tool calls or branch differently.

**Too much workflow authority:**

- Cost, SLA, speed, and risk become a brittle `if/else` tree.
- Every policy adjustment becomes a deploy.
- The "agent" becomes a wrapper around hard-coded policy.

**Tie back to current step:**

- Use the history you are inspecting to identify which side owns each decision.

## Slide 13

**Exercise activity:** 3. Inspect the agent boundary

**Header:** Temporal AI Integration or custom dispatcher?

**Subheader:** The right answer depends on how much of the boundary you need to own.

**Use a Temporal AI Integration when:**

- The agent pattern is standard.
- Tool calls map cleanly to Temporal work.
- You want less custom loop infrastructure.
- Finalization policy is simple.

**Use a custom dispatcher when:**

- Tool calls cross languages, task queues, and Nexus endpoints.
- Tool schemas are domain contracts.
- You need custom rejection behavior.
- You want the workshop to expose every enforcement point.

**Tie back to current step:**

- Participants can see the custom dispatcher in the history as typed tool calls and tool results.

## Slide 14

**Exercise activity:** 3. Inspect the agent boundary

**Header:** The dispatcher is deliberately small

**Subheader:** It maps model tool names to durable Temporal operations.

**Tool mapping:**

- `get_carrier_rates`: Activity on `fulfillment-shipping`.
- `get_location_events`: Activity on `agents`.
- `find_alternate_warehouse`: Nexus operation to integrations.
- `finalize_recommendation`: internal workflow tool.

**Interesting topic in this step:**

- The model does not get arbitrary function access.
- Unknown tools fail.
- Inputs are parsed into declared schemas.
- Domain services stay behind contracts.

**Facilitator line:**

- The dispatcher is infrastructure. The important design is the boundary it preserves.

## Slide 15

**Exercise activity:** 4. Inspect the fulfillment decision

**Header:** Return to `fulfillment.Order`

**Subheader:** This is where the recommendation becomes a business action.

**Confirm:**

- `ShippingAgent` returns a recommendation and options.
- `fulfillment.Order` finds the recommended option by ID.
- `fulfillment.Order` computes margin delta.
- `fulfillment.Order` prints the label.
- `fulfillment.Order` deducts inventory.

**Interesting topic in this step:**

- The agent does not buy the label.
- The agent does not deduct inventory.
- The deterministic fulfillment workflow applies the recommendation.

**Ask participants:**

- What would break if the agent directly purchased the label?

## Slide 16

**Exercise activity:** 4. Inspect the fulfillment decision

**Header:** The harness enforces business rules after the recommendation too

**Subheader:** Fulfillment records the outcome in workflow state and visibility.

**Fulfillment enforcement:**

- Recommended option must exist in the returned options.
- Margin delta is recomputed from the selected option and configured margin.
- `margin_leak` is upserted when delta is positive.
- `sla_breach_days` is upserted for an accepted SLA breach.

**Interesting topic in this step:**

- The model can recommend an outcome.
- Fulfillment independently computes the operational facts it records.
- The business gets queryable evidence, not just model reasoning.

## Slide 17

**Exercise activity:** 5. Query the discovery data

**Header:** Turn recommendations into an exception list

**Subheader:** Search Attributes make individual risky orders inspectable.

**Queries to run:**

- `margin_leak > 0`
- `margin_leak >= 500`
- `sla_breach_days > 0`
- `sla_breach_days >= 2`
- `margin_leak > 0 OR sla_breach_days > 0`

**Interesting topic in this step:**

- Metrics tell you how often a problem happens.
- Search Attributes show which workflows had the problem.
- Temporal UI connects the query result back to the full decision history.

**Ask participants:**

- Which exact order would you hand to operations for review?

## Slide 18

**Exercise activity:** 5. Query the discovery data

**Header:** Connect visibility back to the recommendation

**Subheader:** Every query result should be explainable from history.

**For one returned workflow, trace:**

- Search Attribute value on `fulfillment.Order`.
- Selected shipping option.
- `ShippingAgent` recommendation.
- Tool facts the model used.
- Any `REJECTED` finalization attempt.
- Alternate warehouse check, when applicable.

**Interesting topic in this step:**

- This is where probabilistic recommendation becomes operationally governable.
- You can inspect the exact order, not only aggregate dashboards.

## Slide 19

**Exercise activity:** 6. Open discussion: Where should HitL live?

**Header:** Human approval is not just another prompt instruction

**Subheader:** A human wait changes workflow ownership and the Nexus contract.

**Current implementation constraint:**

- `fulfillment.Order` calls `ShippingAgent.recommendShippingOption` through synchronous Nexus.
- The operation timeout is 120 seconds.
- The Python handler waits for the `recommend_shipping_option` Update result.

**Interesting topic in this step:**

- A minutes- or hours-long approval does not fit the current quick recommendation operation.
- The design question is which workflow owns the durable wait and audit trail.

**Ask participants:**

- What exactly is the human approving?

## Slide 20

**Exercise activity:** 6. Open discussion: Where should HitL live?

**Header:** Option A: fulfillment owns the approval wait

**Subheader:** The agent recommends an exception path; fulfillment owns the business hold.

**Shape:**

- Add an outcome such as `MANUAL_APPROVAL_REQUIRED`.
- `ShippingAgent` returns quickly.
- `fulfillment.Order` waits for approval before label purchase.
- Fulfillment re-verifies rates, warehouse, inventory, and SLA after approval.

**Tradeoff:**

- Business hold stays with the workflow that owns label purchase and inventory.
- The original agent context may be stale when approval arrives.

**Ask participants:**

- What must fulfillment re-check before buying the label later?

## Slide 21

**Exercise activity:** 6. Open discussion: Where should HitL live?

**Header:** Option B: agent owns an approval tool

**Subheader:** The model can wait for approval, then continue reasoning with fresh facts.

**Shape:**

- Add an LLM tool backed by an Asynchronously Completed Activity.
- The agent waits for human input.
- After approval, the agent can re-check warehouse, rates, SLA, and risk.
- The caller likely needs a pending/completion contract instead of a 120-second synchronous call.

**Tradeoff:**

- The agent loop can continue with updated context.
- The order workflow must know how to observe or resume after a pending recommendation.

**Ask participants:**

- Should the caller wait, receive `PENDING`, or be signaled later?

## Slide 22

**Exercise close:** After Step 6

**Header:** What the exercise should make clear

**Subheader:** The agent is useful because the boundary is explicit.

**Takeaways:**

- Workflow code owns durable state, enforcement, retries, and audit.
- The LLM owns advisory tradeoff reasoning.
- Tools are typed Temporal operations, not arbitrary callbacks.
- `fulfillment.Order` applies the recommendation.
- Search Attributes turn agent findings into operational discovery data.
- Human approval is a separate workflow design decision.

**Final prompt:**

- Which part of this system would you be comfortable changing with a prompt, and which part needs code?
