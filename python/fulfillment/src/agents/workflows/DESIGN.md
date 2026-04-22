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

if all(r.cost > request.customer_paid_price.units for r in rates.options):
    alt = await find_alternate_warehouse(items, exclude=[lookup.address])
    if alt:
        rates = await get_carrier_rates(alt.easypost.id, verify.address.easypost.id)
        if all(r.cost > request.customer_paid_price.units for r in rates.options):
            return MARGIN_SPIKE  # still too expensive from alternate
    else:
        return MARGIN_SPIKE

if fastest.transit_days > request.transit_days_sla:
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
PredictHQ queries) are not re-executed.
