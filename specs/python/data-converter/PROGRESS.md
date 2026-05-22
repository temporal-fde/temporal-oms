# Progress: Protobuf Pydantic Data Converter

**Spec:** [SPEC.md](SPEC.md)
**Status:** Complete
**Started:** 2026-04-25
**Completed:** 2026-04-25

## Phases

- [x] Phase 1: Registry script + generated `_registry.py`
- [x] Phase 2: Converter package (`__init__.py`, `_converters.py`)
- [x] Phase 3: Wire up workers
- [x] Phase 4: Tests

## Checklist

- [x] `scripts/gen_converter_registry.py` written
- [x] `python/fulfillment/src/converter/_registry.py` generated (145 entries, 13 modules)
- [x] `python/fulfillment/src/converter/__init__.py` created
- [x] `python/fulfillment/src/converter/_converters.py` created
- [x] `fulfillment_worker.py` updated
- [x] `shipping_worker.py` updated
- [x] ~~`predicthq_worker.py`~~ removed (PredictHQ replaced — see `specs/fulfillment/location-events/`)
- [x] `tests/test_converter.py` written and passing (15/15)
- [x] Registry completeness test passing
- [x] Existing tests (`test_shipping_agent.py`, `test_tool_dispatch.py`) still passing (22/22)

## Notes

- `buf.gen.yaml` Python plugin pinned to `v33.0` (generates protobuf gencode 6.33.0, compatible with installed runtime 6.33.6; `temporalio==1.26.0` requires `protobuf<7.0.0`)
- `gen_converter_registry.py` scans `tree.body` (top-level only) to skip nested classes like `OmsProperties.BoundedContextConfig` that aren't accessible as module-level attributes
- Naive datetime strings from `model_dump(mode="json")` get `Z` appended before `ParseDict` — protobuf's Timestamp parser uses `rfind('-')` to find timezone offset which would otherwise match the date separator
- `MessageToDict` option `including_default_value_fields` was renamed to `always_print_fields_with_no_presence` in protobuf 6.x
