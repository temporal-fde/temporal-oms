# Visual 03 - Safe Fulfillment Handoff Rollout

**Status:** Draft visual brief
**Mermaid source:** [`../mermaid/03-safe-fulfillment-handoff-rollout.mmd`](../mermaid/03-safe-fulfillment-handoff-rollout.mmd)

## Job

Show how the system moves from V1 to V2 without breaking in-flight workflows or creating duplicate
fulfillment handoffs.

## Audience Takeaway

The migration is safe because two controls work together:

- Worker Versioning controls which worker code receives new executions.
- The `send_fulfillment` routing slip records who owns fulfillment for a specific order.

## Required Explanation

The deploy order matters:

1. Promote `processing v2` first because it understands `send_fulfillment`.
2. Keep the default legacy-compatible so `apps v1` still works.
3. Ramp `apps v2` only after `processing v2` is available.
4. `apps v2` starts `fulfillment.Order` and sends `send_fulfillment=false`.
5. Old executions stay pinned to their original worker versions until they drain.

## Hazard to Call Out

If `apps v2` receives traffic before compatible `processing v2` is available, `processing v1` can
ignore `send_fulfillment=false` and still publish Kafka fulfillment. That mixed state risks
duplicate fulfillment. The rollout sequence exists to avoid that.

## Speaker Notes

This is the workshop's core safe-extensibility visual. Keep the conversation focused on ownership:
`apps.Order` is taking responsibility for fulfillment orchestration, and `processing.Order` remains
the processing domain service.

Avoid turning this into a general Worker Versioning lecture. The concrete story is enough:
in-flight orders keep their chosen behavior, new orders can be ramped gradually, and the routing
slip is visible in workflow history.

