# Exercise 01 Risk Mitigation Slide Copy

## Slide 1

**Header:** Can you spot the risk in this move toward fulfillment ownership while rolling this out under load?

**Subheader:** We are changing who owns fulfillment while orders are still flowing.

**Prompt:**

- What could double-fulfill an order?
- What could strand an order?
- What could make an old workflow replay differently?
- What proof would convince you the cutover is safe?

## Slide 2

**Header:** The safe rollout order

**Subheader:** The sequence is the safety mechanism.

**Steps:**

1. Prove `apps v1 -> processing v1 -> Kafka fulfillment`
2. Start sustained traffic
3. Deploy `processing v2` first
4. Promote `processing v2`
5. Deploy `apps v2`
6. Start fulfillment workers
7. Ramp `apps v2`
8. Verify old and new paths
9. Complete the cutover

**Speaker note:**

- The code matters, but the order matters more.

## Slide 3

**Exercise activity:** Confirm `v1` is current

**Header:** Start from a known routing baseline

**Subheader:** Before changing behavior, prove Temporal is routing new executions to the old behavior.

**Risk mitigation:**

- Prevents accidental mixed-version debugging.
- Makes the baseline explainable.
- Gives us a clear before/after comparison.

**What participants should see:**

- `apps` current version is `v1`
- `processing` current version is `v1`

## Slide 4

**Exercise activity:** Start sustained traffic

**Header:** Keep the system under load

**Subheader:** A safe rollout has to work while orders are arriving, not after the system is quiet.

**Risk mitigation:**

- Exposes version routing behavior in real time.
- Creates in-flight executions that must remain pinned.
- Forces us to prove old and new paths can coexist.

**Facilitator line:**

- We are not testing whether the happy path works. We are testing whether the transition works.

## Slide 5

**Exercise activity:** Observe the legacy path

**Header:** Prove what "old behavior" means

**Subheader:** `apps v1` calls `processing`, and `processing` publishes the Kafka fulfillment handoff.

**Risk mitigation:**

- Confirms the old fulfillment owner is still `processing.Order`.
- Gives participants a concrete artifact to compare against later.
- Avoids vague "it worked" validation.

**Proof:**

- Generated order exists.
- Processing admin endpoint shows Kafka fulfillment record.

## Slide 6

**Exercise activity:** Implement/start `processing v2`

**Header:** Teach processing the new contract before anyone uses it

**Subheader:** `processing v2` must understand `send_fulfillment` before `apps v2` can safely send it.

**Risk mitigation:**

- Prevents `apps v2` from talking to code that ignores the routing slip.
- Keeps `apps v1` compatible because missing `send_fulfillment` still means `true`.
- Makes the contract visible in workflow input/history.

**Key phrase:**

- Absent means legacy. `false` means apps owns fulfillment.

## Slide 7

**Exercise activity:** Promote `processing v2`

**Header:** Make the dependency current first

**Subheader:** New `processing.Order` executions now land on code that understands the handoff contract.

**Risk mitigation:**

- Removes the duplicate-fulfillment trap.
- Keeps old pinned `processing v1` executions alive.
- Allows `apps v1` traffic to keep working unchanged.

**Callout:**

- If `apps v2` reaches `processing v1`, the old code can still publish Kafka.

## Slide 8

**Exercise activity:** Implement `apps v2`

**Header:** Move orchestration ownership to `apps.Order`

**Subheader:** `apps v2` starts `fulfillment.Order`, still calls processing, then completes fulfillment after processing succeeds.

**Risk mitigation:**

- Fulfillment starts early, but shipping does not happen before processing succeeds.
- Processing stays focused on validation and enrichment.
- The caller explicitly tells processing not to send the legacy handoff.

**Proof to look for later:**

- `ProcessOrderRequest.options.send_fulfillment=false`

## Slide 9

**Exercise activity:** Start fulfillment workers

**Header:** Start the new owner before routing traffic to it

**Subheader:** `apps v2` depends on `fulfillment.Order` being available.

**Risk mitigation:**

- Prevents new-path orders from starting and then waiting on missing fulfillment workers.
- Separates "processing can skip Kafka" from "fulfillment can actually run."
- Makes the new path observable before ramping traffic.

## Slide 10

**Exercise activity:** Start and ramp `apps v2`

**Header:** Ramp the behavior change, not the whole system

**Subheader:** Some new orders keep using `apps v1`; some new orders use `apps v2`.

**Risk mitigation:**

- Limits blast radius.
- Shows old and new behavior side by side.
- Lets participants inspect mixed traffic while both versions are intentionally alive.

**Expected split:**

- `apps v1` orders: Kafka fulfillment record.
- `apps v2` orders: `fulfillment.Order`, no Kafka handoff.

## Slide 11

**Exercise activity:** Inspect proof

**Header:** The audit trail is the point

**Subheader:** We should be able to explain each order's path from Temporal history.

**Risk mitigation:**

- No hidden feature flag decision.
- No guessing which service owned fulfillment.
- No silent duplicate handoff.

**Proof checklist:**

- Deployment version on `apps.Order`
- `send_fulfillment=false` on new-path `processing.Order`
- `fulfillment.Order` exists for new-path orders
- Kafka record exists only for old-path orders

## Slide 12

**Exercise activity:** Complete cutover

**Header:** Promote only after the mixed period is understood

**Subheader:** Once the new path is proven, make `apps v2` current and let old pinned executions drain.

**Risk mitigation:**

- Avoids forced migration of in-flight workflows.
- Keeps old workers available only for work that already chose them.
- Ends with a clean ownership model.

**Takeaway:**

- Worker Versioning controls which code receives new executions.
- The routing slip controls who owns fulfillment for each order.
