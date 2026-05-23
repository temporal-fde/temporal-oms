# Exercise 02 ShippingAgent Slide Copy

## Slide 1

**Header:** What are we really observing in the ShippingAgent exercise?

**Subheader:** The agent is a recommendation loop inside a deterministic fulfillment harness.

**Prompt:**

- Which decisions happened before the model saw the task?
- Which decisions does the model actually own?
- Where does fulfillment keep final authority?
- What proof in Temporal UI would convince you the boundary is real?

## Slide 2

**Header:** The split is the design

**Subheader:** Durable workflow owns process. The LLM owns tradeoff reasoning.

**Workflow owns:**

- Order state, validation, timeouts, retries, and cache TTL.
- Origin and destination resolution before the LLM loop.
- Tool dispatch through declared Activities and Nexus operations.
- Acceptance or rejection of the final recommendation.
- Fulfillment Search Attributes for business visibility.

**LLM owns:**

- Which factual tools to call next after seeing current observations.
- How to weigh cost, SLA, speed, and location risk.
- The structured recommendation outcome and reasoning.

## Slide 3

**Discussion prompt:** What is workflow and what is model reasoning?

**Header:** Ask code to do facts; ask the model to do judgment

**Subheader:** If the branch is a crisp invariant, make it workflow code.

**Deterministic workflow work:**

- Validate request shape.
- Resolve inventory origin and verified destination.
- Run the LLM call as an Activity.
- Dispatch only declared tools.
- Require alternate-warehouse search before accepting negative outcomes.
- Confirm the recommended option exists before fulfillment applies it.

**LLM reasoning work:**

- Decide whether carrier rates and risk events are enough context.
- Decide whether to inspect origin and destination risk.
- Choose among acceptable rates.
- Recommend `PROCEED`, `CHEAPER_AVAILABLE`, `FASTER_AVAILABLE`, `MARGIN_SPIKE`, or `SLA_BREACH`.

**Facilitator line:**

- The question is not "can the model do this?" The question is "does the business need this step to be replayable, testable, and non-negotiable?"

## Slide 4

**Discussion prompt:** What happens if we get the split wrong?

**Header:** The wrong boundary creates the wrong failure mode

**Subheader:** Too much model authority and too much workflow authority fail differently.

**If too much lives in the LLM:**

- Mandatory checks become prompt compliance instead of process guarantees.
- The model can finalize a margin or SLA exception before checking alternatives.
- Structured decisions can collapse into prose.
- Retries can repeat expensive tools or branch differently.
- Business decisions may be visible only in provider logs.

**If too much lives in workflow code:**

- Cost, speed, SLA, and risk become a brittle `if/else` tree.
- Every policy adjustment becomes a deploy.
- The "agent" becomes a template wrapper around hard-coded policy.
- New outcomes require touching orchestration code instead of changing advisory behavior.

## Slide 5

**Header:** Why use a real ReAct loop here?

**Subheader:** The alternate-warehouse branch only exists after the first facts are known.

**Reasoning path:**

- Workflow supplies concrete origin, destination, items, and selected shipment context.
- The model calls carrier and risk tools to gather facts.
- If rates fail margin or SLA, the model should call `find_alternate_warehouse`.
- The model may then re-check rates and finalize.

**Decision made:**

- Do not pre-code every branch of the shipping policy tree.
- Let the model reason over the current facts.
- Keep mandatory process gates in the workflow.

## Slide 6

**Header:** Temporal is the reliability harness

**Subheader:** The agent loop is durable execution, not a loose Python `while` loop.

**Harness pieces:**

- `build_system_prompt` is a LocalActivity, so prompt construction is visible in history.
- `call_llm` is an Activity, so vendor calls stay outside deterministic workflow code.
- Tool calls run as Activities or Nexus operations with timeouts and retries.
- Conversation state lives in workflow history.
- Completed tools are not re-executed after a worker crash.

**Proof:**

- Temporal UI shows the prompt build, LLM calls, tool results, rejection results, and final recommendation.

## Slide 7

**Discussion prompt:** Temporal AI Integration or custom dispatcher?

**Header:** Use the integration when it fits; own the dispatcher when the boundary matters

**Subheader:** This exercise rolls a small dispatcher because the tool boundary is part of the lesson.

**A Temporal AI Integration is attractive when:**

- The agent pattern is standard.
- Tool calls map cleanly to regular Temporal work.
- You do not need much custom policy around finalization.
- You want less infrastructure code around the LLM loop.

**A custom dispatcher is useful here because:**

- Tools cross Python, Java, task queues, and Nexus endpoints.
- Tool inputs and outputs are typed with proto/Pydantic contracts.
- The workflow needs custom `REJECTED` tool results.
- Participants need to see exactly where the harness enforces process.

**Key phrase:**

- The dispatcher is not the business policy. It is a typed adapter from LLM tool calls to durable Temporal work.

## Slide 8

**Header:** The dispatcher is intentionally boring

**Subheader:** Tool registration maps names to typed requests and Temporal calls.

**Tool choices:**

- `get_carrier_rates` is an Activity on the `fulfillment-shipping` task queue.
- `get_location_events` is an Activity on the `agents` task queue.
- `find_alternate_warehouse` is a Nexus operation to the integrations endpoint.
- `finalize_recommendation` is internal to the workflow, not an external integration.

**Risk mitigation:**

- The LLM never receives arbitrary function access.
- Unknown tool names fail as non-retryable workflow errors.
- Tool input is parsed into declared schemas.
- Domain services remain behind their own contracts.

## Slide 9

**Header:** The model can recommend; it cannot skip the gate

**Subheader:** Negative outcomes are rejected until the alternate-warehouse check has happened.

**Workflow contract:**

- If the model finalizes `MARGIN_SPIKE` or `SLA_BREACH` before `find_alternate_warehouse`, the workflow appends a `REJECTED` tool result.
- The loop continues.
- The model must call `find_alternate_warehouse`.
- A later final recommendation can be accepted.

**What participants should see:**

- First `finalize_recommendation` can be rejected.
- `find_alternate_warehouse` runs.
- Second `finalize_recommendation` is accepted.

**Takeaway:**

- The recommendation is probabilistic. The process prerequisite is deterministic.

## Slide 10

**Header:** Business rules live at two levels

**Subheader:** Policy guidance is prompt. Process invariants are code.

**Prompt guidance:**

- Margin rule.
- SLA rule.
- Rule priority.
- Risk rule.
- Mandatory actions for margin and SLA exceptions.

**Workflow enforcement:**

- Validate update input.
- Dispatch only declared tools.
- Require alternate warehouse before accepted negative outcome.
- Require structured `finalize_recommendation`.
- Track all options seen across primary and alternate rate calls.

**Fulfillment enforcement:**

- Apply the recommendation to a concrete shipping option.
- Compute margin delta against configured shipping margin.
- Upsert `margin_leak` and `sla_breach_days`.
- Print the label and deduct inventory only after selection.

## Slide 11

**Header:** Why the agent is per-customer

**Subheader:** `ShippingAgent` is a long-running workflow keyed by `CUSTOMER_ID`, not `ORDER_ID`.

**Decision made:**

- The Nexus handler uses UpdateWithStart.
- The workflow ID is the customer ID.
- Existing customer agents are reused.
- The cache key includes origin, destination, items, and selected shipment context.

**Tradeoff:**

- This supports reuse and cache behavior across similar requests.
- It requires idempotent update IDs.
- It keeps order completion authority in `fulfillment.Order`, not the agent.

**Proof:**

- `fulfillment.Order` workflow ID is `ORDER_ID`.
- `ShippingAgent` workflow ID is `CUSTOMER_ID`.

## Slide 12

**Header:** Why Nexus is the caller boundary

**Subheader:** `fulfillment.Order` calls the agent like a domain operation, not a Python function.

**Decision made:**

- Java `fulfillment.Order` uses a Nexus service stub.
- The Python Nexus handler starts or reuses `ShippingAgent`.
- The Nexus request ID becomes the Update ID for idempotent retries.
- The current operation timeout is 120 seconds.

**Tradeoff:**

- The boundary is clean across languages and task queues.
- The caller can stay in fulfillment domain code.
- Long human approval waits do not fit the current synchronous operation contract.

## Slide 13

**Header:** Pre-resolve facts before asking for judgment

**Subheader:** The first LLM turn should reason with concrete addresses, not discover basic context.

**Decision made:**

- Inventory origin is resolved before the LLM loop.
- Destination is verified before the LLM loop when needed.
- The task text includes EasyPost IDs, coordinates, timezone, items, and selected shipment context.

**Why it matters:**

- The model can request carrier rates and location events immediately.
- Address validation stays deterministic and auditable.
- The model spends tokens on the shipping decision, not plumbing.

## Slide 14

**Header:** The final decision stays in `fulfillment.Order`

**Subheader:** The label purchase happens after fulfillment applies the recommendation.

**Proof path:**

- `ShippingAgent` returns a recommendation and available options.
- `fulfillment.Order` finds the recommended option by ID.
- `fulfillment.Order` computes margin delta.
- `fulfillment.Order` records Search Attributes.
- `fulfillment.Order` prints the label and deducts inventory.

**Key phrase:**

- Advisory does not mean unaudited. The recommendation is input to a deterministic fulfillment decision.

## Slide 15

**Header:** Search Attributes are the first launch story

**Subheader:** The first business value is discovery, not immediate process change.

**Queries:**

- `margin_leak > 0`
- `margin_leak >= 500`
- `sla_breach_days > 0`
- `sla_breach_days >= 2`
- `margin_leak > 0 OR sla_breach_days > 0`

**Why Search Attributes:**

- Metrics show counts.
- Search Attributes list the exact orders.
- Temporal UI connects the order, the recommendation, and the business exception.

## Slide 16

**Discussion prompt:** What would change for human approval?

**Header:** Approval is a workflow design decision, not just another prompt line

**Subheader:** A long human wait changes the caller contract.

**Option A: fulfillment owns the wait**

- Agent returns an outcome such as `MANUAL_APPROVAL_REQUIRED`.
- `fulfillment.Order` waits before buying the label.
- Fulfillment re-verifies rates, warehouse, inventory, and SLA after approval.

**Option B: agent owns an approval tool**

- Add an LLM tool backed by an Asynchronously Completed Activity.
- The agent waits for human input, then re-checks context before finalizing.
- The current synchronous Nexus operation would need a different pending/completion contract.

**Prompt:**

- What is the human approving?
- What must be re-verified later?
- Which workflow owns cancellation, timeout, and audit?

## Slide 17

**Header:** What to observe in the lab

**Subheader:** Tie every design decision back to a visible history event.

**Proof checklist:**

- `build_system_prompt` LocalActivity.
- `call_llm` Activity.
- `get_carrier_rates` and `get_location_events` tool calls.
- `REJECTED` finalize before a negative outcome, when present.
- `find_alternate_warehouse` before accepted `MARGIN_SPIKE` or `SLA_BREACH`.
- Recommendation returned to `fulfillment.Order`.
- `margin_leak` or `sla_breach_days` on `fulfillment.Order`.

**Takeaway:**

- We are not trusting an agent because it sounds plausible. We are constraining and observing it through a workflow.
