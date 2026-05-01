# Exercise 02 Spec: Observe The ShippingAgent Reliability Harness

**Workshop Slot:** Exercise 02

**Target Timebox:** 55 minutes

**Exercise Mode:** Hands-on guided observation, no production code edits

**Prerequisite:** Exercise 01 completed, with new order traffic routed through `apps v2 -> fulfillment.Order -> ShippingAgent`

## Current State

Exercise 01 moves new fulfillment orchestration into `apps.Order` and routes new orders through
`fulfillment.Order`. The second exercise starts from that new path and zooms in on the AI component
that now participates in fulfillment.

The relevant runtime path is:

```text
apps.Order
  -> fulfillment.Order validateOrder, via Nexus endpoint oms-fulfillment-v1
  -> processing.Order, with send_fulfillment=false after Exercise 01
  -> fulfillment.Order fulfillOrder
  -> ShippingAgent.recommendShippingOption, via Nexus endpoint oms-fulfillment-agents-v1
  -> ShippingAgent workflow, Python, fulfillment namespace, agents task queue
  -> fixture-backed shipping and integration tools
```

`ShippingAgent` is a long-running per-customer workflow. Its workflow ID is `customer_id`, and the
Python Nexus handler starts or reuses that workflow with UpdateWithStart:

- Nexus service handler: `ShippingAgentImpl.recommend_shipping_option`
- Temporal workflow type: `ShippingAgent`
- Workflow ID: `customer_id`
- Task queue: `agents`
- Conflict policy: use the existing workflow if it is already running
- Update name: `recommend_shipping_option`
- Update ID: the Nexus request ID when present

The current implementation pre-resolves the inventory origin, and verifies the destination when
needed, before the LLM loop so the first LLM turn can request carrier rates and location events
using concrete addresses. The exercise should teach this current behavior rather than older design
notes that described inventory lookup as the first LLM-selected tool call.

The visible reliability harness includes:

- `build_system_prompt` as a LocalActivity, so prompt text is captured in history for replay
- `call_llm` as an Activity, so vendor calls are retried and audited outside deterministic workflow code
- `get_carrier_rates` on the `fulfillment-shipping` task queue, backed by `enablements-api`
- `get_location_events` on the `agents` task queue, backed by `enablements-api`
- `find_alternate_warehouse` through the integrations Nexus endpoint before negative outcomes
- internal `finalize_recommendation` tool handling, so structured output is not parsed from prose
- workflow-layer process contract that appends a `REJECTED` tool result when the LLM tries to
  finalize `MARGIN_SPIKE` or `SLA_BREACH` before calling `find_alternate_warehouse`

`ShippingAgent` recommends. `fulfillment.Order` decides. The recommendation is applied by
`fulfillment.Order`, which records fulfillment state and upserts fulfillment Search Attributes such
as `margin_leak` and `sla_breach_days`.

## Goal

Participants should be able to trace one AI-assisted shipping decision end to end and explain which
parts are probabilistic, which parts are deterministic, and where Temporal provides durable
execution, auditability, retries, and operational visibility.

The exercise is intentionally observational. Exercise 01 already used the hands-on coding and
rollout mechanics. Exercise 02 gives participants a repeatable way to debug and govern AI behavior
inside a production Temporal application.

## Business Stories

### Story 1: Discovery Before Process Change

The initial ShippingAgent launch is a discovery mechanism, not an immediate business-process
change.

The business questions are:

- Are we leaking margin when fulfillment-time carrier rates are worse than checkout assumptions?
- Are we missing delivery SLAs that customers were promised at checkout?

The first implementation answers those questions through fulfillment workflow visibility:

- `margin_leak` records the shipping-cost overage in cents when the selected fulfillment-time rate
  exceeds the configured shipping margin.
- `sla_breach_days` records how many days the selected option misses the promised delivery window.

Metrics could answer aggregate questions such as "how many orders leaked margin this hour?" This
exercise deliberately uses Search Attributes because participants can list and inspect the exact
workflow executions in Temporal UI. That makes discovery concrete: the list is not only a graph, it
is the set of orders that need follow-up analysis.

Temporal UI visibility queries to run in the `fulfillment` namespace:

| Business question | Temporal UI query |
|---|---|
| Which orders leaked shipping margin? | `margin_leak > 0` |
| Which orders leaked more than $5.00? | `margin_leak >= 500` |
| Which orders missed the promised delivery window? | `sla_breach_days > 0` |
| Which orders missed SLA by at least two days? | `sla_breach_days >= 2` |
| Which orders need shipping exception review? | `margin_leak > 0 OR sla_breach_days > 0` |

Naming note: the current Search Attribute is `margin_leak`. The business story may call this a
margin breach; the implementation records the cents leaked beyond the configured margin.

### Story 2: Open Discussion - Human-In-The-Loop Margin Approval

After discovery, the business may decide that margin leaks above a threshold should require manual
approval before buying the shipping label.

This should be an open design discussion in the lab, not a solved design in the exercise. The
discussion should be guided by responsibility boundaries: which component recommends, which
component owns the business hold, which component owns re-verification, and which component owns the
final decision to buy a label.

Possible implementation directions:

| Direction | Shape | Why it is interesting | Main design pressure |
|---|---|---|---|
| Agent recommends a separate path | Add a recommendation outcome such as `MANUAL_APPROVAL_REQUIRED`, `SHIP_WITH_APPROVAL`, or another exception path; `ShippingAgent` returns quickly; `fulfillment.Order` owns the human approval wait before label purchase | Keeps the business hold in the fulfillment domain workflow, where label purchase, inventory hold, cancellation, and visibility already live | After approval, fulfillment may need to call the agent or integrations again because the original rate/warehouse context may be stale |
| Agent owns a long-running approval tool | Add an LLM tool backed by an Asynchronously Completed Activity; the agent waits for human approval and then continues the reasoning loop | Shows how easily the agent can be extended with a new tool, even one that takes a long time to resolve. When approval resolves, the agent can re-check the current warehouse, rates, SLA, and alternate options before finalizing whether the approved shipment is still possible | The current Nexus call is synchronous and short-lived; a long approval wait would require a different operation contract |

The current implementation is an important constraint for that discussion:

- `fulfillment.Order` calls `ShippingAgent.recommendShippingOption` through a synchronous Nexus
  operation.
- The current `ShippingAgent` Nexus operation timeout in `fulfillment.Order` is 120 seconds.
- The Python Nexus handler is a synchronous operation that waits for the `ShippingAgent`
  `recommend_shipping_option` Update result.
- A manual approval that waits minutes, hours, or days would keep the fulfillment update and Nexus
  operation open far longer than the current contract allows.

Discussion questions:

- What is the human actually approving: margin overage, a specific carrier label, a specific
  warehouse, or a best-effort shipment despite SLA risk?
- If approval arrives later, what must be re-verified before the label can be purchased?
- Which workflow should own the long wait: `ShippingAgent`, `fulfillment.Order`, or a separate
  approval workflow?
- Is the agent responsible for recommending a separate path, or for carrying that path all the way
  through approval and re-verification?
- Where should the durable audit trail of the human decision live?
- What should happen if the order is cancelled, inventory hold expires, or rates change while
  approval is pending?
- Should approval be a recommendation that `fulfillment.Order` acts on, or a tool call inside the
  agent loop?
- If the agent owns the wait, should the Nexus operation stay open, or should the caller receive an
  accepted/pending result and observe completion another way?

For this workshop, the key point is the architectural boundary: discovery can be added as
observability with minimal process change; enforcement via human approval is a separate workflow
design decision. The lab should make that tradeoff visible rather than resolve it prematurely.

## Constraints

- The exercise must avoid environment-specific debugging of Python, Maven, prompts, or API credentials.
- Attendees should not edit `ShippingAgent` code in this exercise. Code extension belongs in the
  next exercise.
- The integration data must stay fixture-backed through `enablements-api`; EasyPost, PredictHQ, and
  other live logistics APIs are out of scope.
- The exercise should use real Temporal workflow histories, not slides or screenshots as the
  primary artifact.
- LLM use must be rate-limit aware. The lab should not require every participant to run every live
  LLM scenario at the same time.
- The exercise must have an instructor fallback if the shared Anthropic key is missing or rate
  limited.

## Available Options

| Option | Mechanism | Pros | Cons |
|---|---|---|---|
| Instructor-only demo | Instructor runs valid, margin, and SLA scenarios while attendees watch Temporal UI | Lowest runtime risk; no attendee setup variance | Too passive for a hands-on workshop; attendees do not practice inspection |
| Direct `ShippingAgent` update | Start `ShippingAgent` and call `recommend_shipping_option` with a handcrafted Temporal CLI payload | Isolates the AI workflow; easiest way to show cache behavior | Bypasses the full `apps -> fulfillment -> ShippingAgent` story that Exercise 01 set up |
| Existing order scenarios | Use `scripts/scenarios/valid-order`, `margin-spike`, and `sla-breach` | Exercises the real order path; already fixture-backed; ties directly to Search Attributes | Needs Exercise 01 solution state; can create too many LLM calls if everyone runs all scenarios |
| Unit-test style mocked LLM | Run Python tests or a local deterministic LLM stub | Fully deterministic; no external LLM key or rate limits | Less compelling as an operations/debugging exercise; hides the live activity and Nexus path |
| Code extension | Add a new tool or modify prompt behavior | Strong hands-on learning | Wrong timebox and support load for Exercise 02; should be Exercise 03 |

## Chosen Approach

Use existing order scenarios as the primary path, with a direct `ShippingAgent` update as an
optional cache drill.

Participants run or inspect one assigned scenario:

| Track | Scenario | Trigger | Expected proof |
|---|---|---|---|
| Normal decision | `scripts/scenarios/valid-order` | Paid shipping price and delivery days are realistic | `ShippingAgent` returns a non-negative recommendation and `fulfillment.Order` completes without `margin_leak` or `sla_breach_days` |
| Margin protection | `scripts/scenarios/margin-spike` | `paidPriceCents=1` | `ShippingAgent` must call `find_alternate_warehouse` before accepted `MARGIN_SPIKE`; `fulfillment.Order` records `margin_leak` |
| SLA protection | `scripts/scenarios/sla-breach` | `deliveryDays=0` | `ShippingAgent` must call `find_alternate_warehouse` before accepted `SLA_BREACH`; `fulfillment.Order` records `sla_breach_days` |

Not every participant needs to run every track live. The debrief recombines the three observations
into one shared model.

## Exercise Narrative

### Act 1: Reconnect From Exercise 01

Start with the architecture change participants just made:

- `apps.Order` owns fulfillment orchestration for new orders.
- `processing.Order` no longer publishes the legacy Kafka handoff for new-path orders.
- `fulfillment.Order` is now the durable owner of shipping selection and fulfillment state.

The question for Exercise 02:

> We moved traffic to the AI-assisted fulfillment path. How do we prove what the AI did, debug a
> bad recommendation, and preserve deterministic business control?

Also frame the discovery question:

> Before adding a new approval process, can we list the exact orders where margin or SLA risk is
> actually happening?

### Act 2: Trace UpdateWithStart

Participants run their assigned scenario and collect two IDs:

- `ORDER_ID`
- `CUSTOMER_ID`

In Temporal UI:

1. Open the `apps` namespace and find `apps.Order` for `ORDER_ID`.
2. Open the `fulfillment` namespace and find `fulfillment.Order` for `ORDER_ID`.
3. Open the `fulfillment` namespace and find `ShippingAgent` for `CUSTOMER_ID`.

They should observe that `ShippingAgent` is not a per-order child workflow. It is a long-running
per-customer workflow that receives a `recommend_shipping_option` Update.

### Act 3: Inspect The AI Reliability Harness

Participants inspect the `ShippingAgent` history and label each boundary:

- deterministic workflow code
- LocalActivity prompt construction
- LLM Activity call
- tool calls dispatched as Temporal Activities or Nexus operations
- internal finalization tool
- workflow-layer `REJECTED` tool result or acceptance
- returned recommendation

For the margin and SLA tracks, participants must find the process contract:

```text
finalize_recommendation(MARGIN_SPIKE or SLA_BREACH)
  -> workflow appends a REJECTED tool result because find_alternate_warehouse has not happened yet
find_alternate_warehouse
  -> returns no usable alternate
finalize_recommendation(...)
  -> accepted
```

The prompt tells the agent what good reasoning looks like. The workflow enforces the minimum
process contract. The model still owns the recommendation, but the workflow makes one prerequisite
non-negotiable: before `MARGIN_SPIKE` or `SLA_BREACH` can be accepted, the alternate-warehouse check
must have happened.

### Act 4: Show Who Decides

Participants return to `fulfillment.Order` and confirm that the Java workflow applies the
recommendation:

- selected carrier rate becomes `shipping_selection`
- `MARGIN_SPIKE` maps to `margin_leak`
- `SLA_BREACH` maps to `sla_breach_days`
- label printing and inventory deduction remain normal deterministic workflow work

This closes the loop: the AI workflow recommends, while the domain workflow owns the business
decision and observability contract.

### Act 5: Query The Discovery Data

Participants use Temporal UI visibility queries in the `fulfillment` namespace:

- `margin_leak > 0`
- `sla_breach_days > 0`
- `margin_leak > 0 OR sla_breach_days > 0`

They should open at least one listed workflow and connect the Search Attribute back to the
`ShippingAgent` recommendation and the `fulfillment.Order` shipping selection.

## What Participants Will Do

The attendee-facing guide should have participants:

1. Stop any Exercise 01 sustained load generator, or leave it running only if the instructor wants
   background noise.
2. Confirm `apps v2` and `processing v2` are current, fulfillment workers are running, and the
   Python worker logs `All workers polling`.
3. Pick one assigned scenario: valid order, margin spike, or SLA breach.
4. Submit the order and capture payment with the scenario scripts.
5. Record `ORDER_ID` and `CUSTOMER_ID`.
6. In Temporal UI, trace `apps.Order -> processing.Order -> fulfillment.Order -> ShippingAgent`.
7. In the `ShippingAgent` history, identify UpdateWithStart and at least three tool boundaries.
8. For margin or SLA scenarios, prove that `find_alternate_warehouse` happened before the accepted
   final negative recommendation.
9. In `fulfillment.Order`, inspect output and Search Attributes to show how the recommendation was
   applied.
10. Run at least one fulfillment namespace visibility query for `margin_leak` or `sla_breach_days`.
11. Share one observation in the debrief: what would they tell a customer who asks, "What did the
    AI actually do?"

## Required Exercise Materials

Create attendee-facing material under:

```text
workshop/exercises/02-observe-shipping-agent/
  README.md
  scripts/
```

Recommended scripts:

| Script | Purpose |
|---|---|
| `scripts/status.sh` | Verify Temporal, APIs, Java fulfillment workers, Python worker, and relevant Worker Deployment state |
| `scripts/run-valid-order.sh` | Wrap the existing valid-order scenario and print Temporal UI lookup hints |
| `scripts/run-margin-spike.sh` | Wrap the margin-spike scenario and print expected `MARGIN_SPIKE` proof points |
| `scripts/run-sla-breach.sh` | Wrap the SLA-breach scenario and print expected `SLA_BREACH` proof points |
| `scripts/direct-cache-drill.sh` | Optional direct `ShippingAgent` UpdateWithStart call twice with the same payload to show `cache_hit=true` |

Recommended guide artifacts:

- A one-page trace worksheet with blanks for `ORDER_ID`, `CUSTOMER_ID`, workflow type, namespace,
  and evidence found.
- A screenshot-free checklist of Temporal UI locations to inspect.
- A short "when things fail" section that maps symptoms to likely causes:
  missing Python worker, missing Anthropic key, LLM rate limit, missing fulfillment endpoint, or
  stale Exercise 01 code state.

## Implementation Follow-Ups

These are not required production behavior changes, but they would make the exercise more reliable:

- Add a read-only `get_options` Query to `ShippingAgent` using the existing `ShippingOptionsCache`
  proto so the cache can be inspected without reading raw history.
- Add a deterministic workshop LLM mode or recorded-response mode for instructor fallback when
  `ANTHROPIC_API_KEY` is unavailable or rate limited.
- Add a small history inspection helper that prints the relevant event types for a `CUSTOMER_ID`.
  This should supplement Temporal UI inspection, not replace it.

## Instructor Setup

Before Exercise 02 starts:

1. Confirm Exercise 01 has completed or apply the Exercise 01 solution state.
2. Stop the `WorkerVersionEnablement` load generator unless the instructor intentionally wants
   background orders.
3. Ensure `apps` and `processing` Worker Deployments are current on `v2`.
4. Ensure fulfillment Java workers and the Python fulfillment worker are running.
5. Confirm the Python worker has access to `ANTHROPIC_API_KEY`, unless deterministic fallback mode
   has been implemented.
6. Open Temporal UI with namespace switching ready for `apps`, `processing`, and `fulfillment`.

## Proposed Timing

| Segment | Time | Purpose |
|---|---:|---|
| Reset | 5 min | Re-orient after Exercise 01 and confirm the new order path |
| Pattern frame | 5 min | Explain UpdateWithStart, per-customer agent workflow, and "agent recommends, workflow decides" |
| Run assigned scenarios | 10 min | Small groups create one order and capture payment |
| Guided trace | 15 min | Inspect `apps.Order`, `fulfillment.Order`, and `ShippingAgent` histories |
| Visibility drill | 10 min | Query `margin_leak` and `sla_breach_days`, then inspect one listed workflow |
| Open discussion | 10 min | Discuss where a future HitL margin approval flow should live |

Total target: 55 minutes.

If Exercise 01 overruns, use a 25 minute fallback:

1. Instructor runs one margin-spike scenario.
2. Everyone inspects the same `CUSTOMER_ID`.
3. Skip the cache drill and scenario split.
4. Debrief only the hard guard and "agent recommends, workflow decides" model.

## Success Criteria

- Participants can locate the `ShippingAgent` workflow by `CUSTOMER_ID`.
- Participants can explain why UpdateWithStart is used instead of a stateless API call.
- Participants can identify `call_llm` and tool dispatch boundaries in Temporal history.
- Participants can explain which calls are deterministic workflow code, Activities, LocalActivities,
  and Nexus operations.
- At least one run proves the `MARGIN_SPIKE` path, including `find_alternate_warehouse`.
- At least one run proves the `SLA_BREACH` path, including `find_alternate_warehouse`.
- Participants can find `margin_leak` or `sla_breach_days` on `fulfillment.Order` when the scenario
  should set it.
- Participants can run the Temporal UI visibility queries for `margin_leak` and `sla_breach_days`.
- Participants can explain why Search Attributes are being used here instead of only metrics.
- Participants can identify the current synchronous 120-second `ShippingAgent` Nexus constraint
  when discussing long-running manual approval designs.
- Final takeaway is clear: Temporal does not make the model deterministic; it makes the AI-mediated
  process durable, inspectable, retryable, and governable.

## Validation Strategy

Before the workshop, dry run the exercise from a clean Codespace or local workspace:

- Run Exercise 01 through `apps v2` promotion.
- Run one valid order scenario and confirm `ShippingAgent` completes with a usable recommendation.
- Run one margin-spike scenario and confirm `margin_leak` is set.
- Run one SLA-breach scenario and confirm `sla_breach_days` is set.
- Confirm Python worker logs show `All workers polling`.
- Confirm Temporal UI histories are short enough to inspect live.
- Confirm Anthropic key and rate limits can handle the expected number of scenario runs.

## Risks And Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---:|---|
| Exercise 01 leaves attendees in inconsistent code or Worker Deployment state | Exercise 02 cannot reach ShippingAgent reliably | Medium | Provide a status script and instructor reset path; allow shared instructor workflow IDs for fallback |
| Anthropic key missing or rate limited | LLM Activity fails, blocking live traces | Medium | Limit duplicate live runs; add deterministic fallback or pre-recorded workflow IDs |
| Participants inspect the wrong namespace or workflow ID | Pacing slows and support load rises | High | Scripts must print `ORDER_ID`, `CUSTOMER_ID`, namespace, and workflow type lookup hints |
| Temporal UI history is too noisy | Learning objective gets buried in event detail | Medium | Provide a trace worksheet and optional CLI summarizer |
| Existing scenarios trigger duplicate legacy Kafka handoffs if Exercise 01 solution is incomplete | Confuses the story about new fulfillment ownership | Medium | `status.sh` must check for `send_fulfillment=false` support and `apps v2` current before scenario runs |
| Too many live scenario runs happen simultaneously | LLM or local CPU saturation | Medium | Limit duplicate live runs and stagger starts when needed |

## Discussion Prompts

- Why is the ShippingAgent a workflow instead of a stateless service call?
- What does UpdateWithStart give us for a per-customer agent session?
- Which parts of the process are allowed to be probabilistic?
- Where does the system enforce a rule even if the model tries to skip it?
- Why should `fulfillment.Order` apply the recommendation instead of letting the agent make the
  final business decision?
- What would you inspect first if a customer says the model chose an expensive label?
- What business threshold would justify a manual approval hold for margin leakage?
- Should manual approval live inside `ShippingAgent`, inside `fulfillment.Order`, or in a separate
  approval workflow?
- If approval takes hours, what should be re-checked before buying the label?
- Which customer-specific systems could be replaced behind these same tool boundaries?

## References

- Workshop overview: `specs/workshop/spec.md`
- AI workshop arc: `specs/workshop/augment-with-ai/spec.md`
- Exercise 01 spec: `specs/workshop/exercises/01-safe-fulfillment-handoff/spec.md`
- ShippingAgent workflow spec: `specs/fulfillment-order/shipping-agent/spec.md`
- Enablements ShippingAgent integration spec: `specs/enablements/shipping-agent/spec.md`
- ShippingAgent workflow implementation: `python/fulfillment/src/agents/workflows/shipping_agent.py`
- ShippingAgent Nexus handler: `python/fulfillment/src/services/shipping_agent_impl.py`
- Scenario scripts: `scripts/scenarios/README.md`
