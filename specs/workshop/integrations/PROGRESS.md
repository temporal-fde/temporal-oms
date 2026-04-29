# Workshop Integrations - Progress Tracking

**Spec:** [spec.md](./spec.md)
**Last Updated:** 2026-04-29
**Current Status:** Implementation complete for runtime integration work; workshop exercise material remains open.

---

## Phase Status

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| Phase 1 | Document and Align Requirements | ✅ Complete | `enablements-api` module added; protobuf JSON converter pattern copied; REST surface and service/cache shape implemented. |
| Phase 2 | EasyPost Fixture Capture | ✅ Complete | Offline capture script and seeded `shipping-fixtures.json` are present. Live EasyPost capture was not re-run during this review because it requires credentials/network. |
| Phase 3 | Shipping Runtime Service | ✅ Complete | Fixture-backed address verification, rate lookup, synthetic labels, scenario mutation, fixture-state endpoints, and compatibility service method are implemented. |
| Phase 4 | Location-Events Integration Service | ✅ Complete | `enablements-api` endpoint and service return `RISK_LEVEL_NONE`, empty events, and echoed request window/timezone. |
| Phase 5 | ShippingAgent Dispatch Migration | ✅ Complete | Python enablements HTTP client/adapters are in place; existing LLM-facing tool names remain stable. |
| Phase 6 | Fulfillment Carrier Migration | ✅ Complete | Java `CarriersImpl` now delegates address verification and label printing to `enablements-api`; runtime EasyPost calls are removed from the fulfillment carrier path. |
| Phase 7 | Workshop Exercise Material | 🟡 Partial | Scenario runner and margin/SLA walkthrough scripts exist; exercise notes and fixture-state query examples still need to be added. |

---

## Completed Deliverables

### Phase 1 - Document and Align Requirements

- [x] Reviewed spec and confirmed the in-scope services: commerce-app, PIMS, inventory, shipping, and location-events
- [x] Added `enablements-api` module to `java/enablements/pom.xml`
- [x] Kept payments out of the workshop integration path
- [x] Copied `ProtobufJsonHttpMessageConverter` into `enablements-api`
- [x] Added `WebMvcConfig` in `enablements-api` to register the protobuf JSON converter first
- [x] Implemented `enablements-api` integration services and REST endpoint shape
- [x] Implemented request-field scenario triggers for invalid orders, margin spike, and SLA breach

### Phase 2 - EasyPost Fixture Capture

- [x] Seeded warehouse and destination addresses in `shipping-fixtures.json`
- [x] Added roughly 10 legitimate destination addresses for route/rate variety
- [x] Added offline capture script: `scripts/capture-easypost-fixtures.py`
- [x] Script verifies addresses through EasyPost when run with `EASYPOST_API_KEY` or `--api-key`
- [x] Script captures shipments and all returned rates for configured routes
- [x] Script synthesizes deterministic labels without buying labels
- [x] Wrote canonical fixture file: `java/enablements/enablements-api/src/main/resources/fixtures/shipping-fixtures.json`

### Phase 3 - Shipping Runtime Service

- [x] Created fixture loader/cache in `ShippingFixtureService`
- [x] Implemented `verifyAddress(VerifyAddressRequest)` from fixtures
- [x] Implemented `getShippingRates(GetShippingRatesRequest)` from fixtures
- [x] Implemented `printShippingLabel(PrintShippingLabelRequest)` from fixtures
- [x] Implemented `getCarrierRates(GetCarrierRatesRequest)` compatibility method
- [x] Added deterministic mutation for `paid_price.units=1`
- [x] Preserved and handled explicit `delivery_days=0`
- [x] Exposed shipping REST endpoints under `/api/v1/integrations/shipping/**`
- [x] Added fixture-state endpoints for shipping and all fixtures

### Phase 4 - Location-Events Integration Service

- [x] Added `LocationEventsIntegrationService` inside `enablements-api`
- [x] First pass returns empty events and `RISK_LEVEL_NONE`
- [x] Echoes request window and timezone
- [x] Exposes `GET /api/v1/integrations/location-events`
- [x] Keeps fixture config visible through fixture-state responses

### Phase 5 - ShippingAgent Dispatch Migration

- [x] Added Python HTTP client: `python/fulfillment/src/services/enablements_integrations.py`
- [x] Kept LLM-facing tool names stable: `get_location_events` and `get_carrier_rates`
- [x] Kept request/response protos unchanged
- [x] Replaced Python EasyPost activity behavior with calls to `enablements-api`
- [x] Replaced Python location-events activity behavior with calls to `enablements-api`
- [x] Preserved `selected_shipment` handling, including explicit zero `delivery_days`

### Phase 6 - Fulfillment Carrier Migration

- [x] Replaced `CarriersImpl.verifyAddress` EasyPost call path with `enablements-api`
- [x] Replaced `CarriersImpl.printShippingLabel` EasyPost call path with `enablements-api`
- [x] Removed EasyPost as a runtime dependency for fulfillment carrier operations
- [x] Preserved deterministic non-retryable failures for invalid address/rate requests

### Phase 7 - Workshop Exercise Material

- [ ] Add exercise notes explaining why integrations are owned by `enablements-api`
- [ ] Add a query/check script for the `enablements-api` fixture state endpoint
- [ ] Add a scenario that demonstrates inventory lookup, alternate warehouse lookup, and location risk in one ShippingAgent run
- [x] Add a scenario that demonstrates `paid_price.units=1` margin leak/spike
- [x] Add a scenario that demonstrates `delivery_days=0` SLA breach
- [x] Add a dynamic scenario selector that discovers `scripts/scenarios/*/run.sh`
- [x] Generate unique order/workflow IDs and unique customer IDs for scenario runs
- [ ] Add a script or REST example that lists fixture addresses, rates, shipments, and labels

---

## Review Notes

- `enablements-api` exists as a sibling module under `java/enablements`.
- REST endpoints use generated protobuf messages directly where practical, with query-encoded protobuf JSON for complex `GET` inputs.
- The copied protobuf JSON converter includes default values, which keeps explicit zero values observable.
- `apps.Integrations` remains prior art/current compatibility infrastructure. Nexus handlers for
  commerce-app, PIMS, and inventory still use it today; rerouting those handlers to
  `enablements-api` is a planned follow-up.
- Python shipping activity class and task queue names are now `ShippingActivities` and
  `fulfillment-shipping`; LLM-facing tool names remain stable.
- The offline EasyPost capture script was reviewed but not executed during this progress update because it requires EasyPost credentials and network access.

---

## Validation

- [x] `env -u JAVA_HOME mvn -pl enablements/enablements-api,fulfillment/fulfillment-core -am test`
  - `IntegrationServicesTest`: 11 passed
  - `CarriersImplTest`: 3 passed
- [x] `python/.venv/bin/python -m pytest python/fulfillment/tests/test_enablements_integrations_client.py`
  - 2 passed
- [x] `mvn -pl enablements/enablements-api,fulfillment/fulfillment-core -am -DskipTests compile`
  - Build success
- [x] Focused ShippingAgent Temporal tests pass with fixture-backed shipping and location-events paths.

---

## Open Items

- Complete Phase 7 workshop material.
- Reroute the existing Nexus integration handlers to use `enablements-api` as their backend.
- Decide later whether `apps.Integrations` should be deprecated or retained as compatibility/prior-art infrastructure.
- If Java tests are run from this shell, unset or update `JAVA_HOME`; it currently points Maven at Java 17 while this project compiles Java 21 classfiles.
