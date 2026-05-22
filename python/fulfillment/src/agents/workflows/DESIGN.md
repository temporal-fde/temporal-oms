# ShippingAgent Design Notes

## Deterministic pipeline vs. LLM ReAct loop

### What it would look like without an agent

```python
lookup, verify = await gather(lookup_inventory_location(items), verify_address(to_address))

rates, origin_risk, dest_risk = await gather(
    get_carrier_rates(lookup.address.easypost.id, verify.address.easypost.id),
    get_location_events(lookup.address.easypost.coordinate, window),
    get_location_events(verify.address.easypost.coordinate, window),
)

# All business logic lives here as code
cheapest = min(rates.options, key=lambda r: r.cost)
fastest  = min(rates.options, key=lambda r: r.transit_days)

if all(r.cost > request.selected_shipment.paid_price.units for r in rates.options):
    alt = await find_alternate_warehouse(items, exclude=[lookup.address])
    if alt:
        rates = await get_carrier_rates(alt.easypost.id, verify.address.easypost.id)
        if all(r.cost > request.selected_shipment.paid_price.units for r in rates.options):
            return MARGIN_SPIKE  # still too expensive from alternate
    else:
        return MARGIN_SPIKE

if fastest.transit_days > request.selected_shipment.easypost.selected_rate.delivery_days:
    return SLA_BREACH

if dest_risk.summary.overall_risk_level >= RISK_LEVEL_HIGH:
    # Do we pick faster? Warn? Check alternate carriers? How do we weigh this against cost?
    ...

# cheapest vs fastest vs risk tradeoff — now what?
```

The conditional tree grows fast once margin, SLA, and risk interact. Every new
business rule is a code change, a deploy, and a test case.

### Why use an LLM instead

The business logic lives in the prompt, not the workflow. When the margin rule
changes, you edit a string. When a new outcome is added, you add a sentence.
The workflow just orchestrates durable execution of whatever the LLM decides.

The `find_alternate_warehouse` branch is the key justification for a genuine
ReAct loop: the LLM sees that all rates exceed the paid price and *decides* to
look for a closer warehouse. That second `get_carrier_rates` call cannot be
pre-planned — it only happens if the first result triggers it. A pipeline
cannot express this without hard-coding the same conditional the LLM is
replacing.

### Why Temporal specifically

A naive agent loop (plain Python calling Anthropic) loses its full conversation
history on a process crash. The agent restarts cold, re-calls completed tools,
and may branch differently on the second attempt.

With Temporal the message history is the event log. The agent resumes
mid-conversation with every prior tool result intact — the LLM does not
re-evaluate decisions it already made, and completed activities (EasyPost calls,
location event lookups) are not re-executed.

## Recommendation cache

`ShippingAgent` is a long-running workflow keyed by `customer_id`, so it can keep
an in-workflow cache without introducing Redis, a database table, or another
consistency boundary. The cache is `self._cache: dict[str, ShippingOptionsResult]`
and stores the final recommendation, all accumulated shipping options, and the
`cached_at` workflow timestamp.

The workflow resolves context before checking the cache:

1. Resolve the origin warehouse with `lookupInventoryAddress`.
2. Use the caller's verified `to_address.easypost` when present; otherwise call
   `verify_address`.
3. Compute the cache key from origin EasyPost ID, destination postal code and
   country, sorted `(sku_id, quantity)` pairs, and selected-shipment context.

The selected-shipment context is part of the key because margin and SLA decisions
depend on it. Two requests with the same origin, destination, and items should
not share a recommendation if one request paid normal shipping and another paid
one cent, or if one promised five delivery days and another promised zero.

On a valid hit, the workflow returns the cached recommendation and options with
`cache_hit=True`. That skips prompt construction, `call_llm`, carrier-rate
lookup, location-event lookup, and alternate-warehouse reasoning. It does not
skip the pre-loop origin lookup, or destination verification when the destination
was not already verified, because those values are needed to build the key.

Entries expire by age: `workflow.now() - cached_at < _cache_ttl_secs`. The
default is `_DEFAULT_CACHE_TTL_SECS = 1800` seconds. A workflow can override the
TTL only at start with `StartShippingAgentRequest.execution_options.cache_ttl_secs`.
Expired entries are treated as misses and overwritten when the fresh
recommendation is produced.

## Determinism and TTL configuration

The age check itself is replay-safe because it uses `workflow.now()`, not wall
clock time. The replay risk is the TTL default. The normal Nexus handler starts
`ShippingAgent` with only `customer_id`, so those workflows currently get the
code fallback of 1800 seconds.

Changing `_DEFAULT_CACHE_TTL_SECS` while existing default-TTL workflows are open
can change replay branching. A cached result that was valid under the old value
may be expired under the new value, causing replay to schedule the LLM/tool
activities where history says the workflow returned a cache hit.

Future improvements should remove that configuration risk before changing the
default:

- Pass `ShippingAgentExecutionOptions(cache_ttl_secs=1800)` from the Nexus
  handler so the TTL is recorded in workflow history for new executions.
- Use Temporal patch/versioning semantics for any default change that must
  coexist with open workflows started under the old behavior.
- Migrate or `continue_as_new` long-running workflows with an explicit TTL before
  changing the fallback constant.
- Add a read-only cache query if operators need to inspect cache contents without
  reading raw workflow history.
