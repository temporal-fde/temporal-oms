# Exercise 01 Spec: Safely Move Fulfillment Ownership

**Workshop Slot:** Exercise 01

**Target Timebox:** 45 minutes

**Exercise Mode:** Hands-on, using Temporal Worker Deployment CLI/operator commands directly

**Production Follow-up:** Temporal Worker Controller demo under load

## Current State

The order lifecycle currently crosses three bounded contexts:

- `apps.Order` is the ApplicationService. It collects commerce and payment inputs, then calls
  `processing.Order` through Nexus.
- `processing.Order` is the processing DomainService. It validates and enriches the order, then
  hands fulfillment off by publishing to the legacy Kafka fulfillment path.
- `fulfillment.Order` is the newer durable fulfillment workflow. It validates the address, holds
  inventory, calls ShippingAgent for rate recommendation, prints the label, deducts inventory, and
  records fulfillment observability such as `margin_leak` and `sla_breach_days`.

The architecture change is that `apps.Order` should become responsible for orchestrating
fulfillment directly:

1. `apps.Order` starts `fulfillment.Order` early via Nexus so address validation and inventory hold
   happen while processing runs.
2. `apps.Order` still calls `processing.Order` for validation and enrichment.
3. `apps.Order` sends `fulfillOrder` to `fulfillment.Order` after processing completes.
4. `processing.Order` must stop publishing the legacy Kafka fulfillment handoff for orders where
   the caller now owns fulfillment orchestration.

## Goal

Introduce the new fulfillment ownership model without disrupting in-flight orders and without
using application-level rollout flags inside workflow code.

Participants should understand how Temporal Worker Versioning and the Temporal Worker Controller
can safely roll out a coordinated change across ApplicationService and DomainService boundaries.

In this first exercise, participants use Temporal Worker Deployment commands directly. This keeps
the underlying mechanism visible before a later production-oriented segment shows how the Temporal
Worker Controller automates the same lifecycle from Kubernetes.

## Constraints

- Existing `apps.Order` executions must complete on the behavior they started with.
- Existing `processing.Order` executions must complete on the behavior they started with.
- `apps v1` must continue to work when `processing v2` is deployed.
- `apps v2` must not cause duplicate fulfillment handoffs.
- Rollout policy should stay in Temporal Worker Deployments, not in business code.
- The contract between `apps.Order` and `processing.Order` must be explicit enough to explain and
  audit from workflow inputs/history.

## Available Options

| Option | Mechanism | Pros | Cons |
|---|---|---|---|
| Application feature flag | Runtime config or percentage check inside `apps.Order` or `processing.Order` | Easy to understand; common in synchronous services | Dangerous in workflows if replay sees a different value; hides rollout policy in business logic; hard to audit per execution |
| `Workflow.getVersion` in `processing.Order` | Deterministic version gate around the Kafka activity | Safe for code evolution inside one workflow type; familiar Temporal primitive | Not the best fit for a cross-context architecture handoff; still leaves ambiguity about which caller owns fulfillment |
| Auto-upgrade Worker Versioning | Let running workflows move to the current Worker Deployment Version when compatible | Useful for compatible fixes where the latest worker should continue execution | Not useful here because this exercise is about preserving each order's chosen fulfillment path until that order finishes |
| Separate task queues/endpoints for legacy and new processing | `apps v1` calls one endpoint/task queue, `apps v2` calls another | Very explicit routing; simple mental model | Reintroduces task-queue-as-version-routing patterns; adds topology that exists only for migration |
| Nexus handler pins by Worker Deployment Version | Handler starts `processing.Order` with `VersioningOverride` based on operation/endpoint context | Strong service autonomy; build-id mapping owned by processing | More advanced than needed for the first workshop exercise; endpoint identity requires manual context propagation; adapter now owns migration routing |
| Routing slip + Worker Versioning | `apps v2` sends a deterministic request option telling processing not to send fulfillment; Worker Deployment commands roll out `processing v2`, then ramp `apps v2` | Explicit per-order contract; processing v2 remains backward-compatible with apps v1; rollout stays in Temporal; easy to inspect in history; maps directly to TWC later | Requires a small contract addition; deploy order matters because apps v2 depends on processing v2 support |

## Chosen Approach

Use a routing slip plus Worker Versioning.

Both `apps.Order` and `processing.Order` use pinned Worker Versioning for this exercise.
Auto-upgrade is not useful here because this exercise is about preserving each order's chosen
fulfillment path until that order finishes.

Add `send_fulfillment` to `ProcessOrderRequestExecutionOptions`.

`processing v2` interprets the option with a legacy-compatible default: absent means `true`.
`apps v1` does not set the field, so `processing v2` preserves legacy behavior. `apps v2` starts
and completes `fulfillment.Order` directly, and sends `send_fulfillment=false` when it calls
processing.

This creates a visible routing slip in the workflow input: the caller explicitly tells processing
whether processing should send the fulfillment handoff for this order.

## Implemented Exercise Materials

The spec stays focused on the architecture, constraints, and rollout model. The implemented lab
material lives under the root `workshop/` directory:

- Participant guide: `workshop/exercises/01-safe-fulfillment-handoff/README.md`
- Solution and code snippets: `workshop/exercises/01-safe-fulfillment-handoff/SOLUTION.md`
- Step runners: `workshop/exercises/01-safe-fulfillment-handoff/scripts/`

Exercise 01 is a live code-and-rollout exercise. Participants may apply the `processing v2` and
`apps v2` code changes during the lab, then start new worker processes with build ID `v2` while
the original `v1` workers keep running. `SOLUTION.md` records the code snippets and build/run
commands.

Exercise-specific scripts wrap the repetitive local process management so participants do not need
one terminal per service during the lab.

## Rollout Model

The exercise uses manual Worker Deployment commands so attendees see what TWC automates later.

The safe rollout sequence is:

1. Start only the baseline services needed for generated v1 traffic: `apps-api`, `apps-workers v1`,
   `processing-api`, `processing-workers v1`, `enablements-api`, and `enablements-workers`.
2. Start the enablements order generator so traffic is flowing continuously.
3. Implement, build, and start `processing v2` with support for `send_fulfillment`.
4. Use Worker Versioning to make `processing v2` current.
5. Keep `processing v1` available only for already-pinned in-flight processing workflows.
6. Implement and build `apps v2`.
7. Start the fulfillment-side workers required by the new path.
8. Start `apps v2` and use Worker Versioning to ramp it.
9. New `apps v2` executions start `fulfillment.Order` and set `send_fulfillment=false`.
10. Old `apps v1` executions continue to call processing without the option and still get the
   legacy Kafka handoff.
11. After `apps v1` and `processing v1` drain, sunset the old worker versions.

The important ordering rule:

`processing v2` and the fulfillment-side workers must be available before `apps v2` receives
traffic.

If `apps v2` calls `processing v1`, the old processing code ignores `send_fulfillment=false` and
would still publish the Kafka handoff, causing duplicate fulfillment. Worker Deployment promotion
order gives us the operational control to avoid that mixed state.

If `apps v2` receives traffic before fulfillment workers are polling, new-path orders can start but
cannot make useful progress through `fulfillment.Order`.

### Manual Commands Used In The Lab

The exercise should expose the underlying Temporal operations explicitly. The exact participant
commands live in the implemented guide:

`workshop/exercises/01-safe-fulfillment-handoff/README.md`

The later TWC/Kubernetes segment should show that the controller performs this same lifecycle from
WorkerDeployment rollout state: register new build IDs, wait for pollers, ramp traffic, gate the
rollout, and sunset drained versions.

## What Participants Will Do

The participant experience is implemented in
`workshop/exercises/01-safe-fulfillment-handoff/README.md`.

Participants will:

1. Start the explicit baseline service set, then start the enablements order generator so traffic is
   flowing continuously.
2. Observe the old path under load: `apps v1 -> processing -> Kafka fulfillment`.
3. Implement, build, and start `processing v2`, which supports the routing slip while preserving
   legacy behavior for old callers, then promote it to current.
4. Implement and build `apps v2`, which now starts `fulfillment.Order` and sets
   `send_fulfillment=false`.
5. Start fulfillment-side workers, then start and ramp `apps v2` to 50%.
6. Let the generator continue during the ramp and verify that old and new orders both complete, but
   only the old path creates Kafka fulfillment records.
7. Promote `apps v2` to current.
8. Inspect Temporal UI to confirm each execution kept its chosen behavior through workflow history.

## Proposed Timing

| Segment | Time | Purpose |
|---|---:|---|
| Decision frame | 5 min | Explain the options and why routing slip + Worker Versioning is selected |
| Start load + observe legacy path | 5 min | Run the enablements order generator and confirm Kafka fulfillment |
| Implement/promote processing v2 | 7 min | Show backward-compatible domain-service rollout |
| Implement/ramp apps v2 | 10 min | Keep generated traffic running and observe old/new behavior |
| Inspect proof | 8 min | Check Kafka records, `fulfillment.Order`, and `send_fulfillment=false` |
| Promote apps v2 | 5 min | Complete the cutover |
| Debrief/TWC bridge | 5 min | Explain how TWC automates the commands later |

Total target: 45 minutes if participants apply the provided solution snippets directly and Java
builds are already warm. Environment debugging or broad manual refactoring will push the exercise
past an hour.

## Success Criteria

- Legacy orders still publish the Kafka fulfillment handoff.
- New orders started by `apps v2` do not publish the Kafka fulfillment handoff.
- New orders do create and complete `fulfillment.Order` workflows.
- `ProcessOrderRequest.options.send_fulfillment=false` is visible on new-path processing workflow
  inputs.
- In-flight workflows stay pinned to their original worker versions.
- The final participant takeaway is clear: Worker Versioning controls which code receives new
  executions; the routing slip controls the per-order contract between ApplicationService and
  DomainService.

## Discussion Prompts

- Why is this not an application feature flag?
- What makes the routing slip replay-safe?
- Why does `processing v2` need a legacy-compatible default?
- What breaks if `apps v2` is ramped before `processing v2` is available?
- Which team owns the routing slip contract: apps, processing, or both?
- When would `VersioningOverride` in a Nexus handler be a better choice?
- When would a separate task queue or endpoint be justified despite the topology cost?
