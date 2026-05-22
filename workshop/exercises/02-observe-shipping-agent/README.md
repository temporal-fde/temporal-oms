# Exercise 02: Observe The ShippingAgent Reliability Harness

Source spec: [spec.md](../../../specs/workshop/exercises/02-observe-shipping-agent/spec.md)

## Goal

Trace one AI-assisted shipping recommendation end to end.

You will run an order scenario, inspect the `ShippingAgent` workflow in Temporal UI, and connect
the recommendation back to `fulfillment.Order` Search Attributes. The point is to see the advisory
boundary clearly: `ShippingAgent` recommends a shipping option; `fulfillment.Order` applies the
business decision.

## Starting Assumptions And Setup

Run this exercise from its directory:

```bash
cd workshop/exercises/02-observe-shipping-agent
```

If Exercise 01 services are still running, stop them first:

```bash
../01-safe-fulfillment-handoff/scripts/stop.sh
```

This exercise uses the full local stack. Start Temporal server in its own terminal and leave it
running:

```bash
temporal server start-dev \
  --ip 0.0.0.0 \
  --port 7233 \
  --ui-ip 0.0.0.0 \
  --ui-port 8233
```

In another terminal, start the OMS services:

```bash
../../../scripts/local-up.sh
```

`local-up.sh` starts the APIs, Java workers, enablements workers, fulfillment workers, and the
Python fulfillment worker. It expects Temporal to already be running.

Confirm the stack is ready:

```bash
./scripts/status.sh
```

Expected result:

- Temporal is reachable.
- `apps-api`, `processing-api`, `fulfillment-api`, and `enablements-api` are running.
- `apps-workers`, `processing-workers`, `fulfillment-workers`, `enablements-workers`, and
  `python-fulfillment-worker` are running.
- The Python fulfillment worker log includes `All workers polling`.

If `ANTHROPIC_API_KEY` is missing or rate limited, the non-AI services may still be up, but the
`ShippingAgent` LLM activity will fail when a scenario reaches it.

## 1. Pick A Scenario

Use one of the three scenario tracks below. You do not need to run all three.

| Track | Command | What It Proves |
|---|---|---|
| Normal decision | `./scripts/run-valid-order.sh` | A normal order can receive a shipping recommendation and complete without `margin_leak` or `sla_breach_days` |
| Margin discovery | `./scripts/run-margin-spike.sh` | A 1-cent paid shipping price forces `MARGIN_SPIKE`; `fulfillment.Order` records `margin_leak` |
| SLA discovery | `./scripts/run-sla-breach.sh` | A same-day delivery promise forces `SLA_BREACH`; `fulfillment.Order` records `sla_breach_days` |

Each wrapper runs the existing scenario script and prints:

- `ORDER_ID`
- `CUSTOMER_ID`
- Temporal UI lookup hints
- Useful fulfillment visibility queries

## 2. Trace The Order Path

Open Temporal UI:

```text
http://localhost:8233
```

Use the IDs printed by the scenario script.

Inspect these workflows:

| Namespace | Workflow | ID |
|---|---|---|
| `apps` | `apps.Order` | `ORDER_ID` |
| `processing` | `processing.Order` | `ORDER_ID` |
| `fulfillment` | `fulfillment.Order` | `ORDER_ID` |
| `fulfillment` | `ShippingAgent` | `CUSTOMER_ID` |

The important shape:

```text
apps.Order
  -> processing.Order
  -> fulfillment.Order
  -> ShippingAgent.recommendShippingOption
```

`ShippingAgent` is not a per-order child workflow. It is a long-running per-customer workflow that
receives a `recommend_shipping_option` Update.

## 3. Inspect The Agent Boundary

In the `ShippingAgent` workflow history, find the `recommend_shipping_option` Update and identify:

- `build_system_prompt` LocalActivity
- `call_llm` Activity
- `get_carrier_rates` tool activity
- `get_location_events` tool activity, when present
- `find_alternate_warehouse`, for margin or SLA discovery tracks
- `finalize_recommendation`

For the margin and SLA tracks, the proof point is:

```text
find_alternate_warehouse happens before the accepted MARGIN_SPIKE or SLA_BREACH recommendation.
```

The prompt tells the agent what good reasoning looks like. The workflow enforces the minimum
process contract. The model still owns the recommendation, but the workflow makes one prerequisite
non-negotiable: before `MARGIN_SPIKE` or `SLA_BREACH` can be accepted, the alternate-warehouse check
must have happened.

## 4. Inspect The Fulfillment Decision

Return to `fulfillment.Order` for the same `ORDER_ID`.

Confirm that `fulfillment.Order` applies the recommendation:

- `ShippingAgent` returns the recommendation.
- `fulfillment.Order` selects the shipping option.
- `fulfillment.Order` prints the label and deducts inventory.
- `fulfillment.Order` upserts Search Attributes when the recommendation exposes margin or SLA risk.

The advisory boundary matters:

```text
ShippingAgent recommends.
fulfillment.Order decides and records the business outcome.
```

## 5. Query The Discovery Data

In Temporal UI, switch to the `fulfillment` namespace and run these visibility queries:

```text
margin_leak > 0
```

```text
margin_leak >= 500
```

```text
sla_breach_days > 0
```

```text
sla_breach_days >= 2
```

```text
margin_leak > 0 OR sla_breach_days > 0
```

Open one workflow returned by a query. Connect the Search Attribute back to:

- the `ShippingAgent` recommendation
- the selected shipping option in `fulfillment.Order`
- the business question it answers

These Search Attributes are the first launch story for the agent:

- Are we leaking fulfillment shipping margin?
- Are we missing promised delivery SLAs?

Metrics could answer aggregate counts. Search Attributes let you list and inspect the exact orders.

## 6. Open Discussion: Where Should HitL Live?

Suppose the discovery data shows that margin leaks above a threshold should require manual approval
before buying the label.

Discuss the responsibility boundary. There is no single answer in this exercise.

Option A: agent recommends a separate path.

- Add a recommendation outcome such as `MANUAL_APPROVAL_REQUIRED` or `SHIP_WITH_APPROVAL`.
- `ShippingAgent` returns quickly.
- `fulfillment.Order` owns the human approval wait before label purchase.
- After approval, fulfillment may need to call the agent or integrations again because rates,
  warehouse availability, and SLA context may be stale.

Option B: agent owns a long-running approval tool.

- Add a new LLM tool backed by an Asynchronously Completed Activity.
- The model can decide that approval is needed.
- The tool can take a long time to resolve.
- When approval resolves, the agent can re-check warehouse, rates, SLA, and alternate options
  before finalizing.

Current implementation constraint:

- `fulfillment.Order` calls `ShippingAgent.recommendShippingOption` through a synchronous Nexus
  operation.
- That Nexus operation currently has a 120-second timeout.
- The Python Nexus handler waits for the `recommend_shipping_option` Update result.

So a long-running approval tool is easy to imagine from the agent side, but the caller contract
would need to change if the approval can take minutes or hours.

Discussion prompts:

- What is the human approving: margin overage, a specific label, a warehouse, or a late shipment?
- If approval arrives later, what must be re-verified?
- Which workflow should own the durable wait?
- Where should the human decision audit trail live?
- Should the caller receive a pending result, or should the Nexus operation remain open?

## Cleanup

Stop local services:

```bash
../../../scripts/local-down.sh
```

Stop the Temporal dev server terminal with `Ctrl-C`.
