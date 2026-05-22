# Exercise 01 Safe Fulfillment Handoff 24-Slide Step Copy

## Slide 1

**Exercise activity:** 1. Confirm `v1` is current

**Header:** Start from a known routing baseline

**Subheader:** Before changing behavior, prove Temporal routes new executions to the old code.

**What to do:**

1. Set `processing` current version to build ID `v1`.
2. Set `apps` current version to build ID `v1`.
3. Describe both Worker Deployments.

**Expected result:**

- `processing` current version is `v1`.
- `apps` current version is `v1`.

**Participant prompt:**

- What would be confusing if we skipped this baseline check?

## Slide 2

**Exercise activity:** 1. Confirm `v1` is current

**Header:** Why the baseline matters

**Subheader:** Mixed-version debugging is expensive when the starting state is unknown.

**What to observe:**

- Worker Deployment state is the rollout control plane.
- Current version controls which code receives new workflow executions.
- Existing pinned executions may still complete on the version they started with.

**Risk mitigation:**

- Prevents accidental mixed-version debugging.
- Makes before/after behavior explainable.
- Gives the group a clean audit point before traffic starts.

**Facilitator line:**

- We are going to change ownership under load. First we prove who owns fulfillment right now.

## Slide 3

**Exercise activity:** 2. Start sustained traffic

**Header:** Keep orders flowing during the rollout

**Subheader:** The transition has to work while new orders are arriving.

**What to do:**

1. Start the enablements load generator.
2. Leave it running through the rollout.
3. Query the generator state.
4. Watch new `apps.Order` executions appear in the `apps` namespace.

**Expected result:**

- New workflow IDs start with `order-${ENABLEMENT_ID}`.
- Orders continue to arrive while worker versions change.

**Participant prompt:**

- Why is an idle-system rollout less convincing?

## Slide 4

**Exercise activity:** 2. Start sustained traffic

**Header:** Why load is part of the safety test

**Subheader:** A safe handoff must preserve in-flight and new executions at the same time.

**What to observe:**

- Some workflows are already pinned before new versions appear.
- More workflows continue starting during the rollout.
- Worker Deployment commands affect routing for new executions, not by editing workflow history.

**Risk mitigation:**

- Exposes version routing behavior in real time.
- Creates in-flight executions that must keep their chosen behavior.
- Forces old and new paths to coexist intentionally.

**Facilitator line:**

- We are not testing the happy path. We are testing the transition.

## Slide 5

**Exercise activity:** 3. Observe the legacy path

**Header:** Prove what old behavior means

**Subheader:** `apps v1` calls processing, and processing publishes the legacy Kafka fulfillment handoff.

**What to do:**

1. Pick a generated `apps.Order` workflow ID.
2. Export it as `ORDER_ID`.
3. Query the processing admin endpoint for that order's fulfillment record.

**Expected result:**

- The generated order exists.
- The admin endpoint returns a Kafka fulfillment handoff record.

**Participant prompt:**

- Which service owns fulfillment in this baseline path?

## Slide 6

**Exercise activity:** 3. Observe the legacy path

**Header:** Why we inspect the old path first

**Subheader:** You cannot prove a migration worked unless you know what changed.

**What to observe:**

- `apps.Order` is the application orchestrator.
- `processing.Order` owns validation, enrichment, and the Kafka fulfillment handoff.
- `fulfillment.Order` is not yet part of the generated-order path.

**Risk mitigation:**

- Confirms the legacy fulfillment owner is still `processing.Order`.
- Gives participants a concrete artifact to compare against later.
- Avoids vague "it worked" validation.

**Proof to compare later:**

- Old path: Kafka fulfillment record exists.
- New path: `fulfillment.Order` exists and Kafka record does not.

## Slide 7

**Exercise activity:** 4. Implement `processing v2`

**Header:** Teach processing the new contract

**Subheader:** Processing must understand the routing slip before apps can safely send it.

**What to do:**

1. Add `send_fulfillment` to `ProcessOrderRequestExecutionOptions`.
2. Regenerate protobuf outputs.
3. Add the compatibility guard in `processing.Order`.
4. Wrap the legacy Kafka handoff with that guard.
5. Update the timeout guard so enrichment is enough when processing no longer owns fulfillment.

**Expected result:**

- `processing v2` can honor `send_fulfillment=false`.
- Missing `send_fulfillment` still behaves like legacy `true`.

## Slide 8

**Exercise activity:** 4. Implement `processing v2`

**Header:** Why the routing slip belongs in the request

**Subheader:** The caller's fulfillment ownership decision should be visible in workflow history.

**What to observe:**

- `apps v1` does not set `send_fulfillment`.
- `processing v2` treats absent as `true`.
- `apps v2` will later set `send_fulfillment=false`.

**Risk mitigation:**

- Keeps `apps v1` compatible with `processing v2`.
- Avoids application feature flags in workflow code.
- Makes the per-order contract explicit and auditable.

**Key phrase:**

- Absent means legacy. `false` means apps owns fulfillment.

## Slide 9

**Exercise activity:** 5. Start `processing v2`

**Header:** Make the new processing code available

**Subheader:** Starting a worker with build ID `v2` registers the behavior; it does not yet route all new processing executions to it.

**What to do:**

1. Run `./scripts/start-processing-v2.sh`.
2. Describe the `processing` Worker Deployment.
3. Confirm `processing v2` is polling.
4. Keep `processing v1` running.

**Expected result:**

- Both processing versions can be present.
- `processing v2` is available as a Worker Deployment Version.

**Participant prompt:**

- Why do we keep `processing v1` alive?

## Slide 10

**Exercise activity:** 5. Start `processing v2`

**Header:** Why starting is not the same as promoting

**Subheader:** Availability and routing are separate controls.

**What to observe:**

- A worker process can poll before it becomes current.
- Current version still decides where new executions go.
- Already-pinned `processing v1` executions may still need `v1` workers.

**Risk mitigation:**

- Lets the new code prove it is polling before traffic depends on it.
- Avoids killing workers required by in-flight executions.
- Separates deploy mechanics from traffic movement.

**Facilitator line:**

- Temporal lets us make new behavior available before making it default.

## Slide 11

**Exercise activity:** 6. Promote `processing v2`

**Header:** Promote the dependency first

**Subheader:** New processing executions must land on code that understands the handoff contract.

**What to do:**

1. Set `processing` current version to build ID `v2`.
2. Describe the `processing` Worker Deployment.
3. Confirm `processing v2` is current.
4. Leave `apps` on `v1`.

**Expected result:**

- New `processing.Order` executions are pinned to `processing v2`.
- `apps v1` traffic still works because absent `send_fulfillment` means `true`.

## Slide 12

**Exercise activity:** 6. Promote `processing v2`

**Header:** Why processing moves first

**Subheader:** The dependency must understand the new contract before the caller uses it.

**What to observe:**

- `apps v1` can safely call `processing v2`.
- `processing v2` preserves the Kafka handoff for legacy callers.
- `processing v1` remains only for executions already pinned to it.

**Risk mitigation:**

- Removes the duplicate-fulfillment trap.
- Avoids `apps v2` talking to processing code that ignores `send_fulfillment=false`.
- Keeps the old path alive while the new dependency becomes current.

**Callout:**

- If `apps v2` reaches `processing v1`, processing can still publish Kafka and duplicate fulfillment.

## Slide 13

**Exercise activity:** 7. Implement `apps v2`

**Header:** Move orchestration ownership to `apps.Order`

**Subheader:** Apps now starts fulfillment directly while still using processing for validation and enrichment.

**What to do:**

1. Configure the fulfillment Nexus stub.
2. Start `fulfillment.Order` validation before processing.
3. Set `send_fulfillment=false` in the processing request.
4. Finish fulfillment after processing succeeds.

**Expected result:**

- `apps v2` starts `fulfillment.Order`.
- `apps v2` still calls `processing.Order`.
- `apps v2` tells processing not to send the legacy Kafka handoff.

## Slide 14

**Exercise activity:** 7. Implement `apps v2`

**Header:** Why apps becomes the owner

**Subheader:** Fulfillment starts early, but shipping still waits for processing to succeed.

**What to observe:**

- Address validation and inventory hold can begin while processing runs.
- Processing remains responsible for validation and enrichment.
- Fulfillment receives enriched items only after processing completes.
- The handoff contract is visible in `ProcessOrderRequest`.

**Risk mitigation:**

- Prevents premature label purchase.
- Keeps domain responsibilities separated.
- Makes ownership explicit instead of inferred from worker version.

**Proof to look for later:**

- `ProcessOrderRequest.options.send_fulfillment=false`.

## Slide 15

**Exercise activity:** 8. Start fulfillment workers for the new path

**Header:** Start the new owner before routing traffic to it

**Subheader:** `apps v2` depends on `fulfillment.Order` and the Python fulfillment worker path being available.

**What to do:**

1. Run `./scripts/start-fulfillment.sh`.
2. Confirm Java fulfillment workers are healthy.
3. Confirm the Python worker logs `All workers polling`.
4. Do this before any `apps v2` worker receives traffic.

**Expected result:**

- The fulfillment-side workers required by the new path are polling.
- The new path can make progress once apps routes to it.

## Slide 16

**Exercise activity:** 8. Start fulfillment workers for the new path

**Header:** Why fulfillment starts before apps v2 traffic

**Subheader:** The caller should not route work to a path with no worker capacity.

**What to observe:**

- The baseline deliberately left fulfillment stopped.
- `apps v1 -> processing -> Kafka` did not need fulfillment workers.
- `apps v2 -> fulfillment.Order` does need them.

**Risk mitigation:**

- Prevents new-path orders from waiting on missing fulfillment workers.
- Separates "processing can skip Kafka" from "fulfillment can actually run."
- Makes the new path observable before ramping apps traffic.

**Facilitator line:**

- Start the new owner before the caller starts handing it work.

## Slide 17

**Exercise activity:** 9. Start `apps v2`

**Header:** Make the new apps code available

**Subheader:** Start a second apps worker with build ID `v2`, but keep `apps v1` alive.

**What to do:**

1. Run `./scripts/start-apps-v2.sh`.
2. Describe the `apps` Worker Deployment.
3. Confirm `apps v2` is polling.
4. Do not stop `apps v1`.

**Expected result:**

- `apps v2` is available as a Worker Deployment Version.
- Existing `apps v1` executions can still complete on `v1`.

**Participant prompt:**

- What should happen to orders that already started on `apps v1`?

## Slide 18

**Exercise activity:** 9. Start `apps v2`

**Header:** Why apps v2 can start only now

**Subheader:** The downstream contract and fulfillment workers are ready.

**What to observe:**

- `processing v2` is already current.
- Fulfillment workers are already polling.
- `apps v2` can now safely start new-path orders.
- `apps v1` stays available for pinned executions.

**Risk mitigation:**

- Avoids duplicate fulfillment from old processing code.
- Avoids stranding new-path orders on missing fulfillment workers.
- Keeps in-flight app workflows pinned to the behavior they chose.

**Facilitator line:**

- The sequencing is the safety mechanism.

## Slide 19

**Exercise activity:** 10. Move traffic to `apps v2`

**Header:** Ramp the behavior change

**Subheader:** Use Worker Deployment routing to create an intentional mixed period.

**What to do:**

1. Set `apps v2` as a ramping version at 50 percent.
2. Or set `apps v2` current directly if skipping the mixed period.
3. Watch generated orders continue arriving.
4. Inspect recent `apps.Order` executions and their Deployment Version.

**Expected result during ramp:**

- Some new orders run on `apps v1`.
- Some new orders run on `apps v2`.

## Slide 20

**Exercise activity:** 10. Move traffic to `apps v2`

**Header:** Why ramp the caller

**Subheader:** We are changing behavior, not just replacing a process.

**What to observe:**

- Old-path and new-path orders exist side by side.
- Temporal records which Deployment Version each order used.
- The generator keeps traffic pressure on the rollout.

**Risk mitigation:**

- Limits blast radius.
- Makes old and new behavior directly comparable.
- Lets participants inspect mixed traffic while both versions are intentionally alive.

**Expected split:**

- `apps v1` orders: Kafka fulfillment record.
- `apps v2` orders: `fulfillment.Order`, no Kafka handoff.

## Slide 21

**Exercise activity:** 11. Inspect proof

**Header:** Prove each order's path

**Subheader:** The audit trail should explain who owned fulfillment for each order.

**What to do:**

1. In `apps`, inspect recent `apps.Order` Deployment Versions.
2. In `processing`, inspect `ProcessOrderRequest`.
3. For new-path orders, confirm `options.send_fulfillment=false`.
4. In `fulfillment`, confirm `fulfillment.Order` exists for new-path orders.
5. Query the processing admin endpoint for Kafka fulfillment records.

**Expected result:**

- Old-path orders have Kafka records.
- New-path orders have `fulfillment.Order` workflows and no Kafka records.

## Slide 22

**Exercise activity:** 11. Inspect proof

**Header:** Why the audit trail is the point

**Subheader:** Safe rollout proof should come from workflow history, not guesswork.

**What to observe:**

- Deployment Version on `apps.Order`.
- `send_fulfillment=false` on new-path `processing.Order`.
- `fulfillment.Order` workflow for new-path orders.
- Kafka fulfillment record only for old-path orders.

**Risk mitigation:**

- No hidden feature flag decision.
- No guessing which service owned fulfillment.
- No silent duplicate handoff.

**Facilitator line:**

- If we cannot explain an individual order's path, the migration is not yet safe enough to finish.

## Slide 23

**Exercise activity:** 12. Complete the cutover

**Header:** Promote after the mixed period is understood

**Subheader:** Once the new path is proven, make `apps v2` current.

**What to do:**

1. Set `apps` current version to build ID `v2`.
2. Describe the `apps` and `processing` Worker Deployments.
3. Confirm both deployments are current on `v2`.
4. Stop the generator when the exercise is complete.
5. Stop exercise services when done.

**Expected result:**

- New executions route to `apps v2` and `processing v2`.
- Old pinned executions continue on their original versions until they drain.

## Slide 24

**Exercise activity:** 12. Complete the cutover

**Header:** What the cutover proves

**Subheader:** Code changes, worker availability, and traffic movement are separate concerns.

**What to observe:**

- New worker behavior was introduced with new build IDs.
- Worker Deployment commands controlled which code received new executions.
- Pinned workflows preserved the behavior they started with.
- The routing slip controlled per-order fulfillment ownership.

**Final takeaway:**

- Worker Versioning controls which code receives new executions.
- The routing slip controls who owns fulfillment for each order.
- The rollout sequence prevents duplicate handoff, stranded orders, and replay-unsafe feature-flag behavior.
