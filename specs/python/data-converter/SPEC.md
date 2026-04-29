# Feature Specification: Custom Protobuf-Pydantic Data Converter

## Overview

**Feature Name:** Protobuf Pydantic Data Converter (binary/protobuf + json/protobuf)
**Status:** Approved
**Owner:** Mike Nichols
**Created:** 2026-04-25
**Updated:** 2026-04-25

### Executive Summary

The Python fulfillment worker currently uses `pydantic_data_converter` (from `temporalio.contrib.pydantic`), which serialises all Pydantic models with encoding `json/plain`. Java's `DefaultDataConverter` sends and expects encoding `json/protobuf` for proto-generated types. At the Nexus wire boundary — where Java's `fulfillment.Order` workflow calls the Python `ShippingAgent` service — the two sides cannot decode each other's payloads, producing a `BAD_REQUEST: Payload converter failed to decode Nexus operation input` error at runtime.

The fix is a custom `DataConverter` with two Pydantic-aware payload converters — one for each protobuf encoding slot — so that Python can both emit `json/protobuf` (compatible with Java's `DefaultDataConverter`) and decode incoming payloads that arrive as either `binary/protobuf` or `json/protobuf`. Both converters are thin subclasses of the existing SDK converters (`JSONProtoPayloadConverter` and `BinaryProtoPayloadConverter`); they delegate all serialization to the parent and only add a Pydantic ↔ pb2 bridge layer. A prebuild script generates an explicit `_registry.py` mapping every `_p2p` Pydantic class to its `_pb2` counterpart, replacing runtime string manipulation. The `json/plain` fallback slot reuses `PydanticJSONPlainPayloadConverter` from `temporalio.contrib.pydantic`. Application code — handlers, workflows, activities — sees only Pydantic types and is not touched.

---

## Goals & Success Criteria

### Primary Goals

- Goal 1: Eliminate the `BAD_REQUEST` decode failure at the Java→Python Nexus boundary.
- Goal 2: Preserve the application-code invariant that all domain types are Pydantic `_p2p` models — never raw `pb2`.
- Goal 3: Ensure Java, Python, and any future polyglot workers can interoperate across both proto wire formats (`json/protobuf` and `binary/protobuf`), with Python defaulting to `json/protobuf` on outbound encoding.

### Acceptance Criteria

- [ ] `ShippingAgentImpl.calculate_shipping_options` receives a properly decoded `CalculateShippingOptionsRequest` (Pydantic) when called from Java.
- [ ] The response encoded by the Python worker is decoded successfully by Java's `DefaultDataConverter`.
- [ ] All existing Python-only workflow and activity roundtrips continue to work.
- [ ] No serialisation or mapping logic appears in `ShippingAgentImpl`, workflow code, or activity code.
- [ ] Round-trip unit test: Pydantic → `json/protobuf` payload → Pydantic produces an identical value.
- [ ] Round-trip unit test: Pydantic → `binary/protobuf` payload → Pydantic produces an identical value.
- [ ] Outbound payload metadata confirms `encoding: json/protobuf` (Python's default emit encoding) and a non-empty `messageType`.
- [ ] Inbound `binary/protobuf` payload is correctly decoded to a Pydantic type.

---

## Current State (As-Is)

### What exists today?

All Python workers create a `Client` with `data_converter=pydantic_data_converter`. This converter handles:

- `None` → `binary/null`
- Raw `google.protobuf.Message` subclasses → `binary/proto`
- Everything else, including Pydantic `BaseModel` subclasses → `json/plain`

Java's `DefaultDataConverter` uses:

- `None` → `binary/null`
- Proto messages → `json/protobuf` (with a `messageType` metadata header containing the fully-qualified proto type name)
- Primitives → `json/plain`

### Pain points / gaps

- Gap 1: `pydantic_data_converter` encodes Pydantic models as `json/plain`; Java cannot decode `json/plain` back to a proto type.
- Gap 2: Java sends `json/protobuf` payloads to the Nexus handler; `pydantic_data_converter` has no `json/protobuf` decoder for Pydantic type hints, so it cannot reconstruct the Pydantic model.
- Gap 3: Fixing this in application code (manual `MessageToDict`/`ParseDict` in the handler) violates the architectural rule that application code works exclusively with `_p2p` Pydantic types.

---

## Desired State (To-Be)

### Architecture Overview

```
Java fulfillment.Order workflow
  │  encodes CalculateShippingOptionsRequest as json/protobuf  ← or binary/protobuf
  │
  ▼ Nexus call (cross-namespace)
Python fulfillment worker
  │  custom converter (json OR binary slot) → CalculateShippingOptionsRequest (_p2p)
  │
  ▼ ShippingAgentImpl.calculate_shipping_options(ctx, input: CalculateShippingOptionsRequest)
  │  (pure Pydantic — no pb2 visible here)
  │
  ▼ returns CalculateShippingOptionsResponse (_p2p)
  │  custom converter encodes _p2p → json/protobuf  (Python always emits json)
  │
  ▼ Java decodes json/protobuf → CalculateShippingOptionsResponse proto
```

The converter is a drop-in replacement: `data_converter=proto_pydantic_data_converter` in `fulfillment_worker.py`. All other code is unchanged.

### Key Capabilities

- Capability 1: Encode any Pydantic `_p2p` model as `json/protobuf` by routing through its `_pb2` counterpart (Python's default outbound encoding).
- Capability 2: Decode `json/protobuf` payloads into the correct Pydantic type when a `BaseModel` type hint is present.
- Capability 3: Decode `binary/protobuf` payloads into the correct Pydantic type when a `BaseModel` type hint is present.
- Capability 4: Fall through transparently to existing null and JSON-plain converters for all other types.

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Converter layer, not application code | Serialisation is infrastructure; application code should be oblivious to wire format | Manual `MessageToDict`/`ParseDict` in `ShippingAgentImpl` — pollutes every handler and violates the _p2p-only rule |
| Subclass `JSONProtoPayloadConverter` / `BinaryProtoPayloadConverter` | The SDK converters already do the serialization correctly (`MessageToDict` → compact JSON, `Parse`, `SerializeToString`, `ParseFromString`, symbol database lookup). Subclassing reuses all of that — we only override `to_payload` to handle `BaseModel` input and `from_payload` to convert the returned pb2 to Pydantic when the type hint says so | Implement from scratch — duplicates MessageToJson/Parse/SerializeToString logic already in the SDK and drifts from SDK behaviour |
| Generated registry via prebuild script | Explicit, type-safe dict of `{p2p_cls: pb2_cls}` generated from the actual generated files; catches mapping gaps at codegen time; no runtime string manipulation | Runtime naming convention (`_p2p` → `_pb2` module suffix swap) — zero-config but errors surface at encode time during a live workflow, not at build time |
| Two separate converters, one per encoding slot | `EncodingPayloadConverter.encoding` is a single string; `CompositePayloadConverter` routes `from_payload` by matching that string exactly — one converter per encoding is the only well-formed design | Single converter that switches internally on the encoding header — violates the `EncodingPayloadConverter` contract |
| `json/protobuf` converter placed before `binary/protobuf` in the composite | `CompositePayloadConverter.to_payloads` iterates in insertion order and returns the first non-None result; placing JSON first makes Python's outbound encoding `json/protobuf`, matching Java's `DefaultDataConverter` default; `from_payload` routes by encoding header so order is irrelevant for decoding | Binary first — Python would emit `binary/protobuf`, more compact but diverges from Java's default |
| Reuse `PydanticJSONPlainPayloadConverter` for `json/plain` fallback | It already exists in `temporalio.contrib.pydantic`, uses `pydantic_core.to_json` and `TypeAdapter.validate_json`, and handles all non-proto Pydantic models correctly (hand-written types, LLM result types, etc.) | Bare `JSONPlainPayloadConverter` — doesn't round-trip Pydantic models through the `json/plain` path; `pydantic_data_converter` re-exports it for exactly this use case |
| Import all `_pb2` modules at worker startup | The protobuf symbol database is populated on import; the parent `from_payload` uses `_sym_db.GetSymbol(message_type)()` which fails silently at runtime if the module was never imported | Lazy import on first use — non-deterministic failure on cold paths; harder to test |

### Component Design

#### Package Structure

```
python/fulfillment/src/converter/
  __init__.py        # exports proto_pydantic_data_converter, ProtoPydanticPayloadConverter
  _converters.py     # PydanticJsonProtoPayloadConverter, PydanticBinaryProtoPayloadConverter
  _registry.py       # AUTO-GENERATED by scripts/gen_converter_registry.py — do not edit
```

#### `_registry.py` (generated)

- **Purpose:** Explicit, build-time-verified mapping from every `_p2p` Pydantic class to its `_pb2` counterpart.
- **Responsibilities:** Import all `_p2p` and `_pb2` classes and expose `REGISTRY: dict[type[BaseModel], type[Message]]`. Acts as the authoritative `_p2p → _pb2` lookup, replacing runtime string manipulation.
- **Generated by:** `scripts/gen_converter_registry.py` — scans `python/generated/pydantic/**/*_p2p.py`, resolves the corresponding `_pb2` module (same path, `_p2p` → `_pb2`), validates every class exists in both modules, and writes the registry file. Should be invoked as part of `buf generate` or the Makefile proto target.
- **Importing `_registry.py` also populates the protobuf symbol database** (side effect of the `_pb2` imports it contains), which makes `pb2_registry.py` redundant — the registry import replaces it.

#### `PydanticJsonProtoPayloadConverter`

- **Purpose:** Extend `JSONProtoPayloadConverter` with Pydantic awareness for the `json/protobuf` slot.
- **Responsibilities:**
  - `to_payload(value)`: If `value` is a `BaseModel`, look up `pb2_cls = REGISTRY[type(value)]`, call `ParseDict(value.model_dump(mode="json"), pb2_cls())` to get a `pb2` instance, then delegate to `super().to_payload(pb2_instance)`. Return `None` if the type is not in the registry. Delegate all other values to `super()`.
  - `from_payload(payload, type_hint)`: Call `pb2_result = super().from_payload(payload)` — the parent already handles symbol database lookup and JSON parse. If `type_hint` is a `BaseModel` subclass, convert: `MessageToDict(pb2_result, preserving_proto_field_name=True, including_default_value_fields=True, use_integers_for_enums=True)` → `type_hint.model_validate(d)`. Otherwise return `pb2_result`.
- **Interfaces:** Extends `temporalio.converter.JSONProtoPayloadConverter`. No change to `encoding` (`"json/protobuf"`).

#### `PydanticBinaryProtoPayloadConverter`

- **Purpose:** Extend `BinaryProtoPayloadConverter` with Pydantic awareness for the `binary/protobuf` slot.
- **Responsibilities:**
  - `to_payload(value)`: Same as above — look up `pb2_cls` from `REGISTRY`, call `ParseDict(value.model_dump(mode="json"), pb2_cls())`, delegate to `super().to_payload(pb2_instance)`. In the default composite this method is never reached for `_p2p` models (the JSON converter fires first) but must be correct for standalone use.
  - `from_payload(payload, type_hint)`: Call `pb2_result = super().from_payload(payload)` — parent handles symbol database lookup and `ParseFromString`. If `type_hint` is a `BaseModel` subclass, convert via `MessageToDict` (same options as above) → `type_hint.model_validate(d)`. Otherwise return `pb2_result`.
- **Interfaces:** Extends `temporalio.converter.BinaryProtoPayloadConverter`. No change to `encoding` (`"binary/protobuf"`).

#### `proto_pydantic_data_converter`

- **Purpose:** Module-level `DataConverter` instance that replaces `pydantic_data_converter` in worker setup.
- **Responsibilities:** Compose the full converter chain.
- **Interfaces:** `temporalio.converter.DataConverter` instance; passed directly as `data_converter=` in `Client.connect`.

#### `_pb2_registry`

- **Purpose:** Import all domain `_pb2` modules at startup to populate the protobuf symbol database.
- **Responsibilities:** Issue one `import` statement per `_pb2` module file. Nothing else.
- **Interfaces:** Module-level side effects only. Imported once from `fulfillment_worker.py` (and any other workers that use the converter) before the `Client` is constructed.

### `_p2p` → `_pb2` Registry

The registry is a generated Python module at `src/converter/_registry.py`:

```python
# AUTO-GENERATED by scripts/gen_converter_registry.py — do not edit
from google.protobuf.message import Message
from pydantic import BaseModel

from acme.fulfillment.domain.v1.shipping_agent_p2p import CalculateShippingOptionsRequest
from acme.fulfillment.domain.v1.shipping_agent_pb2 import CalculateShippingOptionsRequest as _pb2_CalculateShippingOptionsRequest
# ... one pair of imports per message type across all generated packages

REGISTRY: dict[type[BaseModel], type[Message]] = {
    CalculateShippingOptionsRequest: _pb2_CalculateShippingOptionsRequest,
    # ...
}
```

**Importing `_registry.py` populates the protobuf symbol database** as a side effect of the `_pb2` imports, eliminating the need for a separate `pb2_registry.py`.

**Edge cases:**

| Case | Behaviour |
|------|-----------|
| `type(value)` not in `REGISTRY` | `to_payload` returns `None`; falls through to `PydanticJSONPlainPayloadConverter` (handles hand-written Pydantic models) |
| Class exists in `_p2p` but not in `_pb2` module | Script fails at codegen time with an `AttributeError` — never reaches runtime |
| New `.proto` added but script not re-run | Class missing from `REGISTRY` → falls through to `json/plain` instead of `json/protobuf` — caught by CI if the converter test covers the new type |
| Incoming `json/protobuf` or `binary/protobuf` with no `messageType` | Parent `from_payload` raises `RuntimeError("Unknown Protobuf type <unknown>")` — same as before |

### Converter Pseudocode — both classes follow the same delegation pattern

```python
# _converters.py
from google.protobuf.json_format import MessageToDict, ParseDict
from pydantic import BaseModel
from temporalio.converter import BinaryProtoPayloadConverter, JSONProtoPayloadConverter
from ._registry import REGISTRY

_MSGTODICT_OPTS = dict(
    preserving_proto_field_name=True,
    including_default_value_fields=True,
    use_integers_for_enums=True,
)

class PydanticJsonProtoPayloadConverter(JSONProtoPayloadConverter):
    def to_payload(self, value):
        if isinstance(value, BaseModel):
            pb2_cls = REGISTRY.get(type(value))
            if pb2_cls is None:
                return None  # not a generated _p2p type — fall through to json/plain
            pb2 = ParseDict(value.model_dump(mode="json"), pb2_cls())
            return super().to_payload(pb2)       # delegate JSON serialization to SDK
        return super().to_payload(value)         # raw Message or unhandled → SDK decides

    def from_payload(self, payload, type_hint=None):
        pb2 = super().from_payload(payload)      # SDK handles sym_db lookup + JSON parse
        if isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
            return type_hint.model_validate(MessageToDict(pb2, **_MSGTODICT_OPTS))
        return pb2


class PydanticBinaryProtoPayloadConverter(BinaryProtoPayloadConverter):
    def to_payload(self, value):
        if isinstance(value, BaseModel):
            pb2_cls = REGISTRY.get(type(value))
            if pb2_cls is None:
                return None
            pb2 = ParseDict(value.model_dump(mode="json"), pb2_cls())
            return super().to_payload(pb2)       # delegate binary serialization to SDK
        return super().to_payload(value)

    def from_payload(self, payload, type_hint=None):
        pb2 = super().from_payload(payload)      # SDK handles sym_db lookup + ParseFromString
        if isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
            return type_hint.model_validate(MessageToDict(pb2, **_MSGTODICT_OPTS))
        return pb2
```

Both overrides are identical in structure: `to_payload` adds Pydantic→pb2 before delegating; `from_payload` delegates first, then optionally converts pb2→Pydantic. All serialization format details (compact JSON, `messageType` metadata, `SerializeToString`) live in the SDK parent classes and are not reimplemented.

### Converter Composition

```python
# __init__.py
from temporalio.contrib.pydantic import PydanticJSONPlainPayloadConverter
from temporalio.converter import (
    BinaryNullPayloadConverter,
    BinaryPlainPayloadConverter,
    CompositePayloadConverter,
    DataConverter,
)
from ._converters import PydanticBinaryProtoPayloadConverter, PydanticJsonProtoPayloadConverter


class ProtoPydanticPayloadConverter(CompositePayloadConverter):
    def __init__(self) -> None:
        super().__init__(
            BinaryNullPayloadConverter(),
            BinaryPlainPayloadConverter(),
            PydanticJsonProtoPayloadConverter(),    # json/protobuf — wins for outbound _p2p encoding
            PydanticBinaryProtoPayloadConverter(),  # binary/protobuf — decode only in practice
            PydanticJSONPlainPayloadConverter(),    # json/plain — reuses pydantic contrib for all other types
        )


proto_pydantic_data_converter = DataConverter(
    payload_converter_class=ProtoPydanticPayloadConverter,
)
```

**Composition notes:**

- `DefaultPayloadConverter` (the SDK default) uses `[BinaryNull, BinaryPlain, JSONProto, BinaryProto, JSONPlain]`. This composite replaces `JSONProto` and `BinaryProto` with the Pydantic-aware subclasses and replaces bare `JSONPlain` with `PydanticJSONPlainPayloadConverter`.
- `BinaryProtoPayloadConverter` (bare SDK) is intentionally omitted — both custom converters already handle raw `Message` instances via `super().to_payload(value)`.
- `PydanticJSONPlainPayloadConverter` is imported directly from `temporalio.contrib.pydantic` — no reimplementation. It handles all non-proto Pydantic models (hand-written types, LLM tool-call result types, etc.) using `pydantic_core.to_json` and `TypeAdapter.validate_json`.
- Decoding routes by `encoding` header — order is irrelevant for `from_payload`. Encoding iterates in order — `PydanticJsonProtoPayloadConverter` fires first for `_p2p` models and returns a non-None payload, so the binary converter's `to_payload` is never reached for those types.

### Descriptor Registration Strategy

The protobuf symbol database must be populated before `Client.connect`. **Importing `src.converter` is sufficient** — `_registry.py` is imported by `__init__.py`, and `_registry.py` imports every `_pb2` module as a side effect of building the `REGISTRY` dict. No separate `pb2_registry.py` is needed.

Workers get this for free by importing the converter:

```python
from src.converter import proto_pydantic_data_converter  # also populates sym_db
```

### Configuration / Deployment

No environment variables or configuration changes required. The converter is purely in-process. The change is confined to:

1. A new package `python/fulfillment/src/converter/`
2. A new script `scripts/gen_converter_registry.py` (invoked during proto generation)
3. One-line change per worker file (swap `data_converter=`)

---

## Implementation Strategy

### Phases

**Phase 1: Registry Script + Generated Registry**
- Write `scripts/gen_converter_registry.py`
- Run it to produce `python/fulfillment/src/converter/_registry.py`
- Wire the script into the proto generation Makefile target

**Phase 2: Core Converter Package**
- Create `python/fulfillment/src/converter/__init__.py`, `_converters.py`
- Implement `PydanticJsonProtoPayloadConverter` and `PydanticBinaryProtoPayloadConverter` as SDK subclasses
- Assemble `ProtoPydanticPayloadConverter` and `proto_pydantic_data_converter`

**Phase 3: Wire Up Workers**
- Update `fulfillment_worker.py`, `shipping_worker.py`: replace `pydantic_data_converter` with `proto_pydantic_data_converter`
- Verify no application code changed

**Phase 4: Tests**
- Unit tests for round-trip encode/decode
- Verify wire format (metadata headers)
- Verify Java-compatible output

### Critical Files / Modules

To Create:
- `python/fulfillment/src/converter/__init__.py` — `ProtoPydanticPayloadConverter`, `proto_pydantic_data_converter`
- `python/fulfillment/src/converter/_converters.py` — `PydanticJsonProtoPayloadConverter`, `PydanticBinaryProtoPayloadConverter`
- `python/fulfillment/src/converter/_registry.py` — **auto-generated**; do not edit by hand
- `scripts/gen_converter_registry.py` — prebuild script that produces `_registry.py`

To Modify:
- `python/fulfillment/src/workers/fulfillment_worker.py` — replace `pydantic_data_converter` with `proto_pydantic_data_converter`
- `python/fulfillment/src/workers/shipping_worker.py` — same
- `Makefile` (or `buf.gen.yaml` post-hook) — add `gen_converter_registry.py` to the proto generation step

---

## Testing Strategy

### Unit Tests

All tests in `python/fulfillment/tests/test_converter.py`.

- **JSON round-trip:** Construct a `CalculateShippingOptionsRequest`, call `PydanticJsonProtoPayloadConverter().to_payload`, assert `encoding == b"json/protobuf"` and `messageType` is set, then call `from_payload` with the Pydantic type as `type_hint`, assert the result equals the original.
- **Binary round-trip:** Same using `PydanticBinaryProtoPayloadConverter`, assert `encoding == b"binary/protobuf"`.
- **Composite outbound encoding:** Call `ProtoPydanticPayloadConverter().to_payloads([model])` and assert `encoding == b"json/protobuf"` (JSON converter wins in composite).
- **Java-compat JSON format:** The `json/protobuf` payload data should be compact camelCase JSON (matching `JSONProtoPayloadConverter` parent behaviour — the spec's earlier `preserving_proto_field_name` concern applies only to the `from_payload` `MessageToDict` call, not the outbound format).
- **Null passthrough:** `to_payload(None)` from each custom converter returns `None` (parent behaviour preserved).
- **Primitive passthrough:** `to_payload("hello")` returns `None` from each custom converter.
- **Non-registry Pydantic fallthrough:** A hand-written `BaseModel` not in `REGISTRY` returns `None` from both converters; the composite encodes it via `PydanticJSONPlainPayloadConverter`.
- **Unknown `messageType`:** Both `from_payload` implementations raise `RuntimeError("Unknown Protobuf type …")` — inherited from the SDK parent.
- **Nested message:** `StartOrderFulfillmentRequest` (contains `PlacedOrder` → `FulfillmentItem` list) round-trips correctly for both JSON and binary encodings.
- **Enum round-trip:** `NotifyDeliveryStatusRequest` (contains `DeliveryStatus` `IntEnum`) encodes and decodes correctly; `use_integers_for_enums=True` in `MessageToDict` ensures Pydantic `IntEnum` round-trips without error.
- **Registry completeness:** Assert that every `_p2p` class importable from `python/generated/pydantic/` has an entry in `REGISTRY` — catches a stale registry before deployment.

### Integration Tests

- **Nexus boundary smoke test:** In the existing `test_shipping_agent.py`, verify that `ShippingAgentImpl.calculate_shipping_options` can be called with a payload encoded by the converter and returns a correctly decoded `CalculateShippingOptionsResponse`. (Uses `temporalio.testing.WorkflowEnvironment` — no real Java process required; encode the input manually with `proto_pydantic_data_converter` before passing to the Nexus test helper.)

### Validation Checklist

- [ ] All unit tests pass (`pytest python/fulfillment/tests/test_converter.py`)
- [ ] All existing tests in `test_shipping_agent.py` and `test_tool_dispatch.py` continue to pass
- [ ] Registry completeness test passes (every `_p2p` class has a `REGISTRY` entry)
- [ ] Worker starts without error when `src.converter` is imported (smoke: `python -c "from src.converter import proto_pydantic_data_converter"`)
- [ ] Payload inspection confirms `messageType` header matches the fully-qualified proto name (e.g. `acme.fulfillment.domain.fulfillment.v1.CalculateShippingOptionsRequest`)

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| `_pb2` module not imported → `RuntimeError("Unknown Protobuf type …")` at runtime | High | Low | `_registry.py` imports all `_pb2` modules; importing `src.converter` guarantees registration before any Client is created |
| `MessageToDict` produces camelCase keys instead of snake_case | High | Low | Pass `preserving_proto_field_name=True` explicitly; covered by the Java-compat output test |
| `including_default_value_fields=False` (default) causes Pydantic validation errors for required fields | Med | Med | Pass `including_default_value_fields=True`; round-trip test catches missing fields |
| Timestamp fields (`google.protobuf.Timestamp`) serialise as ISO strings in `MessageToDict`; Pydantic may reject them | Med | Med | Pydantic v2's `datetime` fields accept ISO 8601 strings; covered by the `FulfilledOrderEvent` nested test (contains `fulfilled_at`) |
| Enum fields: `MessageToDict` emits the enum name string by default; Pydantic `IntEnum` expects an integer | Med | Med | Pass `use_integers_for_enums=True`; IntEnum accepts integers. Covered by `DeliveryStatus` round-trip test. |
| `binary/protobuf` payload missing `messageType` header | High | Low | Raises `ValueError` with clear message; Java and other well-behaved senders always include `messageType`; covered by missing-header unit test |
| Existing workflow histories recorded as `json/plain` become undecodable | High | None (greenfield) | This is a greenfield deployment with no existing workflow history; acknowledged below |

---

## Dependencies

### External Dependencies

- `google-protobuf` — `MessageToJson`, `MessageToDict`, `Parse`, `ParseDict`, `symbol_database` (already a transitive dependency)
- `temporalio` — `EncodingPayloadConverter`, `CompositePayloadConverter`, `DataConverter` (already present)
- `pydantic` v2 — `BaseModel.model_dump(mode="json")`, `model_validate` (already present)

### Cross-Cutting Concerns

- Both Python workers (`fulfillment_worker`, `shipping_worker`) use `pydantic_data_converter` today and must be updated in the same commit to maintain a consistent wire format across task queues.
- The converter applies to **all** payloads on a worker, not just Nexus payloads. Python-internal activity inputs/outputs that are currently `json/plain` Pydantic models will become `json/protobuf`. This is the desired end state but requires the round-trip test to confirm no regressions.

### Rollout Blockers

- None. This is a greenfield system with no existing workflow history.

---

## Open Questions & Notes

### Questions for Tech Lead / Product

- [x] Should `shipping_worker` receive the same converter in this PR, or in a follow-up? **Same PR** — consistent wire format is a system-wide invariant, not a per-worker choice.

### Implementation Notes

- **`model_dump(mode="json")`:** Use `mode="json"` so `datetime` fields become ISO strings that `ParseDict` can parse into `google.protobuf.Timestamp`.
- **Outbound JSON is camelCase:** `JSONProtoPayloadConverter.to_payload` calls `MessageToDict(value)` without `preserving_proto_field_name` — output is camelCase, matching the proto JSON standard and Java's `DefaultDataConverter`. This is correct; do not add `preserving_proto_field_name=True` to the outbound path.
- **Inbound decode uses snake_case:** `MessageToDict(pb2, preserving_proto_field_name=True, ...)` in `from_payload` produces snake_case keys for Pydantic. This is separate from the outbound format.
- **`including_default_value_fields=True` matters:** Without it, `MessageToDict` omits fields with zero/false/empty values. Pydantic models with non-Optional fields would fail validation. Include it.
- **`gen_converter_registry.py` is the only place that knows the `_p2p`/`_pb2` pairing.** Neither converter class nor any worker code should reference the naming convention. If the pairing logic ever needs to change, it changes in one script.
- **`pb2_registry.py` is no longer needed.** Importing `src.converter` is sufficient to populate the symbol database via `_registry.py`'s `_pb2` imports. Remove any existing `pb2_registry.py` imports from workers.

---

## Migration Note

This is a **greenfield deployment**. No Temporal workflows are currently running or have recorded history in the `fulfillment` namespace. The converter swap requires no history migration and no backward-compatibility shims. If workflows were running, the `json/plain` payloads in existing history would be undecodable by the new converter — that scenario does not apply here.

---

## References & Links

- `python/fulfillment/src/workers/fulfillment_worker.py` — current worker setup (`data_converter=pydantic_data_converter`)
- `python/fulfillment/src/services/shipping_agent_impl.py` — Nexus handler (must remain pure Pydantic)
- `python/generated/pydantic/acme/fulfillment/domain/v1/shipping_agent_p2p.py` — example Pydantic generated types
- `python/generated/acme/fulfillment/domain/v1/shipping_agent_pb2.py` — corresponding pb2 types
- `proto/README.md` — handler-owns-contract principle
- Temporal Python SDK: `temporalio.converter` — `JSONProtoPayloadConverter`, `BinaryProtoPayloadConverter`, `CompositePayloadConverter`, `DataConverter`
- Temporal Python SDK: `temporalio.contrib.pydantic` — `PydanticJSONPlainPayloadConverter`
- protobuf Python: `google.protobuf.json_format` — `MessageToDict`, `ParseDict`
- protobuf Python: `google.protobuf.symbol_database` — used internally by SDK parent classes
