# Exercise 02 ShippingAgent 12-Slide Step Copy

## Slide 1

**Exercise activity:** 1. Pick a scenario

**Header:** Choose one agent path to inspect

**Subheader:** Each scenario creates a different recommendation outcome.

**What to do:**

1. Pick one track.
2. Run the matching wrapper script.
3. Capture the printed `ORDER_ID` and `CUSTOMER_ID`.

**Tracks:**

- Normal decision: `./scripts/run-valid-order.sh`
- Margin discovery: `./scripts/run-margin-spike.sh`
- SLA discovery: `./scripts/run-sla-breach.sh`

**Participant prompt:**

- What business risk is your scenario designed to expose?

## Slide 2

**Exercise activity:** 1. Pick a scenario

**Header:** Why this starts with scenarios

**Subheader:** The first agent launch story is discovery, not immediate process change.

**What to observe:**

- Normal track proves the agent can recommend without creating an exception.
- Margin track proves a low paid shipping price can surface `MARGIN_SPIKE`.
- SLA track proves an impossible delivery promise can surface `SLA_BREACH`.

**Design point:**

- We are using controlled inputs so participants can inspect one path deeply.
- The business question is not "can the agent ship orders?"
- The business question is "which exact orders leak margin or miss SLA?"

**Proof to find later:**

- `ShippingAgent` recommendation outcome.
- `margin_leak` or `sla_breach_days` on `fulfillment.Order`.

## Slide 3

**Exercise activity:** 2. Trace the order path

**Header:** Follow the workflow chain

**Subheader:** Before looking at model behavior, locate the deterministic orchestration path.

**What to do in Temporal UI:**

1. Open namespace `apps`; find `apps.Order` with workflow ID `ORDER_ID`.
2. Open namespace `processing`; find `processing.Order` with workflow ID `ORDER_ID`.
3. Open namespace `fulfillment`; find `fulfillment.Order` with workflow ID `ORDER_ID`.
4. In namespace `fulfillment`; find `ShippingAgent` with workflow ID `CUSTOMER_ID`.

**Path shape:**

- `apps.Order`
- `processing.Order`
- `fulfillment.Order`
- `ShippingAgent.recommendShippingOption`

## Slide 4

**Exercise activity:** 2. Trace the order path

**Header:** What this path tells us

**Subheader:** The agent is advisory; fulfillment still owns the order decision.

**What to observe:**

- `ShippingAgent` is not a per-order child workflow.
- It is a long-running per-customer workflow keyed by `CUSTOMER_ID`.
- Java `fulfillment.Order` calls the Python agent through Nexus.
- The Python Nexus handler uses UpdateWithStart to start or reuse the agent.

**Design point:**

- Per-customer workflow state supports cache reuse.
- Nexus keeps the cross-language boundary explicit.
- The order lifecycle still belongs to `fulfillment.Order`.

**Participant prompt:**

- Which workflow owns the order, and which workflow owns the advisory conversation?

## Slide 5

**Exercise activity:** 3. Inspect the agent boundary

**Header:** Inspect how the recommendation was produced

**Subheader:** Look for the harness events around the LLM call.

**What to do in `ShippingAgent` history:**

1. Find the `recommend_shipping_option` Update.
2. Find `build_system_prompt`.
3. Find `call_llm`.
4. Find tool calls such as `get_carrier_rates` and `get_location_events`.
5. For margin or SLA tracks, find `find_alternate_warehouse`.
6. Find `finalize_recommendation`.

**Proof checklist:**

- Prompt build is visible.
- Model call is visible.
- Tool requests and tool results are visible.
- Final recommendation is structured.

## Slide 6

**Exercise activity:** 3. Inspect the agent boundary

**Header:** What the harness proves

**Subheader:** Prompt guides the model; workflow enforces the process.

**What to observe:**

- Workflow pre-resolves inventory origin and verified destination.
- `call_llm` runs as an Activity, outside deterministic workflow code.
- Tool calls are limited to declared Activities and Nexus operations.
- `finalize_recommendation` is internal to the workflow.
- `MARGIN_SPIKE` and `SLA_BREACH` are rejected until `find_alternate_warehouse` has happened.

**Design point:**

- The LLM owns tradeoff reasoning across cost, SLA, speed, and risk.
- Workflow owns state, retries, timeouts, schemas, and non-negotiable gates.
- If the model owns too much, mandatory checks become prompt compliance.
- If workflow owns too much, shipping policy becomes a brittle `if/else` tree.

**Integration question:**

- A Temporal AI Integration is useful for standard agent loops.
- This exercise uses a custom dispatcher because the typed tool boundary and custom rejection behavior are part of what we need to teach.

## Slide 7

**Exercise activity:** 4. Inspect the fulfillment decision

**Header:** Return to `fulfillment.Order`

**Subheader:** Confirm where the recommendation becomes a business action.

**What to do:**

1. Open `fulfillment.Order` for `ORDER_ID`.
2. Find where it receives the `ShippingAgent` response.
3. Confirm the selected shipping option.
4. Confirm label printing.
5. Confirm inventory deduction.
6. For exception tracks, inspect Search Attribute upserts.

**Fields to connect:**

- Recommended option ID.
- Selected rate ID.
- Actual shipping price.
- Margin delta.
- SLA breach days, when present.

## Slide 8

**Exercise activity:** 4. Inspect the fulfillment decision

**Header:** Why fulfillment applies the recommendation

**Subheader:** The probabilistic recommendation is input to deterministic fulfillment code.

**What to observe:**

- `fulfillment.Order` verifies the recommended option exists in the returned options.
- It recomputes margin delta from the selected option and configured margin.
- It records `margin_leak` when the delta is positive.
- It records `sla_breach_days` for accepted SLA breach outcomes.
- It buys the label and deducts inventory after applying the recommendation.

**Design point:**

- The agent does not buy the label.
- The agent does not deduct inventory.
- The agent does not own the final business outcome.

**Facilitator line:**

- Advisory does not mean unaudited. The decision is applied by workflow code.

## Slide 9

**Exercise activity:** 5. Query the discovery data

**Header:** Query for risky orders

**Subheader:** Turn individual recommendations into an operational exception list.

**What to do in the `fulfillment` namespace:**

1. Run `margin_leak > 0`.
2. Run `margin_leak >= 500`.
3. Run `sla_breach_days > 0`.
4. Run `sla_breach_days >= 2`.
5. Run `margin_leak > 0 OR sla_breach_days > 0`.

**Then open one returned workflow and connect:**

- Search Attribute value.
- Selected shipping option.
- Agent recommendation.
- Tool facts used by the agent.

## Slide 10

**Exercise activity:** 5. Query the discovery data

**Header:** Why Search Attributes matter here

**Subheader:** Metrics give counts; Search Attributes give exact workflow executions.

**What to observe:**

- The query result is a concrete list of orders.
- Each order can be opened and audited.
- The recommendation can be traced back to tool calls and fulfillment state.
- Operations can review exact exceptions, not only dashboard aggregates.

**Design point:**

- This is the first safe business value of the agent.
- We can measure margin and SLA risk before adding new approval mechanics.
- Discovery is a lower-risk launch than immediate automated enforcement.

**Participant prompt:**

- Which exact order would you hand to operations for review?

## Slide 11

**Exercise activity:** 6. Open discussion: Where should HitL live?

**Header:** Discuss human approval ownership

**Subheader:** Approval is a workflow design decision, not just another prompt line.

**What to discuss:**

1. What is the human approving?
2. What must be re-verified after approval?
3. Which workflow owns the durable wait?
4. Where should cancellation and timeout behavior live?
5. Where should the approval audit trail live?

**Current constraint:**

- `fulfillment.Order` calls `ShippingAgent.recommendShippingOption` through synchronous Nexus.
- The operation timeout is 120 seconds.
- The Python handler waits for the `recommend_shipping_option` Update result.

## Slide 12

**Exercise activity:** 6. Open discussion: Where should HitL live?

**Header:** What the approval discussion reveals

**Subheader:** Long human waits change the caller contract.

**Option A: fulfillment owns the wait**

- Agent returns an outcome such as `MANUAL_APPROVAL_REQUIRED`.
- `fulfillment.Order` waits before label purchase.
- Fulfillment re-verifies rates, warehouse, inventory, and SLA after approval.

**Option B: agent owns an approval tool**

- Add an LLM tool backed by an Asynchronously Completed Activity.
- The agent waits for human input, then re-checks current context.
- The Nexus operation likely needs a pending/completion contract.

**Final takeaway:**

- Workflow owns durable process and enforcement.
- The LLM owns advisory reasoning.
- The harness makes the boundary visible, testable, and discussable.
