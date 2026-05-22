# ShippingAgent Workflow Specification

**Feature Name:** `ShippingAgent` — AI-Powered Shipping Rate Selection
**Status:** Implemented for workshop fixture-backed path; live location-events enrichment deferred
**Owner:** Temporal FDE Team
**Created:** 2026-04-15
**Updated:** 2026-05-05

---

## Overview

### Executive Summary

The `ShippingAgent` is a long-running Python Temporal workflow that acts as an intelligent,
caching shipping advisor. It is called by `fulfillment.Order` via a Nexus operation in the V2
`fulfillOrder` path, replacing the naive `DeliveryService.getCarrierRates()` activity with an
LLM-driven agent that accounts for real-world supply chain risk, inventory location, and margin
protection.

The workflow is keyed on `customer_id` and never concludes. It caches shipping recommendations by
a content hash of the resolved origin, destination rate zone, items, and selected-shipment context.
Repeated calls for the same shipping decision are served from workflow state without re-invoking
the LLM, rate lookup, location-events lookup, or alternate-warehouse reasoning loop.

The agent uses Claude (Anthropic API) with four external tool definitions plus an internal
finalization tool:

- `lookup_inventory_address` — available to resolve sku_ids to a warehouse address
- `get_carrier_rates` — retrieve fixture-backed shipment rates through `enablements-api`
- `get_location_events` — query for supply chain risk events at an address
- `find_alternate_warehouse` — locate a different warehouse when all rates fail margin or SLA
- `finalize_recommendation` — internal workflow-handled tool for structured final output

Destination verification runs before the LLM loop when the caller provides an unverified address;
it is not exposed as an LLM tool in the current implementation.

Claude dispatches these tools in whatever order and concurrency it determines appropriate. When
multiple tool calls are returned in a single LLM response, the implementation dispatches them as
concurrent Temporal activities.

The ShippingAgent **recommends**; `fulfillment.Order` **decides**. The response carries a
`ShippingRecommendation` with an outcome enum, the recommended option ID, a margin delta, and
the LLM's reasoning. What `fulfillment.Order` does with that recommendation is its own business
logic.

Both the fulfillment path (`fulfillment.Order` V2 via Nexus) and the cart/UI path (storefront
checkout rates) use the same workflow and the same `RecommendShippingOptionRequest`. The caller
always provides `items` with `sku_id`; the workflow resolves the warehouse origin from inventory
before the LLM loop. There is no pre-resolved `from_address` in the request — warehouse resolution
is the agent workflow's job regardless of caller.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Replace `DeliveryService.getCarrierRates()` in `fulfillment.Order` V2 with an
  LLM-driven agent that reasons about carrier rates, inventory origin, and supply chain risk
- Goal 2: Teach the agentic loop pattern — LLM tool calls map directly to registered Temporal
  activities; students see every step
- Goal 3: Demonstrate durable concurrency — Claude dispatches multiple tools in parallel and
  Temporal executes them as concurrent activities, safely and durably
- Goal 4: Cache shipping recommendations by content hash within the long-running agent workflow so
  repeated calls are cheap

### Acceptance Criteria

- [ ] `ShippingAgent` starts via UpdateWithStart from `fulfillment.Order`'s Nexus call
- [ ] `recommend_shipping_option` Update triggers the agentic loop and returns a `ShippingRecommendation`
- [ ] The workflow resolves the warehouse origin from `sku_id`s before cache lookup and LLM
      reasoning — no `from_address` is provided in the request by either caller
- [ ] The LLM dispatches `get_carrier_rates` and `get_location_events` (origin + destination)
      as Temporal activity tool calls; `verify_address` is a workflow-level fallback for
      unverified destination addresses only
- [ ] `get_location_events` for origin and destination execute concurrently when Claude requests
      both in the same tool call batch
- [ ] `get_carrier_rates` and any concurrent `get_location_events` batch execute concurrently
- [ ] Results are cached by
      `fn(origin_easypost_id, sorted([(skuId, qty)]), destinationPostalCode,
      destinationCountry, selectedShipmentContext)` → hash with a configurable TTL; cache hits
      skip the LLM/tool loop after origin and destination have been resolved
- [ ] `ShippingRecommendation` outcome is one of: `PROCEED`, `CHEAPER_AVAILABLE`,
      `FASTER_AVAILABLE`, `MARGIN_SPIKE`, `SLA_BREACH`
- [ ] `fulfillment.Order` V2 receives the recommendation and applies its own decision logic
- [ ] Old `fulfillment.Order` V1 workflows (PINNED) complete unaffected on V1 workers; V2 is a
      clean new build-id — no `getVersion()` branching needed
- [ ] `find_alternate_warehouse` is called before any `MARGIN_SPIKE` or `SLA_BREACH` finalize
- [ ] Post-loop rejection re-invokes the LLM when `MARGIN_SPIKE`/`SLA_BREACH` is finalized
      without a prior `find_alternate_warehouse` call; second finalize is accepted once the
      tool has been called
- [x] `MARGIN_SPIKE` path is reliably exercised in tests by setting
      `selected_shipment.paid_price.units=1`

---

## Current State (As-Is)

- `fulfillment.Order` V2 calls `ShippingAgent` through Nexus and applies the returned
  recommendation.
- Shipping and location-event tool activities call `enablements-api`; runtime EasyPost calls have
  been removed from the workshop path.
- `RecommendShippingOptionRequest` carries `selected_shipment`, whose `paid_price` and
  `easypost.selected_rate.delivery_days` drive deterministic margin and SLA scenarios.
- `ShippingAgent` accumulates and de-dupes every option returned by primary and alternate
  `get_carrier_rates` calls so `fulfillment.Order` can select any recommended option ID.
- `ShippingAgent` stores `ShippingOptionsResult` entries in workflow state with a default
  1800-second (30-minute) TTL. The current Nexus handler starts workflows with only
  `customer_id`, so normal service calls use the workflow code's default TTL unless a workflow
  was started directly with `execution_options.cache_ttl_secs`.

### Pain Points in V1

- Rates fetched at checkout go stale by fulfillment time — margin leakage
- No awareness of weather, infrastructure events, or local disruptions at origin or destination
- Inventory is assumed to ship from a known location; dynamic location lookup is not supported
- No LLM reasoning — the "best" rate is just the cheapest, ignoring SLA or risk context

---

## Desired State (To-Be)

### Architecture

```
fulfillment.Order V2 (Nexus)          Cart/UI (storefront)
items: [{sku_id, qty}]                items: [{sku_id, qty}]
to_address: (pre-verified)            to_address: (from user input)
        │                                     │
        └──────────────┬──────────────────────┘
                       │  recommendShippingOption Update
                       ▼
       ShippingAgent (Python, fulfillment namespace)
       WorkflowID: customer_id
       │
       ├── Resolve origin + destination
       │
       ├── Cache hit? → return cached ShippingOptionsResult
       │
       └── Cache miss → agentic loop:
           │
           ├── LLM turn 1: [concurrent tool calls with resolved addresses]
           │   ├── get_carrier_rates(origin_easypost_id, destination, items)
           │   │   → carrier rates
           │   ├── get_location_events(origin.address.coordinate)   ← origin SCRM
           │   └── get_location_events(to_address.coordinate)       ← destination SCRM
           │
           └── LLM final turn: reason across rates + SCRM (origin + dest)
               → ShippingRecommendation
               → cache result (keyed by origin + items + destination + selected-shipment context)
               → return RecommendShippingOptionResponse

fulfillment.Order applies recommendation (selects rate, sets margin_leak SA, etc.)
```

### Agentic Loop

The workflow runs a standard hand-rolled agentic loop:

1. Pre-fetch workflow-owned context before the LLM loop:
   a. Call `lookupInventoryAddress` through the integrations Nexus endpoint to resolve the origin
      warehouse from `items`.
   b. If `to_address.easypost.id` is absent, call `verify_address`; otherwise use the caller's
      verified destination.
2. Compute the cache key from the resolved origin, destination postal/country, sorted items, and
   selected-shipment context. Return the cached `ShippingOptionsResult` on hit if it is still
   inside the workflow's TTL.
3. Build system prompt via `build_system_prompt` LocalActivity — result is memoized in event
   history so prompt changes do not affect replay of in-flight workflows and do not require a
   build-id bump. The activity receives the full `RecommendShippingOptionRequest` and returns
   the system prompt string. Includes: margin threshold rule, SLA rule, path instruction
   (warehouse resolution vs. pre-verified `from_address`), concurrency instruction, and final
   `finalize_recommendation` tool instruction.
4. Build tool definitions: the four external tool definitions plus a fifth internal-only
   `finalize_recommendation` tool (see Design Decisions — Structured output via `finalize_recommendation`)
5. Iterate:
   a. Call Claude (via `call_llm` activity — Anthropic API)
   b. If response contains `tool_use` blocks and one block is `finalize_recommendation`:
      - If outcome is `MARGIN_SPIKE` or `SLA_BREACH` and `find_alternate_warehouse` was
        not called in any prior turn: inject a `tool_result` rejection block and continue
        the loop — the LLM is forced to call the tool before the outcome is accepted
        (see Phase 6 Hardening — post-loop enforcement)
      - Otherwise: extract `ShippingRecommendation` directly from the tool input dict
        (always valid SDK-serialized JSON — no text parsing) and exit the loop
   c. If response contains `tool_use` blocks with no `finalize_recommendation`: dispatch
      all real activity tools as concurrent Temporal activities, track any
      `find_alternate_warehouse` calls, append all `tool_result` blocks to messages,
      continue loop
   d. If `END_TURN` fires without a preceding `finalize_recommendation` call: raise a
      retryable `ApplicationError` — the LLM did not follow instructions
6. Cache result keyed by content hash with `cached_at=workflow.now()`
7. Return `RecommendShippingOptionResponse`

### Recommendation Outcomes

| Outcome | Condition | Action for `fulfillment.Order` |
|---|---|---|
| `PROCEED` | Original rate valid, within margin, SLA met | Use original option |
| `CHEAPER_AVAILABLE` | A cheaper option meets the SLA | Consider substituting; margin saved |
| `FASTER_AVAILABLE` | A faster option is within margin | Surface as upgrade; caller decides |
| `MARGIN_SPIKE` | All rates exceed `selected_shipment.paid_price`; no alternate warehouse saves it | Use recommended fallback; `fulfillment.Order` records `margin_leak` when selected rate exceeds `shipping_margin` |
| `SLA_BREACH` | No rate meets `selected_shipment.easypost.selected_rate.delivery_days`; no alternate warehouse offers a faster option | Use fastest available rate (best-effort); `fulfillment.Order` sets `sla_breach_days` SA (actual_days − promised_days); `is_fallback=true` on `ShippingSelection` |

Before finalizing `MARGIN_SPIKE` or `SLA_BREACH`, the agent **must** call `find_alternate_warehouse`.
A warehouse closer to the destination may offer rates that resolve the margin overage or meet
the SLA — the outcome should only be `MARGIN_SPIKE`/`SLA_BREACH` once that possibility is
exhausted. This requirement is enforced at two levels: the system prompt makes it explicit, and
the workflow loop rejects a premature finalize and re-invokes the LLM (see Phase 6 Hardening).

The LLM reasons across origin SCRM, destination SCRM, carrier rates, and (when needed) the
alternate warehouse response to arrive at one of these outcomes and a `recommended_option_id`.
For `MARGIN_SPIKE`, `recommended_option_id` is the cheapest available rate (even if it exceeds
the paid price). For `SLA_BREACH`, `recommended_option_id` is the fastest available rate (even
if it misses the SLA) — the order still ships, it just ships late. `recommended_option_id` is
never empty.

### Caching

Cache key:
`fn(origin_easypost_id, sorted([(skuId, qty)]), destinationPostalCode, destinationCountry, selectedShipmentContext)` → first 16 hex chars of SHA-256.

- `origin_easypost_id` comes from the pre-loop `lookupInventoryAddress` Nexus operation. The cache
  check is therefore after origin resolution, not before the workflow has an origin.
- Destination matching uses postal code + country from the verified EasyPost destination. This is
  sufficient for the fixture-backed rate-zone behavior; street lines are intentionally excluded.
- Sorting skuId+qty pairs makes item order irrelevant.
- `selectedShipmentContext` includes selected rate ID, selected delivery days, paid-price currency,
  and paid-price units when `selected_shipment` is explicitly present. This prevents a cached
  normal recommendation from being reused for a margin-spike or SLA-breach scenario with the same
  origin, destination, and items.
- Cache entries store `ShippingOptionsResult`: the final `ShippingRecommendation`, all accumulated
  `ShippingOption` values returned by primary/alternate rate lookups, and `cached_at`.
- The default TTL is `_DEFAULT_CACHE_TTL_SECS = 1800` seconds (30 minutes). A workflow can override
  it at start with `StartShippingAgentRequest.execution_options.cache_ttl_secs`; otherwise it uses
  the code default.
- A hit returns `cache_hit=true` and skips prompt construction, `call_llm`, carrier-rate lookup,
  location-events lookup, and alternate-warehouse calls. The origin lookup, and destination
  verification when needed, still run before the key can be checked.
- Expired entries are treated as misses and overwritten by the refreshed result. There is no
  proactive cleanup pass.
- Cache state is workflow state. It survives worker restarts and workflow replay, but it is not an
  external shared cache and must be carried forward explicitly if the workflow later uses
  `continue_as_new`.

Temporal determinism note: `workflow.now()` is replay-safe for the age calculation. The replay risk
is changing the code default for `_DEFAULT_CACHE_TTL_SECS` while existing workflows that did not
record an explicit TTL are still open. A different fallback TTL can make a replayed cache branch
expire where the original execution returned a hit, or vice versa. Future changes to the default
must use recorded workflow input, Temporal versioning/patching, or a controlled migration.

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|---|---|---|
| Long-running per-`customer_id` workflow | Enables in-memory caching of recommendations across multiple calls for the same customer without an external cache | Per-request short-lived workflow — no caching benefit, cold start on every call |
| Hand-rolled agentic loop | Transparent to Workshop students; every LLM ↔ activity step is visible in workflow history | PydanticAI plugin — abstracts the loop, less teachable, adds dependency |
| Fixed registered activities as tools (not dynamic dispatch) | Activities are already registered on the worker by name; no dispatch broker needed | Dynamic activity lookup — adds indirection with no benefit when tools are known |
| LLM dispatches tools (not pre-fetched) | Shows students the LLM making real decisions about what to call and when; more interesting for teaching | Pre-fetch SCRM + rates before LLM — skips the agentic reasoning the workshop is designed to show |
| Concurrency from multi-tool LLM responses | Claude returns multiple `tool_use` blocks in one response when it recognizes no dependency; implementation dispatches them as concurrent activities | Sequential tool dispatch — loses latency benefit, doesn't demonstrate Temporal's concurrent activity pattern |
| ShippingAgent recommends, `fulfillment.Order` decides | Keeps the agent focused on logistics reasoning; business rules (margin policy, SLA enforcement) stay in `fulfillment.Order` | Agent makes the final selection — couples business rules to the Python agent |
| Workflow resolves inventory origin; no `from_address` in request | Caller provides `sku_id`s — warehouse resolution is the agent workflow's responsibility regardless of whether the caller is `fulfillment.Order` (EnrichedItem skus) or cart (cart item skus). Avoids a two-path design where callers must know about warehouse assignment. | Pre-resolve warehouse in caller and pass `from_address` — couples callers to inventory logic and creates a split path with different behavior |
| Separate `fulfillment-shipping` task queue | Shipping integration activities are blocking HTTP calls to `enablements-api`; isolating them keeps LLM/agent work on the `agents` queue and makes future vendor throttling easy to add behind the same boundary | Single shared queue — simpler but less operationally clear |
| Worker Versioning (new build-id) for V2 cutover | `fulfillment.Order` is PINNED and has no history to bridge; old workflows complete on V1 workers, new ones pick up V2 cleanly | `Workflow.getVersion()` — unnecessary for a new workflow with no pre-existing history |
| System prompt built in `build_system_prompt` LocalActivity (not inline workflow code) | LocalActivity result is memoized in event history; on replay, Temporal returns the memoized value and ignores the current implementation. Prompt text can be updated and redeployed without a build-id bump — in-flight workflows replay against the original prompt from history. Inline function: any text change produces different `call_llm` args than history → non-determinism error on replay. | Inline `_build_system_prompt` function — simple but couples prompt iteration to build-id lifecycle |
| Structured output via `finalize_recommendation` tool, not raw JSON text parsing | Observed in production: models (especially smaller ones like `claude-haiku-4-5`) frequently add preamble, analysis prose, or markdown code fences before or instead of the requested JSON, causing `json.loads()` to fail non-retryably. Tool call inputs are always SDK-serialized, structurally valid JSON — prose contamination is impossible. This is Anthropic's recommended approach for guaranteed structured output: define a tool the model must call to submit its answer, give it a strict JSON Schema with enum constraints, and extract the recommendation directly from `block.tool_use.input`. The `finalize_recommendation` tool is never dispatched to an activity; the loop detects it by name and exits. | System prompt instruction "output only raw JSON — no preamble, no markdown": the model can and does ignore this under certain prompting conditions; failures accumulate silently until a retry happens to comply |
| Post-loop rejection enforces `find_alternate_warehouse` before MARGIN_SPIKE/SLA_BREACH | Prompt-only instructions are stochastic — the LLM may skip the tool call, especially under token pressure or on less capable models. The workflow loop tracks a `alternate_warehouse_called` boolean; if `finalize_recommendation` arrives with a negative outcome before the tool was called, the loop injects a `tool_result` rejection and re-invokes the LLM. This is a hard workflow-layer guarantee that requires zero prompt compliance. | Prompt instruction only ("MANDATORY: call find_alternate_warehouse first") — works in most cases but not all; failures are silent and produce incorrect outcomes rather than retryable errors |
| Test trigger via `selected_shipment.paid_price.units=1` (1 cent), not SKU-based rate injection | To exercise the `find_alternate_warehouse` path, the MARGIN_SPIKE condition must be reliably induced. The selected shipment paid price is the direct trigger in the prompt margin rule, and fixture-backed rates deterministically exceed one cent. | Intercept `get_carrier_rates` dispatch and return synthetic high rates for test SKU prefixes — adds production-path complexity, creates a maintenance surface, and only works in test |

### Component Design

#### `ShippingAgent` Workflow (`python/fulfillment`)

- **WorkflowID:** `customer_id`
- **Task Queue:** `fulfillment` (Python worker)
- **Namespace:** `fulfillment`
- **Versioning:** PINNED
- **Interfaces:**
  - Update: `recommend_shipping_option(RecommendShippingOptionRequest) → RecommendShippingOptionResponse`
  - Query: none currently; `ShippingOptionsCache` exists in proto as a future inspection surface
- **State:**
  - `_cache: dict[str, ShippingOptionsResult]` — keyed by content hash
  - `_cache_ttl_secs: int` — workflow-level TTL, defaulting to 1800 unless provided at workflow start

#### Activity Task Queues & Rate Limits

Shipping activities run on a dedicated queue. All other agent activities run on the main `agents`
queue.

| Activity | Task Queue | Rate Limit | Rationale |
|---|---|---|---|
| `lookup_inventory_location` | `agents` | none | Internal config / inventory service; no external rate limit |
| `call_llm` | `agents` | none | Anthropic API; rate limit managed separately at LLM tier |
| `get_location_events` | `agents` | none | First pass delegates to `enablements-api` and returns no-risk fixture data |
| `verify_address` | `fulfillment-shipping` | worker-local guard | Fixture-backed shipping HTTP call to `enablements-api` |
| `get_carrier_rates` | `fulfillment-shipping` | worker-local guard | Fixture-backed shipping HTTP call to `enablements-api` |

The `fulfillment-shipping` worker keeps a conservative local activity rate guard. There is no
runtime EasyPost quota in the fixture-backed path.

#### Activities and LLM Tools

The Python worker registers the activities and Nexus operations needed by the workflow. The
LLM-visible tools are `lookup_inventory_address`, `get_carrier_rates`, `get_location_events`,
and `find_alternate_warehouse`, plus the workflow-handled `finalize_recommendation` tool.
`verify_address` is a pre-loop workflow activity, not an LLM-visible tool.

**`lookup_inventory_address` / `lookup_inventory_location`**
- **Task Queue:** `fulfillment`
- Input: `[{sku_id, quantity}]`
- Output: `[{address: Address, items: [{sku_id, quantity}]}]` — items grouped by warehouse.
  Each group's `address.easypost_address` is pre-populated from seed data; `easypost_address.id`
  is ready to use as carrier origin and cache key component.
- Note: The current workflow resolves the origin before cache lookup and before the LLM loop, so
  this lookup is not normally the first LLM-selected tool call. The lookup tool remains available
  to the LLM, but the cache key is based on the pre-loop resolved origin.

**`verify_address`**
- **Task Queue:** `fulfillment-shipping`
- Input: raw `Address`
- Output: `EasyPostAddress` (id, residential, verified) + `Coordinate` from fixtures
- Calls `enablements-api` shipping verification
- Note: Fallback only in normal operation. `to_address` is pre-verified by `fulfillment.Order`
  `validateOrder`; the warehouse address returned by origin lookup is pre-verified from seed data.
  When `to_address.easypost.id` is missing, the workflow calls this before cache lookup so the
  destination is concrete before the LLM loop.

**`get_carrier_rates`**
- **Task Queue:** `fulfillment-shipping`
- Input: `from_easypost_id`, `to_easypost_id`, `[{sku_id, quantity}]`
- Output: `shipment_id`, `[CarrierRate]`
- Calls `enablements-api` for fixture-backed shipment rates. Response options from every primary
  and alternate rate lookup are accumulated and de-duped before the final response is returned.

**`get_location_events`**
- **Task Queue:** `agents`
- Input: `Coordinate`, `within_km`, `active_from`, `active_to`, `timezone`
- Output: `LocationRiskSummary`, `[LocationEvent]`
- Currently stubbed — returns no events; see `specs/fulfillment/location-events/spec.md` for planned implementation
- Called twice per recommendation (origin + destination) — expected to run concurrently

**`find_alternate_warehouse`**
- **Task Queue:** Nexus (`fulfillment` namespace via `integrations` endpoint)
- Input: `FindAlternateWarehouseRequest` — `items: [ShippingLineItem]`, `exclude_address` (the warehouse already tried)
- Output: `FindAlternateWarehouseResponse` — `address: Address` (empty if none available)
- Calls the Integrations API (Nexus) to locate a different warehouse that can fulfill the same items
- Called at most once per agentic loop execution — only when a MARGIN_SPIKE or SLA_BREACH condition is detected before finalizing
- An empty `address` in the response is a valid outcome; it confirms no alternate exists and the agent proceeds to finalize the negative outcome

#### Nexus Service

- **Interface:** `ShippingAgent` Nexus service (in `java/oms/src/main/java/com/acme/oms/services/ShippingAgent.java`)
- **Operation:** `recommendShippingOption(RecommendShippingOptionRequest) → RecommendShippingOptionResponse`
- **Handler:** `ShippingAgentImpl` in Python `fulfillment` workers
- **Endpoint name:** `shipping-agent`
- **Pattern:** UpdateWithStart with `WORKFLOW_ID_CONFLICT_POLICY_USE_EXISTING` (same as `fulfillment.Order` ← `apps.Order`)

### Data Model

Proto definitions are the source of truth. This section describes intent only.

#### `proto/acme/fulfillment/domain/v1/shipping_agent.proto` — extensions

**`RecommendShippingOptionRequest`** — replaces current stub. Carries:
- `order_id`, `customer_id`
- `to_address` (`common.Address` with `easypost_address` already populated from `fulfillment.Order`
  `validateOrder` in the fulfillment path; raw address in the cart path — the workflow calls
  `verify_address` before cache lookup if `easypost_address` is absent)
- `items`: `[{sku_id, quantity}]` — the workflow resolves the warehouse origin from these before
  cache lookup and LLM reasoning; no `from_address` is provided by the caller
- `selected_shipment`: optional `common.Shipment`; `paid_price` supplies the customer-paid margin
  context, and `easypost.selected_rate.delivery_days` supplies the selected delivery-days SLA.

**`RecommendShippingOptionResponse`** — replaces current stub. Carries:
- `recommendation`: `ShippingRecommendation`
- `options`: `[ShippingOption]` (full accumulated set of available rates, including rates fetched
  after alternate warehouse lookup)
- `cache_hit`: bool

**`ShippingRecommendation`** — new message. Carries:
- `outcome`: `RecommendationOutcome` enum (`PROCEED`, `CHEAPER_AVAILABLE`, `FASTER_AVAILABLE`, `MARGIN_SPIKE`, `SLA_BREACH`)
- `recommended_option_id`: string
- `reasoning`: string (LLM explanation, for logging and support visibility)
- `margin_delta_cents`: int64 (positive = over margin, negative = savings)
- `origin_risk_level`: `RiskLevel` (from `from_address` location events)
- `destination_risk_level`: `RiskLevel` (from `to_address` location events)

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

#### `proto/acme/common/v1/values.proto`

`EasyPostAddress` includes a `coordinate` field (`common.Coordinate` lat/lng). Runtime values come
from packaged shipping fixtures, and `get_location_events` uses them when present.

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

- [x] Extend `RecommendShippingOptionRequest` and `RecommendShippingOptionResponse` with fields above
- [x] Add `ShippingRecommendation` message and `RecommendationOutcome` enum
- [x] Add `coordinate` field to `EasyPostAddress` in `common/v1/values.proto` (see Data Model note)
- [x] Extend `ShippingAgentExecutionOptions` with `cache_ttl_secs`
- [x] Run `buf generate`; verify Python and Java classes produced

### Phase 2 — Activity Implementations

- [ ] `lookup_inventory_location` — returns `[{address, items}]` groups; V1 static TOML config returns one group (all items → single warehouse); agent handles any number of groups without changes
- [x] `verify_address` — fixture-backed call to `enablements-api`; populate `coordinate` from fixtures
- [x] `get_carrier_rates` — fixture-backed shipment/rate lookup through `enablements-api`
- [x] `get_location_events` — first pass delegates to `enablements-api` and returns no events
      (see `specs/fulfillment/location-events/` for planned real enrichment)
- [ ] `call_llm` — Anthropic API activity: sends messages + tool definitions to Claude, returns response
- [ ] Register activities on the correct workers per task queue:
  - `lookup_inventory_location` + `call_llm` + `get_location_events` → `agents` worker (no external rate limit)
  - `verify_address` + `get_carrier_rates` → `fulfillment-shipping` worker

### Phase 3 — ShippingAgent Workflow

- [ ] `ShippingAgent` workflow class: `@workflow.defn`, WorkflowID = `customer_id`
- [ ] `recommend_shipping_option` Update handler:
  - [ ] Resolve origin with `lookupInventoryAddress` and verify destination when needed before the
        LLM loop
  - [ ] Compute cache key from resolved origin, destination postal/country, sorted items, and
        selected-shipment context; return cached result if hit and within TTL
  - [ ] Call `build_system_prompt` LocalActivity to compute the system prompt string before
        the agentic loop — result is memoized in history; prompt changes do not require a
        build-id bump (see Design Decisions)
  - [ ] Build tool definitions from the four activity signatures
  - [ ] Agentic loop: call LLM → dispatch concurrent activities for all tool_use blocks → append results → repeat
  - [ ] Extract `ShippingRecommendation` from the `finalize_recommendation` tool input
  - [ ] Store result in `_cache` with `cached_at=workflow.now()`
  - [ ] Return `RecommendShippingOptionResponse`
- [ ] Future `get_options` Query handler: return current cache state
- [ ] Unit tests:
  - [ ] Cache hit — LLM not called after pre-loop context resolves the key
  - [ ] Cache miss — origin lookup still happens before key evaluation
  - [ ] Cache miss + multi-tool response (concurrent activity dispatch after pre-loop context)
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
- [ ] `fulfillment.Order` applies `ShippingRecommendation`: selects rate, sets `margin_leak` SA on `MARGIN_SPIKE`, sets `sla_breach_days` SA (actual_days − promised_days) and `is_fallback=true` on `SLA_BREACH`
- [ ] Deploy `fulfillment-workers` (Python) with new build-id; mark as default

### Phase 6 — Alternate Warehouse Path Hardening

This phase hardens the `find_alternate_warehouse` requirement from a behavioral nudge into a
workflow-layer guarantee. The agent is already working end-to-end; this phase ensures the
alternate warehouse path is reliably exercised and structurally enforced rather than prompt-dependent.

- [ ] **Prompt hardening** (`llm.py` — `build_system_prompt`)
  - Change `"RECOMMENDED ACTIONS:"` heading to `"MANDATORY ACTIONS:"`
  - Replace the soft "call before returning MARGIN_SPIKE or SLA_BREACH" language with explicit
    mandatory framing: you MUST call `find_alternate_warehouse` before calling
    `finalize_recommendation` with either outcome; the system will reject a premature finalize
  - Both the `find_alternate_warehouse` tool description and the system prompt rule should be
    consistent: the tool description already says "Call before returning MARGIN_SPIKE or
    SLA_BREACH" — tighten to "You MUST call this before returning MARGIN_SPIKE or SLA_BREACH"

- [ ] **Post-loop enforcement** (`shipping_agent.py` — `_run_react_loop`)
  - Add `alternate_warehouse_called: bool = False` tracking variable at the top of the loop
  - Set it to `True` when a `find_alternate_warehouse` block appears in any tool dispatch batch
  - When `finalize_recommendation` is detected with `outcome` of `MARGIN_SPIKE` or `SLA_BREACH`
    and `alternate_warehouse_called` is `False`:
    - Do **not** break the loop
    - Append a `tool_result` message for the `finalize_recommendation` block with content:
      `{"error": "REJECTED: You must call find_alternate_warehouse before returning MARGIN_SPIKE or SLA_BREACH. Call it now, then re-submit your recommendation."}`
    - Continue the loop — the LLM will see its finalize was refused and must call the tool
  - When `alternate_warehouse_called` is `True`: accept the finalize as normal

- [ ] **Unit tests** (`tests/test_shipping_agent.py`)
  - `MARGIN_SPIKE` + no alternate call → rejection injected → LLM calls `find_alternate_warehouse` → finalize accepted
  - `SLA_BREACH` + no alternate call → same rejection pattern
  - `MARGIN_SPIKE` + alternate call already in history → finalize accepted without rejection
  - `selected_shipment.paid_price.units=1` integration smoke: use fixture-backed rates to confirm the MARGIN_SPIKE path is triggered deterministically

### Phase 5 — Workshop Scenarios

- [ ] Demo script: happy path — `lookup_inventory_location` → concurrent rates + SCRM → `PROCEED`
- [ ] Demo script: margin spike (`MARGIN_SPIKE` → fallback selected, `margin_leak` visible in Temporal UI)
- [ ] Demo script: concurrent tool dispatch — turn 2 shows `get_carrier_rates` + both
      `get_location_events` as parallel activities in workflow history
- [ ] Demo script: cache hit — second call with same items resolves warehouse, hits cache, returns instantly
- [ ] Slide / README: before (V1 dumb rate fetch) vs after (ShippingAgent) contrast

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
| LLM response structure is unpredictable — `ShippingRecommendation` parsing fails | High | Low | Mitigated by the `finalize_recommendation` tool (forced tool use for structured output): the final answer is always submitted as a tool call input, never as free-form text. Tool inputs are SDK-serialized JSON; prose and markdown contamination are structurally impossible. See Design Decisions. |
| Inventory Locations spec not ready — `lookup_inventory_location` has nothing to query | High | High | V1 workaround: static config with hardcoded warehouse(s); unblock Workshop with seed data |
| Location events tool returns no risk data in the first pass | Low | — | By design until real implementation lands; LLM reasons correctly with `RISK_LEVEL_NONE` |
| Fixture route missing for a scenario address pair | Medium | Medium | Add the route to `shipping-fixtures.json` and keep scenario scripts aligned with fixture IDs |
| Long-running `ShippingAgent` accumulates unbounded cache entries | Low | Medium | TTL eviction on cache reads; `continue_as_new` if cache map exceeds size threshold |
| Cache TTL fallback constant changes while default-TTL workflows are open | High | Low | Treat `_DEFAULT_CACHE_TTL_SECS` as replay-sensitive. Record the desired TTL in `StartShippingAgentRequest`, or use Temporal versioning/patching/controlled migration before changing the fallback for in-flight workflows. |
| LLM skips `find_alternate_warehouse` despite prompt instruction | Medium | Medium | Post-loop enforcement in Phase 6: the workflow rejects a premature MARGIN_SPIKE/SLA_BREACH finalize and forces another loop iteration; the LLM cannot skip the tool without receiving an explicit rejection |
| Post-loop rejection loops indefinitely if LLM ignores the correction | Low | Low | The existing `ApplicationError` on `END_TURN` without finalize already surfaces as a retryable failure; a loop guard (max iterations counter) can be added if observed in practice |

---

## Open Questions

All open questions resolved:

- [x] What is the `within_km` radius default for Workshop demos? **50km**
- [x] What is the default `cache_ttl_secs`? **1800 (30 minutes)**
- [x] Should `SLA_BREACH` signal a support workflow directly from `ShippingAgent`, or return the outcome and let `fulfillment.Order` decide? **`fulfillment.Order` handles it** — ShippingAgent returns `SLA_BREACH` with the fastest available `recommended_option_id`; `fulfillment.Order` ships best-effort, records the breach via `sla_breach_days` SA, and marks the selection `is_fallback=true`. Human-in-the-loop escalation is deferred (see Deferred Work).

---

## Deferred Work

Items that were considered during design or implementation and deliberately excluded from V1.
Each is a candidate for a follow-up spec or Workshop extension exercise.

### Warehouse address caching in workflow state

**What:** Cache the inventory origin lookup response in workflow state after the first
`lookupInventoryAddress` call. On subsequent `recommend_shipping_option` updates, skip
the pre-loop origin lookup entirely and inject the resolved warehouse address directly into the
task context.

**Why deferred:** Warehouse-to-SKU assignment is stable in V1 (static TOML seed data), so
every call pays the lookup cost unnecessarily. The optimization is safe to defer because the
activity is cheap and in-process for the Workshop. Promotes naturally once a real Inventory
Locations service is behind it.

**Consideration for production:** If SKU-to-warehouse assignment changes (new warehouse, SKU
migration), the cached address becomes stale for the lifetime of the workflow. A cache
invalidation Signal or a TTL would be needed before enabling this in production.

---

### Cache TTL configuration hardening

**What:** Make the cache TTL an explicitly recorded workflow configuration for every
`ShippingAgent` execution. The Nexus handler currently starts the workflow with only
`customer_id`, so workflows created through the normal service path use the code fallback
`_DEFAULT_CACHE_TTL_SECS = 1800`.

**Why deferred:** The current 30-minute default is acceptable for the workshop path and the
behavior is covered by unit tests. The improvement is about operational safety when changing the
default later, not about current correctness.

**Consideration for production:** Changing the fallback constant while existing workflows are open
can create a Temporal replay mismatch if a cached entry is valid under the old value but expired
under the new one. Future work should either:

- pass `ShippingAgentExecutionOptions(cache_ttl_secs=1800)` from `ShippingAgentImpl` so the value is
  recorded in workflow history for new executions;
- gate any default change with Temporal patch/versioning semantics; or
- migrate/continue-as-new existing workflows with an explicit TTL before changing the fallback.

---

### Live Carrier Gateway

**What:** A future adapter behind `enablements-api` could call a real carrier provider and enforce
vendor-specific throttling or purchasing rules.

**Why deferred:** Workshop runtime uses deterministic fixtures. EasyPost is allowed only in the
offline capture script, so a live gateway is unnecessary for the current architecture.

---

### Human-in-the-Loop SLA Breach Escalation

**What:** When `SLA_BREACH` is confirmed (after `find_alternate_warehouse` is exhausted),
pause the `fulfillment.Order` workflow and wait for a Temporal Signal from a support agent
before printing the label. The support agent can approve the fastest available rate (current
behaviour), override the rate selection, or cancel the order. The `sla_breach_days` SA makes
breached workflows easily discoverable from the Temporal UI or via search.

**Why deferred:** The current best-effort approach (ship fastest, record the breach) is the
right default for automation at scale — a human decision gate adds latency and requires a
support queue integration that is out of scope for the Workshop. The `sla_breach_days` SA
provides the observability needed to identify and process breaches asynchronously.

**Consideration for production:** A dedicated `SupportEscalation` workflow (or Signal handler
on `fulfillment.Order`) could consume the breach event, page on-call, and inject the support
decision back as a Signal. The `Workflow.await()` hold with a configurable timeout (auto-approve
fastest rate if no Signal arrives within N minutes) keeps the order moving even if support is
slow to respond.

---

## References

- [`shipping_agent.proto`](../../../proto/acme/fulfillment/domain/v1/shipping_agent.proto)
- [`fulfillment/domain/v1/values.proto`](../../../proto/acme/fulfillment/domain/v1/values.proto) — `LocationEvent`, `LocationRiskSummary`, `RiskLevel`
- [`fulfillment.Order` spec](../fulfillment-order-workflow/spec.md) — Phase 7: V2 wiring
- [Temporal AI Cookbook — Agentic Loop with Claude (Python)](https://docs.temporal.io/ai-cookbook/agentic-loop-tool-call-claude-python)
- [Location Events spec](../../fulfillment/location-events/spec.md)
