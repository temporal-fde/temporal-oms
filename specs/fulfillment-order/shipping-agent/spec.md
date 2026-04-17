# ShippingAgent Workflow Specification

**Feature Name:** `ShippingAgent` — AI-Powered Shipping Rate Selection
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-15
**Updated:** 2026-04-15

---

## Overview

### Executive Summary

The `ShippingAgent` is a long-running Python Temporal workflow that acts as an intelligent,
caching shipping advisor. It is called by `fulfillment.Order` via a Nexus operation in the V2
`fulfillOrder` path, replacing the naive `DeliveryService.getCarrierRates()` activity with an
LLM-driven agent that accounts for real-world supply chain risk, inventory location, and margin
protection.

The workflow is keyed on `customer_id` and never concludes. It caches shipping calculations by
a content hash of the request inputs so repeated calls for the same order characteristics are
served from state without re-invoking the LLM or external APIs.

The agent uses Claude (Anthropic API) with four registered Temporal activities as tools:

- `lookup_inventory_location` — resolve sku_ids to a warehouse address
- `verify_address` — verify a raw address via EasyPost (returns `easypost_address.id` + coordinate)
- `get_carrier_rates` — create an EasyPost Shipment and retrieve carrier rates
- `get_location_events` — query PredictHQ for supply chain risk events at an address

Claude dispatches these tools in whatever order and concurrency it determines appropriate. When
multiple tool calls are returned in a single LLM response, the implementation dispatches them as
concurrent Temporal activities.

The ShippingAgent **recommends**; `fulfillment.Order` **decides**. The response carries a
`ShippingRecommendation` with an outcome enum, the recommended option ID, a margin delta, and
the LLM's reasoning. What `fulfillment.Order` does with that recommendation is its own business
logic.

The spec covers **two call paths** served by the same workflow and the same
`CalculateShippingOptionsRequest`:

- **Fulfillment path** — called by `fulfillment.Order` V2 via Nexus during `fulfillOrder`.
  The caller has already resolved the warehouse from `EnrichedItem` and passes a pre-resolved
  `from_address` in the request. The LLM skips `lookup_inventory_location`.
- **Cart/UI path** — called from the storefront to show shipping rates at checkout.
  No warehouse is pre-resolved; `from_address` is absent. The LLM calls
  `lookup_inventory_location` as its first action to determine origin.

Both paths use identical workflow logic; the system prompt instructs the LLM to branch based on
whether `from_address` is present.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Replace `DeliveryService.getCarrierRates()` in `fulfillment.Order` V2 with an
  LLM-driven agent that reasons about carrier rates, inventory origin, and supply chain risk
- Goal 2: Teach the agentic loop pattern — LLM tool calls map directly to registered Temporal
  activities; students see every step
- Goal 3: Demonstrate durable concurrency — Claude dispatches multiple tools in parallel and
  Temporal executes them as concurrent activities, safely and durably
- Goal 4: Cache shipping calculations by content hash within the long-running agent workflow so
  repeated calls are cheap

### Acceptance Criteria

- [ ] `ShippingAgent` starts via UpdateWithStart from `fulfillment.Order`'s Nexus call
- [ ] `calculate_shipping_options` Update triggers the agentic loop and returns a `ShippingRecommendation`
- [ ] **Fulfillment path**: when `from_address` is present in the request, the LLM skips
      `lookup_inventory_location` and proceeds directly to `verify_address` + `get_location_events`
- [ ] **Cart path**: when `from_address` is absent, the LLM calls `lookup_inventory_location`
      first, then proceeds with the resolved warehouse address
- [ ] The LLM dispatches `verify_address`, `get_carrier_rates`, and `get_location_events`
      (origin + destination) as Temporal activity tool calls in both paths
- [ ] `get_location_events` for origin and destination execute concurrently when Claude requests
      both in the same tool call batch
- [ ] `get_carrier_rates` and any concurrent `get_location_events` batch execute concurrently
- [ ] Results are cached by `fn(locationId, sorted([(skuId, qty)]), postalCode, country)` → hash
      with a configurable TTL; cache hits skip the LLM loop
- [ ] `ShippingRecommendation` outcome is one of: `PROCEED`, `CHEAPER_AVAILABLE`,
      `FASTER_AVAILABLE`, `MARGIN_SPIKE`, `SLA_BREACH`
- [ ] `fulfillment.Order` V2 receives the recommendation and applies its own decision logic
- [ ] Old `fulfillment.Order` V1 workflows (PINNED) complete unaffected on V1 workers; V2 is a
      clean new build-id — no `getVersion()` branching needed

---

## Current State (As-Is)

- `fulfillment.Order` V1 calls `DeliveryService.getCarrierRates()` — a dumb EasyPost rate fetch
  with no SCRM data, no inventory location reasoning, and no LLM
- `shipping_agent.proto` exists with `StartShippingAgentRequest`, a partially-defined
  `CalculateShippingOptionsRequest/Response`, and `GetLocationEventsRequest/Response`
- `values.proto` has `LocationEvent`, `LocationRiskSummary`, and `RiskLevel` — the PredictHQ
  data model is already designed
- `ShippingAgent` workflow is not implemented; Python fulfillment module skeleton exists at
  `python/fulfillment/`

### Pain Points in V1

- Rates fetched at checkout go stale by fulfillment time — margin leakage
- No awareness of weather, infrastructure events, or local disruptions at origin or destination
- Inventory is assumed to ship from a known location; dynamic location lookup is not supported
- No LLM reasoning — the "best" rate is just the cheapest, ignoring SLA or risk context

---

## Desired State (To-Be)

### Architecture

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │ FULFILLMENT PATH                      │ CART/UI PATH                │
 │ (fulfillment.Order V2 via Nexus)      │ (storefront checkout)       │
 │                                       │                             │
 │ from_address: provided (EnrichedItem) │ from_address: absent        │
 └───────────────────────┬───────────────┴──────────────┬──────────────┘
                         │                              │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                          calculateShippingOptions Nexus op
                                        │
                                        ▼
                    ShippingAgent (Python, fulfillment namespace)
                    WorkflowID: customer_id
                    │
                    ├── Cache hit? → return cached ShippingOptionsResult
                    │
                    └── Cache miss → agentic loop:
                        │
                        ├── from_address absent? (cart path only)
                        │   └── LLM turn 1: lookup_inventory_location(sku_ids)
                        │                  → location_id + raw warehouse Address
                        │
                        ├── LLM turn (1 fulfillment / 2 cart): [concurrent]
                        │   ├── verify_address(warehouse raw address)
                        │   │   → easypost_id + coordinate
                        │   └── get_location_events(to_address.coordinate)
                        │       → destination SCRM snapshot
                        │
                        ├── LLM next turn: [concurrent]
                        │   ├── get_carrier_rates(from_easypost_id, to_easypost_id, items)
                        │   │   → carrier rates + shipment_id
                        │   └── get_location_events(from_address.coordinate)
                        │       → origin SCRM snapshot
                        │
                        └── LLM final turn: reason across rates + SCRM (origin + dest)
                            → ShippingRecommendation
                            → cache result (keyed by location_id + items + destination)
                            → return CalculateShippingOptionsResponse

fulfillment.Order applies recommendation (selects rate, sets margin_leak SA, etc.)
```

### Agentic Loop

The workflow runs a standard hand-rolled agentic loop:

1. Check cache — return immediately on hit
2. Build system prompt including:
   - Business rules: margin threshold, SLA targets, recommendation logic
   - Concurrency instruction: "call multiple tools in a single response when there are no
     dependencies between them"
   - Path instruction: "If `from_address` is provided in the request, use it directly as the
     warehouse origin — do not call `lookup_inventory_location`. If `from_address` is absent,
     call `lookup_inventory_location` first to resolve the warehouse address."
3. Build tool definitions for the four registered activities
4. Iterate:
   a. Call Claude (via `call_llm` activity — Anthropic API)
   b. If response contains `tool_use` blocks: dispatch all as concurrent Temporal activities,
      append all `tool_result` blocks to messages, continue loop
   c. If response is text: parse `ShippingRecommendation`, exit loop
5. Cache result keyed by content hash with TTL
6. Return `CalculateShippingOptionsResponse`

### Recommendation Outcomes

| Outcome | Condition | Action for `fulfillment.Order` |
|---|---|---|
| `PROCEED` | Original rate valid, within margin, SLA met | Use original option |
| `CHEAPER_AVAILABLE` | A cheaper option meets the SLA | Consider substituting; margin saved |
| `FASTER_AVAILABLE` | A faster option is within margin | Surface as upgrade; caller decides |
| `MARGIN_SPIKE` | Original cost exceeds `customer_paid_price` + threshold | Use recommended fallback; set `margin_leak` SA |
| `SLA_BREACH` | No available option meets `transit_days_sla` | Escalate; `fulfillment.Order` signals support |

The LLM reasons across origin SCRM, destination SCRM, and carrier rates to arrive at one of
these outcomes and a `recommended_option_id`.

### Caching

Cache key: `fn(locationId, sorted([(skuId, qty)]), destinationPostalCode, destinationCountry)` → SHA-256 hash

- `locationId`: provided in the request (`location_id` field) in the fulfillment path; resolved
  from `lookup_inventory_location` in the cart path — always a stable warehouse identifier
  regardless of how it was resolved
- Sorting skuId+qty pairs makes the key order-independent
- Postal code + country is sufficient for rate zone resolution (street address does not change rates)
- Cache entries store: `ShippingOptionsResult` (rates + SCRM snapshots + recommendation) + `cached_at` timestamp
- TTL is configurable; entries older than TTL are treated as misses and re-fetched
- Cache is in-memory workflow state — survives replays, lost on workflow restart (acceptable given TTL)

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|---|---|---|
| Long-running per-`customer_id` workflow | Enables in-memory caching of rate calculations across multiple calls for the same customer without an external cache | Per-request short-lived workflow — no caching benefit, cold start on every call |
| Hand-rolled agentic loop | Transparent to Workshop students; every LLM ↔ activity step is visible in workflow history | PydanticAI plugin — abstracts the loop, less teachable, adds dependency |
| Fixed registered activities as tools (not dynamic dispatch) | Activities are already registered on the worker by name; no dispatch broker needed | Dynamic activity lookup — adds indirection with no benefit when tools are known |
| LLM dispatches tools (not pre-fetched) | Shows students the LLM making real decisions about what to call and when; more interesting for teaching | Pre-fetch SCRM + rates before LLM — skips the agentic reasoning the workshop is designed to show |
| Concurrency from multi-tool LLM responses | Claude returns multiple `tool_use` blocks in one response when it recognizes no dependency; implementation dispatches them as concurrent activities | Sequential tool dispatch — loses latency benefit, doesn't demonstrate Temporal's concurrent activity pattern |
| ShippingAgent recommends, `fulfillment.Order` decides | Keeps the agent focused on logistics reasoning; business rules (margin policy, SLA enforcement) stay in `fulfillment.Order` | Agent makes the final selection — couples business rules to the Python agent |
| Separate `fulfillment-easypost` (5 rps) and `fulfillment-predicthq` (50 rps) task queues | EasyPost and PredictHQ limits differ by 10×; sharing one queue forces both to the 5 rps floor, wasting 45 rps of PredictHQ capacity | Single shared queue — simpler setup but throttles PredictHQ to EasyPost's limit |
| Worker Versioning (new build-id) for V2 cutover | `fulfillment.Order` is PINNED and has no history to bridge; old workflows complete on V1 workers, new ones pick up V2 cleanly | `Workflow.getVersion()` — unnecessary for a new workflow with no pre-existing history |

### Component Design

#### `ShippingAgent` Workflow (`python/fulfillment`)

- **WorkflowID:** `customer_id`
- **Task Queue:** `fulfillment` (Python worker)
- **Namespace:** `fulfillment`
- **Versioning:** PINNED
- **Interfaces:**
  - Update: `calculate_shipping_options(CalculateShippingOptionsRequest) → CalculateShippingOptionsResponse`
  - Query: `get_options() → ShippingOptionsCache` (reads cached state, no LLM call)
- **State:**
  - `cache: dict[str, ShippingOptionsResult]` — keyed by content hash
  - `cache_metadata: dict[str, CacheEntry]` — TTL tracking per hash

#### Activity Task Queues & Rate Limits

EasyPost and PredictHQ have very different published rate limits, so activities that call them
run on dedicated task queues with per-queue rate limiting. The main `fulfillment` queue is used
for activities that call no external rate-limited API.

| Activity | Task Queue | Rate Limit | Rationale |
|---|---|---|---|
| `lookup_inventory_location` | `fulfillment` | none | Internal config / inventory service; no external rate limit |
| `call_llm` | `fulfillment` | none | Anthropic API; rate limit managed separately at LLM tier |
| `verify_address` | `fulfillment-easypost` | 5 rps | EasyPost index ops: 5 rps documented; write ops load-based — 5 rps is the conservative safe bound |
| `get_carrier_rates` | `fulfillment-easypost` | 5 rps | Same EasyPost account quota; shares the 5 rps budget |
| `get_location_events` | `fulfillment-predicthq` | 50 rps | PredictHQ documented limit |

EasyPost and PredictHQ limits differ by 10×; sharing a single queue would cap PredictHQ at
EasyPost's 5 rps floor, wasting 45 rps of headroom. Separate queues let each API run at its
actual limit.

Worker configuration for each queue sets `max_activities_per_second` on the worker (or
`maxTaskQueueActivitiesPerSecond` server-side) to enforce the limit. Activity options in the
agentic loop dispatch each tool call to its designated task queue.

> **V1 limitation:** Worker-level rate limiting governs only that worker's poll rate. If the
> `fulfillment-easypost` worker is ever scaled to multiple instances, each will independently
> do 5 rps and the aggregate will exceed EasyPost's limit. The correct long-term solution is
> an `EasyPostGateway` workflow: a long-running workflow that accepts EasyPost operations via
> Updates, queues them in-process, and drains at the rate limit — a single durable serializer
> across all callers. This also gives Temporal UI visibility into the EasyPost backlog. Deferred
> to a follow-up spec.

#### Activities (LLM Tools)

All five activities are registered on the Python worker(s) and exposed to Claude as tool
definitions. The agentic loop dispatches them as standard Temporal activities, routing each
to its designated task queue via `ActivityOptions(task_queue=...)`.

**`lookup_inventory_location`**
- **Task Queue:** `fulfillment`
- Input: `[{sku_id, quantity}]`, optional `location_id` override
- Output: warehouse `location_id`, raw warehouse `Address`
- Note: Called by the LLM in the **cart path** only (when `from_address` is absent in the
  request). In the fulfillment path the caller provides `from_address` pre-resolved from
  `EnrichedItem`, so the LLM skips this tool. V1 uses a static config lookup; later versions
  query the Inventory Locations service.

**`verify_address`**
- **Task Queue:** `fulfillment-easypost` (5 rps)
- Input: raw `Address`
- Output: `EasyPostAddress` (id, residential, verified) + `Coordinate` (lat/lng from EasyPost)
- Wraps `EasyPost AddressService.createAndVerify()`
- Note: `to_address` is already verified by `fulfillment.Order`'s `validateOrder`; the agent
  uses the passed-in `easypost_address.id` for the destination. `verify_address` is called for
  the warehouse origin in both paths: in the fulfillment path on the provided `from_address`
  (skipping `lookup_inventory_location`); in the cart path on the address returned by
  `lookup_inventory_location`.

**`get_carrier_rates`**
- **Task Queue:** `fulfillment-easypost` (5 rps)
- Input: `from_easypost_id`, `to_easypost_id`, `[{sku_id, quantity}]`
- Output: `shipment_id`, `[CarrierRate]`
- Wraps EasyPost Shipment creation + rate retrieval

**`get_location_events`**
- **Task Queue:** `fulfillment-predicthq` (50 rps)
- Input: `Coordinate`, `within_km`, `active_from`, `active_to`, `timezone`
- Output: `LocationRiskSummary`, `[LocationEvent]`
- Wraps PredictHQ Events API
- Called twice per calculation (origin + destination) — expected to run concurrently

#### Nexus Service

- **Interface:** `ShippingAgent` Nexus service (in `java/oms/src/main/java/com/acme/oms/services/ShippingAgent.java`)
- **Operation:** `calculateShippingOptions(CalculateShippingOptionsRequest) → CalculateShippingOptionsResponse`
- **Handler:** `ShippingAgentImpl` in Python `fulfillment` workers
- **Endpoint name:** `shipping-agent`
- **Pattern:** UpdateWithStart with `WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING` (same as `fulfillment.Order` ← `apps.Order`)

### Data Model

Proto definitions are the source of truth. This section describes intent only.

#### `proto/acme/fulfillment/domain/v1/shipping_agent.proto` — extensions

**`CalculateShippingOptionsRequest`** — replaces current stub. Carries:
- `order_id`, `customer_id`
- `to_address` (`common.Address` with `easypost_address` already populated from `fulfillment.Order` `validateOrder`)
- `items`: `[{sku_id, quantity}]`
- `from_address`: optional `common.Address` — pre-resolved warehouse origin. The fulfillment
  path populates this from `EnrichedItem` warehouse data. The cart/UI path omits it; the LLM
  calls `lookup_inventory_location` to resolve it.
- `location_id`: optional string — warehouse identifier for cache keying. The fulfillment path
  provides this alongside `from_address` (e.g., `EnrichedItem.warehouse_id`). The cart path
  leaves it absent; the value is resolved by `lookup_inventory_location` before the cache key
  is computed.
- `selected_shipping_option_id`: optional string (the customer's original selection, for comparison)
- `customer_paid_price`: optional `common.Money`
- `transit_days_sla`: optional int32 (days)

**`CalculateShippingOptionsResponse`** — replaces current stub. Carries:
- `recommendation`: `ShippingRecommendation`
- `options`: `[ShippingOption]` (full set of available rates for caller to inspect)
- `cache_hit`: bool

**`ShippingRecommendation`** — new message. Carries:
- `outcome`: `RecommendationOutcome` enum (`PROCEED`, `CHEAPER_AVAILABLE`, `FASTER_AVAILABLE`, `MARGIN_SPIKE`, `SLA_BREACH`)
- `recommended_option_id`: string
- `reasoning`: string (LLM explanation, for logging and support visibility)
- `margin_delta_cents`: int64 (positive = over margin, negative = savings)
- `origin_risk_level`: `RiskLevel` (from `from_address` PredictHQ)
- `destination_risk_level`: `RiskLevel` (from `to_address` PredictHQ)

**`StartShippingAgentRequest`** — extend `ShippingAgentExecutionOptions` with:
- `cache_ttl_secs`: optional int64

#### `proto/acme/common/v1/llm.proto` — new file

Vendor-agnostic LLM message types shared across any service that calls an LLM. Defined in
`common/v1` so they can be reused by future services without importing `shipping_agent.proto`.

- `LlmTextBlock`: `text: string`
- `LlmToolUseBlock`: `id: string`, `name: string`, `input: google.protobuf.Struct` (generates `Dict[str, Any]` in Pydantic)
- `LlmToolResultBlock`: `tool_use_id: string`, `content: string`
- `LlmContentBlock`: `type: string` (discriminator: `"text"` | `"tool_use"` | `"tool_result"`), `text: LlmTextBlock`, `tool_use: LlmToolUseBlock`, `tool_result: LlmToolResultBlock`
  - **No `oneof`** — `protobuf-to-pydantic` assigns `default_factory` to every message field in a `oneof`, making all fields non-None and field-presence discrimination impossible. The `type` string is set explicitly by `call_llm` and checked in the agentic loop.
- `LlmMessage`: `role: LlmRole enum (USER | ASSISTANT)`, `content: repeated LlmContentBlock`
- `LlmResponse`: `content: repeated LlmContentBlock`, `stop_reason: LlmStopReason enum (END_TURN | TOOL_USE)`
- `LlmToolDefinition`: `name: string`, `description: string`, `input_schema: google.protobuf.Struct` (JSON Schema as dict)

#### `proto/acme/common/v1/values.proto` — extension needed

`EasyPostAddress` needs a `coordinate` field (`common.Coordinate` lat/lng) — EasyPost returns
lat/lng from address verification and `get_location_events` requires it. This field should be
added in Phase 1 alongside the `shipping_agent.proto` changes.

#### Dependencies

- **Inventory Locations spec** — defines the warehouse location data model and seed data that
  `lookup_inventory_location` queries. Required before ShippingAgent can run end-to-end.
  V1 workaround: static config with one or two hardcoded warehouse addresses.
- **Inventory Availability spec** — what stock exists at each location. Not required for
  ShippingAgent (it resolves location, not stock levels). Needed for `fulfillment.Order`
  Phase 6 `AllocationsImpl`.

---

## Implementation Strategy

### Phase 1 — Proto Schema

- [ ] Extend `CalculateShippingOptionsRequest` and `CalculateShippingOptionsResponse` with fields above
- [ ] Add `ShippingRecommendation` message and `RecommendationOutcome` enum
- [ ] Add `coordinate` field to `EasyPostAddress` in `common/v1/values.proto` (see Data Model note)
- [ ] Extend `ShippingAgentExecutionOptions` with `cache_ttl_secs`
- [ ] Run `buf generate`; verify Python and Java classes produced

### Phase 2 — Activity Implementations

- [ ] `lookup_inventory_location` — V1: static config lookup by `location_id` or first matching warehouse for sku_ids
- [ ] `verify_address` — EasyPost `AddressService.createAndVerify()`; populate `coordinate` from response
- [ ] `get_carrier_rates` — EasyPost Shipment creation + rate retrieval (already exists as `DeliveryService` in Java; Python version needed)
- [ ] `get_location_events` — PredictHQ Events API (already has proto definition; implement Python activity)
- [ ] `call_llm` — Anthropic API activity: sends messages + tool definitions to Claude, returns response
- [ ] Register activities on the correct workers per task queue:
  - `lookup_inventory_location` + `call_llm` → `fulfillment` worker (no external rate limit)
  - `verify_address` + `get_carrier_rates` → `fulfillment-easypost` worker (`max_activities_per_second=5`)
  - `get_location_events` → `fulfillment-predicthq` worker (`max_activities_per_second=50`)

### Phase 3 — ShippingAgent Workflow

- [ ] `ShippingAgent` workflow class: `@workflow.defn`, WorkflowID = `customer_id`
- [ ] `calculate_shipping_options` Update handler:
  - [ ] Compute cache key (requires `location_id` to be resolved first — from request if present,
        otherwise after `lookup_inventory_location` returns); return cached result if hit and within TTL
  - [ ] Build system prompt with margin threshold, SLA rules, concurrency instruction, and
        path instruction (use provided `from_address` or call `lookup_inventory_location`)
  - [ ] Build tool definitions from the four activity signatures
  - [ ] Agentic loop: call LLM → dispatch concurrent activities for all tool_use blocks → append results → repeat
  - [ ] Parse `ShippingRecommendation` from final text response
  - [ ] Store result in cache with TTL metadata
  - [ ] Return `CalculateShippingOptionsResponse`
- [ ] `get_options` Query handler: return current cache state
- [ ] Unit tests:
  - [ ] Cache hit — LLM not called
  - [ ] Fulfillment path — `from_address` provided; `lookup_inventory_location` not dispatched
  - [ ] Cart path — `from_address` absent; `lookup_inventory_location` dispatched as first tool call
  - [ ] Cache miss + single tool call per turn (sequential path)
  - [ ] Cache miss + multi-tool response (concurrent activity dispatch)
  - [ ] `PROCEED` outcome
  - [ ] `MARGIN_SPIKE` outcome
  - [ ] `SLA_BREACH` outcome
  - [ ] TTL expiry triggers re-fetch

### Phase 4 — Nexus Handler + `fulfillment.Order` V2 Wiring

- [ ] `ShippingAgent` Nexus service interface in `java/oms/src/main/java/com/acme/oms/services/ShippingAgent.java`
- [ ] Python `ShippingAgentImpl` Nexus handler: UpdateWithStart on `ShippingAgent` workflow with `WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING`
- [ ] Register `shipping-agent` Nexus endpoint in Temporal cluster
- [ ] `fulfillment.Order` V2: replace `DeliveryService.getCarrierRates()` in `fulfillOrder` handler with `ShippingAgent` Nexus call
- [ ] `fulfillment.Order` applies `ShippingRecommendation`: selects rate, sets `margin_leak` SA on `MARGIN_SPIKE`, signals support on `SLA_BREACH`
- [ ] Deploy `fulfillment-workers` (Python) with new build-id; mark as default

### Phase 5 — Workshop Scenarios

- [ ] Demo script: fulfillment path happy path — `from_address` provided, LLM skips
      `lookup_inventory_location`, returns `PROCEED`
- [ ] Demo script: cart path — `from_address` absent, LLM calls `lookup_inventory_location`
      first, then proceeds; shows the additional tool call turn in workflow history
- [ ] Demo script: margin spike (`MARGIN_SPIKE` → fallback selected, `margin_leak` visible in Temporal UI)
- [ ] Demo script: concurrent tool dispatch visible in workflow history
- [ ] Demo script: cache hit (second call with same inputs is instant, regardless of path)
- [ ] Slide / README: before (V1 dumb rate fetch) vs after (ShippingAgent) contrast;
      fulfillment path vs cart path call flows

---

## Testing Strategy

### Unit Tests (Temporal Python test framework)

- Mock the `call_llm` activity to control what tool calls the LLM "requests"
- Assert activities are dispatched concurrently when LLM returns multiple `tool_use` blocks
- Assert cache is populated after first call and returned on second call without LLM invocation
- Assert each `RecommendationOutcome` is produced under the correct input conditions

### Integration Tests

- End-to-end: `fulfillment.Order` V2 `fulfillOrder` → Nexus → `ShippingAgent` UpdateWithStart → agentic loop → `ShippingRecommendation` → `fulfillment.Order` applies recommendation
- Concurrency: verify origin + destination `get_location_events` appear as concurrent activities in workflow history

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| LLM response structure is unpredictable — `ShippingRecommendation` parsing fails | High | Medium | Use structured output / JSON mode in Claude API call; validate schema before caching |
| Inventory Locations spec not ready — `lookup_inventory_location` has nothing to query | High | High | V1 workaround: static config with hardcoded warehouse(s); unblock Workshop with seed data |
| EasyPost write-op rate limit undocumented — actual limit for `createAndVerify` / Shipment creation may differ from the 5 rps index limit | Medium | Medium | 5 rps is the safe conservative bound; monitor 429 responses in workshop and raise if sustained throttling is observed |
| PredictHQ API latency spikes degrade UpdateWithStart round-trip | Medium | Low | Set activity `start_to_close_timeout`; LLM can reason with partial data if one tool times out |
| `EasyPostAddress` missing `coordinate` — `get_location_events` cannot run | High | Medium | Noted in Data Model section; must be added in Phase 1 before Phase 3 can proceed |
| Long-running `ShippingAgent` accumulates unbounded cache entries | Low | Medium | TTL eviction on cache reads; `continue_as_new` if cache map exceeds size threshold |

---

## Open Questions

All open questions resolved:

- [x] What is the PredictHQ `within_km` radius default for Workshop demos? **50km**
- [x] What is the default `cache_ttl_secs`? **1800 (30 minutes)**
- [x] Should `SLA_BREACH` signal a support workflow directly from `ShippingAgent`, or return the outcome and let `fulfillment.Order` decide? **`fulfillment.Order` handles it** — ShippingAgent returns the `SLA_BREACH` outcome; `fulfillment.Order` decides what to do (consistent with "recommends, not decides" principle)

---

## References

- [`shipping_agent.proto`](../../../proto/acme/fulfillment/domain/v1/shipping_agent.proto)
- [`fulfillment/domain/v1/values.proto`](../../../proto/acme/fulfillment/domain/v1/values.proto) — `LocationEvent`, `LocationRiskSummary`, `RiskLevel`
- [`fulfillment.Order` spec](../fulfillment-order-workflow/spec.md) — Phase 7: V2 wiring
- [Temporal AI Cookbook — Agentic Loop with Claude (Python)](https://docs.temporal.io/ai-cookbook/agentic-loop-tool-call-claude-python)
- [EasyPost Java SDK — AddressService](https://easypost.github.io/easypost-java/com/easypost/service/AddressService.html)
- [PredictHQ Events API](https://docs.predicthq.com/api/events)
