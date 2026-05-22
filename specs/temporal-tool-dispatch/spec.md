# Temporal Tool Dispatch — Reusable Agentic Tool Registration

**Feature Name:** `temporal-tool-dispatch` — Reusable Agentic Tool Dispatch Module
**Status:** Draft
**Owner:** Temporal FDE Team
**Created:** 2026-04-19
**Updated:** 2026-04-19

---

## Overview

### Executive Summary

The `ShippingAgent` workflow contains a working but non-reusable pattern for LLM tool dispatch:
two parallel dicts (`_TOOL_SPECS`, `_TOOL_DESCRIPTIONS`), a helper to extract Temporal-registered
activity names, and a pair of functions (`_build_tool_definitions`, `_dispatch_tool`). This is
good enough for one workflow but cannot be imported by any other.

This module extracts that pattern into a small, importable Python module — `tool_dispatch` —
that any Temporal agentic workflow can use for static tool registration and dispatch. The module
introduces `ToolSpec`, a single struct that carries the tool name, LLM description, request
schema, and a `dispatch` coroutine that encapsulates the underlying Temporal execution primitive.
The agentic loop never calls `execute_activity` (or any other Temporal primitive) directly; it
calls `spec.dispatch(req)`. This makes Activities, Local Activities, Nexus Operations, and Child
Workflows look identical to the loop.

A set of builder functions — `activity_tool`, `local_activity_tool`, `nexus_tool`,
`child_workflow_tool` — create `ToolSpec` instances in a single line each. These specs are
collected into a `ToolSpecs` container, which owns the name-keyed dispatch table and exposes
two methods: `definitions()` and `dispatch(block)`. The agentic loop holds one object and calls
two methods — it never manages a dict, never passes specs as arguments to standalone functions,
and never knows what Temporal primitive any tool uses.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: A `ToolSpec` dataclass carries all dispatch information so tools are registered in one place, not two parallel dicts
- Goal 2: `dispatch` encapsulates the Temporal primitive — the agentic loop is primitive-agnostic
- Goal 3: `ToolSpecs` container owns the name-keyed dispatch table — the agentic loop holds one object, not a raw dict, and never passes specs as arguments to standalone functions
- Goal 4: Builder functions make registering a new tool a one-liner for each Temporal primitive type
- Goal 5: `ShippingAgent` is migrated to the module as the primary worked example; its agentic loop becomes simpler, not more complex

### Acceptance Criteria

- [ ] `ToolSpec` is importable from the shared module and carries `name`, `description`, `req_type`, and `dispatch`
- [ ] `activity_tool(...)` returns a `ToolSpec` whose `dispatch` calls `workflow.execute_activity` with the options provided at builder time
- [ ] `local_activity_tool(...)` returns a `ToolSpec` whose `dispatch` calls `workflow.execute_local_activity`
- [ ] `nexus_tool(...)` returns a `ToolSpec` whose `dispatch` calls the Nexus operation
- [ ] `child_workflow_tool(...)` returns a `ToolSpec` whose `dispatch` calls `workflow.execute_child_workflow`
- [ ] `ToolSpecs(*specs)` accepts a variadic sequence of `ToolSpec` instances and builds an internal name-keyed dict
- [ ] `ToolSpecs.definitions()` returns a `list[LlmToolDefinition]` built from the registered specs
- [ ] `ToolSpecs.dispatch(block)` looks up by name, deserializes input, calls `spec.dispatch`, returns JSON string
- [ ] `ToolSpecs.dispatch` raises `ApplicationError(non_retryable=True)` for an unrecognized tool name
- [ ] `activity_name(method)` utility is exported from the module
- [ ] `ShippingAgent` migrated to use `tool_dispatch` with no change to observable behavior
- [ ] No dynamic tool discovery, runtime tool registration, or MCP integration in the module

---

## Current State (As-Is)

### What exists today?

`python/fulfillment/src/agents/workflows/shipping_agent.py` contains:

- `_activity_name(method)` — reads `__temporal_activity_definition` from an `@activity.defn`
  class method to extract the Temporal-registered name
- `_TOOL_SPECS: dict[str, tuple]` — maps tool name → `(unbound method, req_type, result_type, task_queue)`;
  hardcoded to `workflow.execute_activity`, hardcoded to ShippingAgent's four tools
- `_TOOL_DESCRIPTIONS: dict[str, str]` — parallel dict mapping the same names to LLM-facing description strings
- `_build_tool_definitions()` — zips the two dicts into a `list[LlmToolDefinition]`; no parameters,
  only usable for ShippingAgent's tools
- `_dispatch_tool(block)` — looks up name in `_TOOL_SPECS`, deserializes input with
  `req_type(**block.tool_use.input)`, calls `workflow.execute_activity` with hardcoded timeout
  and retry policy, returns `result.model_dump_json()`

### Pain points / gaps

- Gap 1: `_TOOL_SPECS` is an untyped `tuple` — adding a new tool requires knowing the exact positional index for `method`, `req_type`, `result_type`, `task_queue`
- Gap 2: Two parallel dicts must be kept in sync manually; a name missing from `_TOOL_DESCRIPTIONS` silently produces a `KeyError` at definition build time
- Gap 3: `_build_tool_definitions()` and `_dispatch_tool()` are module-level private functions — any new workflow must copy them verbatim
- Gap 4: `_dispatch_tool` calls `workflow.execute_activity` unconditionally — Local Activity, Nexus, and Child Workflow tools cannot be represented in this pattern
- Gap 5: `_activity_name()` is a private utility — any workflow needing it must copy it

---

## Desired State (To-Be)

### Architecture Overview

```
tool_dispatch.py (shared module)
│
├── ToolSpec                       — dataclass: name, description, req_type, dispatch
│
├── ToolSpecs(*specs)              — container: owns the name-keyed dispatch table
│   ├── .definitions()             — → list[LlmToolDefinition]
│   └── .dispatch(block)           — → Awaitable[str]  (look up, deserialize, dispatch, serialize)
│
├── activity_name(method)          — utility: registered name from @activity.defn
│
├── activity_tool(...)             — builder → ToolSpec (dispatch = execute_activity)
├── local_activity_tool(...)       — builder → ToolSpec (dispatch = execute_local_activity)
├── nexus_tool(...)                — builder → ToolSpec (dispatch = execute_nexus_operation)
└── child_workflow_tool(...)       — builder → ToolSpec (dispatch = execute_child_workflow)


ShippingAgent (consumer — worked example)
│
├── _TOOLS = ToolSpecs(
│     activity_tool(
│         name=activity_name(LookupInventoryActivities.lookup_inventory_location),
│         description=..., method=..., req_type=..., result_type=...,
│         task_queue="fulfillment", ...),
│     activity_tool(..., task_queue="fulfillment-shipping", ...),   # verify_address
│     activity_tool(..., task_queue="fulfillment-shipping", ...),   # get_carrier_rates
│     activity_tool(..., task_queue="agents", ...),                  # get_location_events
│   )
│
├── tools = _TOOLS.definitions()                             # called once before the loop
└── results = await asyncio.gather(                         # inside the loop
        *[_TOOLS.dispatch(b) for b in tool_blocks]
    )
```

### Key Capabilities

- Capability 1: A single `ToolSpec` is the source of truth for a tool — name, description, schema, and dispatch options are co-located and typed
- Capability 2: `ToolSpecs` owns the dispatch table — the agentic loop holds one object and calls `.definitions()` / `.dispatch(block)`; it never manages a dict or passes specs as arguments
- Capability 3: The agentic loop is primitive-agnostic — `_TOOLS.dispatch(block)` works identically whether the underlying primitive is an Activity, Local Activity, Nexus Operation, or Child Workflow
- Capability 4: Builder functions capture Temporal execution options (task queue, timeouts, retry policy) at registration time — the loop passes no options at dispatch time
- Capability 5: Any workflow imports `ToolSpec`, `ToolSpecs`, the builders, and `activity_name` — nothing to copy-paste
- Capability 6: Workflows that need to inspect a specific tool's result (e.g. ShippingAgent extracting `easypost_address.id` after `lookup_inventory_location`) key off `block.tool_use.name`, which equals `activity_name(...)` — the same string used at registration

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|---|---|---|
| `ToolSpecs` container owns the name-keyed dict and exposes `.definitions()` / `.dispatch(block)` | The loop holds one object and calls two methods. Dict construction, key derivation, and error handling are encapsulated — the caller has nothing to manage. | Standalone `build_tool_definitions(specs)` and `dispatch_tool(specs, block)` functions with a caller-managed `dict[str, ToolSpec]` — the caller is responsible for building and passing the dict on every call, which is boilerplate that belongs inside the abstraction |
| `dispatch` is an `async` callable `(req: BaseModel) -> BaseModel` on `ToolSpec`, not a method | The loop calls `spec.dispatch(req)` through `ToolSpecs.dispatch` — it does not know or care which Temporal primitive is involved. Builder functions construct this coroutine at registration time. | Passing the primitive type and options to `ToolSpecs.dispatch` at call time — couples the loop to primitive selection, exactly what we're trying to eliminate |
| Builder functions, not a class hierarchy | Agentic workflows register 3–6 tools; a class hierarchy adds indirection with no benefit at this scale | `ActivityToolSpec(ToolSpec)` subclass — adds `isinstance` checks and import noise for no gain |
| `ToolSpecs.dispatch` returns `str` (serialized JSON) | The agentic loop appends tool results to LLM messages as JSON strings; deserializing after dispatch would be wasteful. `str` keeps the method signature stable regardless of result type. | Return `BaseModel` — the caller always serializes to JSON, so this pushes boilerplate into every loop |
| `activity_name(method)` exported from the module | General-purpose utility for extracting Temporal-registered names; prevents silent breakage from `name=` kwarg changes on `@activity.defn` | Private `_activity_name` per workflow — already the problem this module solves |
| Static registration only — `ToolSpecs` is constructed at module level, not at runtime | Static registration produces a deterministic, replay-safe dispatch table. The full list is known at workflow definition time. Temporal workflow code must be deterministic. | Dynamic tool discovery (e.g. listing activity registrations from the worker at runtime) — violates Temporal determinism; also conflates "what is registered" with "what the LLM should see" |
| Builder execution options forwarded via `**kwargs`, not a custom options dataclass | The Temporal SDK already defines the valid options for each primitive (`execute_activity`, `execute_local_activity`, etc.). Replicating those fields into our own dataclasses would create a parallel type that diverges from the SDK over time. Instead each builder accepts `**execute_kwargs` and passes them through verbatim — the SDK function's own signature is the source of truth for valid options. | Custom `ActivityOptions` dataclass per primitive — duplicates SDK fields, must be maintained as the SDK evolves, adds a type the caller must learn |
| Execution options captured at builder call time | Builders close over `**execute_kwargs` at construction. `ToolSpecs.dispatch` passes no options. | Passing options to `ToolSpecs.dispatch` at call time — couples the loop to per-tool configuration |

### Component Design

#### `ToolSpec` dataclass

- **Purpose:** Single struct representing one LLM-callable tool
- **Fields:**
  - `name: str` — the name the LLM uses in `tool_use` blocks
  - `description: str` — LLM-facing description passed to `LlmToolDefinition`
  - `req_type: type[BaseModel]` — Pydantic model; `model_json_schema()` is called by `ToolSpecs.definitions()`
  - `dispatch: Callable[[BaseModel], Awaitable[BaseModel]]` — async callable; receives the deserialized request, returns the result model
- **Responsibilities:** Data only. `ToolSpecs` manages keying and routing; `ToolSpec` carries the spec for one tool.

#### `activity_name(method) -> str`

- **Purpose:** Extract the Temporal-registered name from an `@activity.defn` class method
- **Mechanism:** Reads `__temporal_activity_definition.name` set by the decorator; falls back to `method.__name__`
- **When to use:** Whenever a workflow registers an activity as a tool — using the registered name ensures that renaming the method or changing the `name=` kwarg to `@activity.defn` propagates automatically to the tool dict key

#### `activity_tool(name, description, method, req_type, result_type, **execute_kwargs) -> ToolSpec`

- **`execute_kwargs`:** All keyword arguments accepted by `workflow.execute_activity` except `args` and `result_type` (those are provided by the builder). Typically includes `task_queue`, `start_to_close_timeout`, `schedule_to_close_timeout`, `retry_policy`, `heartbeat_timeout`, `cancellation_type`. The SDK function is the authoritative list — the builder forwards them verbatim.
- **Dispatch behavior:** `workflow.execute_activity(method, args=[req], result_type=result_type, **execute_kwargs)`
- **When to use:** The tool calls an external API, reads a database, or performs I/O that may fail and should be retried. Produces a separate event in workflow history. Task-queue rate limiting is available.

#### `local_activity_tool(name, description, method, req_type, result_type, **execute_kwargs) -> ToolSpec`

- **`execute_kwargs`:** All keyword arguments accepted by `workflow.execute_local_activity` except `args` and `result_type`. Typically includes `start_to_close_timeout`, `schedule_to_close_timeout`, `retry_policy`, `local_retry_threshold`, `cancellation_type`.
- **Dispatch behavior:** `workflow.execute_local_activity(method, args=[req], result_type=result_type, **execute_kwargs)`
- **When to use:** The tool is fast and cheap (seconds, not minutes), runs in-process, and does not need a separate history event. Examples: lightweight in-memory lookups, short JSON transforms, deterministic calculations. **Not appropriate** for external API calls — use `activity_tool` for those.

#### `nexus_tool(name, description, endpoint, operation, req_type, result_type, **execute_kwargs) -> ToolSpec`

- **`execute_kwargs`:** All keyword arguments accepted by the Temporal Python SDK's Nexus operation call, minus the operation input. Exact set to be confirmed against the SDK during implementation (see Open Questions).
- **Dispatch behavior:** Execute the Nexus operation via the Temporal Python SDK's Nexus client, forwarding `**execute_kwargs`. Stub with `raise NotImplementedError` until the Python SDK Nexus dispatch API is confirmed.
- **When to use:** The capability is owned by another team or service in a different Temporal namespace. The caller sees only the endpoint name and operation contract.

#### `child_workflow_tool(name, description, workflow_type, req_type, result_type, id_fn=None, **execute_kwargs) -> ToolSpec`

- **`id_fn`:** Optional callable `(req: BaseModel) -> str`; constructs a deterministic workflow ID from the request. This is the one builder-level convenience that has no direct SDK equivalent — all other options go in `**execute_kwargs`.
- **`execute_kwargs`:** All keyword arguments accepted by `workflow.execute_child_workflow` except `args` and `result_type`. Typically includes `task_queue`, `execution_timeout`, `run_timeout`, `task_timeout`, `id_reuse_policy`, `retry_policy`, `cancellation_type`, `versioning_intent`.
- **Dispatch behavior:** `workflow.execute_child_workflow(workflow_type, args=[req], result_type=result_type, id=id_fn(req) if id_fn else None, **execute_kwargs)`
- **When to use:** The work triggered by the tool is itself long-running (minutes to hours), benefits from its own checkpoint history, or may need to be queried or cancelled independently.

#### `ToolSpecs` container

- **Purpose:** Owns the name-keyed dispatch table and exposes the two methods the agentic loop needs
- **Construction:** `ToolSpecs(*specs: ToolSpec)` — variadic; builds `_by_name: dict[str, ToolSpec]` internally
- **`.definitions() -> list[LlmToolDefinition]`**
  - Builds `LlmToolDefinition(name=spec.name, description=spec.description, input_schema=spec.req_type.model_json_schema())` for each registered spec
  - Called once before the agentic loop begins — tool definitions do not change during a run
- **`.dispatch(block: LlmContentBlock) -> Awaitable[str]`**
  1. Look up `block.tool_use.name` in `_by_name`; raise `ApplicationError(non_retryable=True)` if not found
  2. Deserialize: `req = spec.req_type(**block.tool_use.input)`
  3. Call: `result = await spec.dispatch(req)`
  4. Return: `result.model_dump_json()`
- **Concurrency:** The agentic loop dispatches a full LLM tool batch concurrently:
  `asyncio.gather(*[_TOOLS.dispatch(b) for b in tool_blocks])` — identical to today's pattern in `ShippingAgent`, without the dict argument

### Primitive Selection Guide

| Primitive | History event | Rate limiting | When to choose |
|---|---|---|---|
| Activity | Yes (separate) | Task-queue level | External API, I/O, anything retryable with backoff |
| Local Activity | No | Worker-level | Fast in-process work (< ~10 s), no external call |
| Nexus Operation | Yes (caller side) | Caller namespace | Capability owned by another team/namespace |
| Child Workflow | Yes (own history) | Task-queue level | Tool call is itself a long-running durable unit |

### Data Model / Schemas

No new proto definitions. `ToolSpec` is a Python `@dataclass` — a workflow-local struct, never serialized to Temporal history or transmitted over the wire.

`LlmToolDefinition` (existing proto in `acme.common.v1.llm`) is the output of `build_tool_definitions`; no changes to the proto are needed.

### Module Location

`python/fulfillment/src/agents/tool_dispatch.py` for the initial implementation (ShippingAgent is
the only consumer). If a second agentic workflow in a different Python package needs the module,
move it to a shared package (e.g. `python/common/src/temporal/tool_dispatch.py`) at that point.
Do not pre-optimize for a second consumer that does not yet exist.

---

## Implementation Strategy

### Phases

**Phase 1: Module**
- Write `tool_dispatch.py`: `ToolSpec`, `ToolSpecs`, `activity_name`, all four builder functions
- Unit tests for each builder (verify `dispatch` calls the right SDK primitive with the right arguments, using `mocker.patch`)
- Unit tests for `ToolSpecs.definitions()` (schema correctness) and `ToolSpecs.dispatch()` (name lookup, deserialization, serialization, unknown-name error path)

**Phase 2: ShippingAgent Migration**
- Replace `_activity_name`, `_TOOL_SPECS`, `_TOOL_DESCRIPTIONS`, `_build_tool_definitions`, `_dispatch_tool` in `shipping_agent.py` with imports from `tool_dispatch` and a single `_TOOLS = ToolSpecs(activity_tool(...), ...)` declaration
- Update call sites: `_build_tool_definitions()` → `_TOOLS.definitions()`; `dispatch_tool(_TOOLS_DICT, b)` → `_TOOLS.dispatch(b)`
- All existing ShippingAgent unit tests pass without modification — observable behavior is unchanged

### Critical Files / Modules

To Create:
- `python/fulfillment/src/agents/tool_dispatch.py` — the module
- `python/fulfillment/tests/agents/test_tool_dispatch.py` — unit tests

To Modify:
- `python/fulfillment/src/agents/workflows/shipping_agent.py` — remove five private symbols; add import from `tool_dispatch`; replace with `_TOOLS` dict

---

## Testing Strategy

### Unit Tests

- `activity_name` with an `@activity.defn` method returns the Temporal-registered name, not `__name__`
- `activity_name` with a plain function falls back to `__name__`
- `activity_tool` dispatch calls `workflow.execute_activity` with the exact `method`, `result_type`, and all `**execute_kwargs` provided at builder time — no kwargs are dropped or added
- `local_activity_tool` dispatch calls `workflow.execute_local_activity` (mock)
- `nexus_tool` dispatch calls the Nexus SDK (mock)
- `child_workflow_tool` dispatch calls `workflow.execute_child_workflow` with correct `id` when `id_fn` is provided, and `None` id when omitted
- `ToolSpecs.definitions()` produces the correct `name`, `description`, and `input_schema` for each registered spec
- `ToolSpecs.dispatch()` with a known name: deserializes input into `req_type`, calls `spec.dispatch`, returns `model_dump_json()` output
- `ToolSpecs.dispatch()` with an unknown name: raises `ApplicationError` with `non_retryable=True`
- `ToolSpecs.dispatch()` does not catch `ValidationError` from Pydantic — it propagates
- `ToolSpecs` construction with duplicate names raises an error (invariant: each name is unique)

### Integration Tests

- ShippingAgent end-to-end via Temporal Python test framework: `_TOOLS.definitions()` produces the correct `LlmToolDefinition` names; `_TOOLS.dispatch(block)` routes each `tool_use` block to the correct mock activity — all existing ShippingAgent test scenarios pass unchanged

### Validation Checklist

- [ ] All unit tests pass
- [ ] ShippingAgent existing tests pass after Phase 2 migration with no test changes
- [ ] No dynamic imports, no runtime activity discovery, no MCP references in the module
- [ ] `dispatch` coroutines in all builders are `async def`, not `lambda`

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Temporal Python SDK Nexus dispatch API is not yet stable or differs from activity API | Medium | Medium | Spike against the SDK before finalizing the `nexus_tool` signature; stub as `raise NotImplementedError` if not yet supported |
| `dispatch` closes over mutable builder arguments — options change after construction | Low | Low | All builder parameters are immutable (`str`, `type`, `timedelta`, `RetryPolicy`); captured values cannot change after construction |
| `dispatch_tool` silently drops `ValidationError` if `req_type(**block.tool_use.input)` raises | Medium | Low | Do not catch `ValidationError` — let it propagate as an activity failure so the LLM can retry with corrected input |

---

## Dependencies

### External Dependencies

- `temporalio` Python SDK — `workflow.execute_activity`, `workflow.execute_local_activity`, `workflow.execute_child_workflow`, Nexus client API
- `pydantic` — `BaseModel`, `model_json_schema()`, `model_dump_json()`

### Cross-Cutting Concerns

- `LlmContentBlock`, `LlmToolDefinition` (proto-generated from `acme.common.v1.llm`) — `ToolSpecs.dispatch` takes an `LlmContentBlock`; all agentic workflows must use this shared block shape
- ShippingAgent spec (`specs/fulfillment-order/shipping-agent/spec.md`) — primary consumer and migration target; this module is a prerequisite to keeping ShippingAgent's implementation clean as new tools are added

### Rollout Blockers

None — the module has no infrastructure dependencies and can be written and tested before ShippingAgent is deployed.

---

## Open Questions & Notes

### Questions for Tech Lead

- [ ] Should the module live in `python/fulfillment/` now and move to `python/common/` when there is a second consumer, or should we create `python/common/` up front?
- [ ] Should `dispatch_tool` catch and re-wrap `pydantic.ValidationError` from input deserialization (e.g. as a non-retryable `ApplicationError`), or let it propagate raw so the Temporal retry policy handles it?
- [ ] Is the Temporal Python SDK Nexus dispatch API stable enough to implement `nexus_tool` now, or should Phase 1 stub it with `raise NotImplementedError`?

### Implementation Notes

- Builder functions must return an `async def` inner function for `dispatch`, not a `lambda`. `workflow.execute_activity` and `workflow.execute_child_workflow` are coroutines; a `lambda` cannot `await` them.
- `ToolSpecs.dispatch` must be declared `async` and awaited inside `asyncio.gather` in the agentic loop.
- The module must not import activity implementation classes at the module level. Activity imports belong in the workflow file that calls the builders. The module only imports from `temporalio` and `pydantic`.
- Builder `**execute_kwargs` are captured at construction time and forwarded verbatim to the SDK call inside `dispatch`. The builder does not inspect or validate them — invalid kwargs surface as `TypeError` at dispatch time, which is acceptable: a misconfigured `ToolSpec` is a programming error caught in testing, not a runtime tool failure.
- `ToolSpec.dispatch` (the per-spec coroutine field) and `ToolSpecs.dispatch` (the container's routing method) are distinct: the former is the primitive-specific callable set by a builder; the latter is the public method that does name lookup, deserialization, and serialization around it.
- Workflows that need to inspect a specific tool's result after dispatch (e.g. ShippingAgent extracting `easypost_address.id` from `lookup_inventory_location`) do so by checking `block.tool_use.name == activity_name(LookupInventoryActivities.lookup_inventory_location)`. This is workflow-specific post-processing, not part of the module.

---

## References & Links

- [`shipping_agent.py`](../../python/fulfillment/src/agents/workflows/shipping_agent.py) — current implementation; source of the pattern being extracted
- [ShippingAgent spec](../fulfillment-order/shipping-agent/spec.md) — primary consumer
- [Temporal Python SDK — execute_activity](https://python.temporal.io/temporalio.workflow.html#execute_activity)
- [Temporal Python SDK — execute_local_activity](https://python.temporal.io/temporalio.workflow.html#execute_local_activity)
- [Temporal Python SDK — execute_child_workflow](https://python.temporal.io/temporalio.workflow.html#execute_child_workflow)
