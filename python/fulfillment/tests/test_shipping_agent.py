"""Unit tests for ShippingAgent workflow.

Uses Temporal Python test framework with mocked activities.
All tests run with retry_policy.maximum_attempts=1 and treat all exceptions as failures.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncIterator

import pytest
import temporalio.api.nexus.v1 as nexus_v1
import temporalio.api.operatorservice.v1 as operator_v1
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

from acme.common.v1.llm_p2p import (
    LlmContentBlock,
    LlmMessage,
    LlmResponse,
    LlmRole,
    LlmStopReason,
    LlmTextBlock,
    LlmToolDefinition,
    LlmToolResultBlock,
    LlmToolUseBlock,
)
from acme.common.v1.values_p2p import (
    Address,
    Coordinate,
    EasyPostAddress,
    EasyPostRate,
    EasyPostShipment,
    Money,
    Shipment,
)
from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    BuildSystemPromptRequest,
    BuildSystemPromptResponse,
    CalculateShippingOptionsRequest,
    CalculateShippingOptionsResponse,
    GetLocationEventsRequest,
    GetLocationEventsResponse,
    GetShippingRatesRequest,
    GetShippingRatesResponse,
    RecommendationOutcome,
    ShippingAgentExecutionOptions,
    ShippingLineItem,
    ShippingOption,
    ShippingOptionsResult,
    ShippingRecommendation,
    StartShippingAgentRequest,
)
from acme.fulfillment.domain.v1.inventory_p2p import (
    FindAlternateWarehouseRequest,
    FindAlternateWarehouseResponse,
    LookupInventoryAddressRequest,
    LookupInventoryAddressResponse,
)
from acme.fulfillment.domain.v1.values_p2p import LocationRiskSummary, RiskLevel
from acme.fulfillment.domain.v1.workflows_p2p import (
    VerifyAddressRequest,
    VerifyAddressResponse,
)
from nexusrpc.handler import StartOperationContext, service_handler, sync_operation
from src.agents.workflows.shipping_agent import ShippingAgent
from src.services.inventory_service import InventoryService

# ─── Constants ────────────────────────────────────────────────────────────────

_WF_TASK_QUEUE = "fulfillment"
_CUSTOMER_ID = "customer-test-1"
_ORDER_ID = "order-test-1"
_TO_ADDRESS = Address(
    easypost=EasyPostAddress(
        id="adr_dest",
        street1="123 Main St",
        city="New York",
        state="NY",
        zip="10001",
        country="US",
        residential=True,
        coordinate=Coordinate(latitude=40.712, longitude=-74.006),
    ),
)

_FROM_ADDRESS = Address(
    easypost=EasyPostAddress(
        id="adr_wh_east_01",
        street1="100 Commerce Drive",
        city="Newark",
        state="NJ",
        zip="07102",
        country="US",
    ),
)

_ITEMS = [ShippingLineItem(sku_id="ELEC-001", quantity=2)]

_PROCEED_INPUT = {
    "outcome": "PROCEED",
    "recommended_option_id": "rate_001",
    "reasoning": "The selected rate is within budget and meets SLA.",
    "margin_delta_cents": -500,
    "origin_risk_level": "RISK_LEVEL_NONE",
    "destination_risk_level": "RISK_LEVEL_LOW",
}

_MARGIN_SPIKE_INPUT = {
    "outcome": "MARGIN_SPIKE",
    "recommended_option_id": "rate_002",
    "reasoning": "Original rate exceeds customer paid price.",
    "margin_delta_cents": 1500,
    "origin_risk_level": "RISK_LEVEL_NONE",
    "destination_risk_level": "RISK_LEVEL_NONE",
}

_SLA_BREACH_INPUT = {
    "outcome": "SLA_BREACH",
    "recommended_option_id": "",
    "reasoning": "No available rate meets the 2-day SLA.",
    "margin_delta_cents": 0,
    "origin_risk_level": "RISK_LEVEL_NONE",
    "destination_risk_level": "RISK_LEVEL_NONE",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _finalize_response(input_dict: dict, tool_id: str = "tu_final") -> LlmResponse:
    """Build a TOOL_USE response that calls finalize_recommendation."""
    return _tool_use_response([(tool_id, "finalize_recommendation", input_dict)])


def _tool_use_response(calls: list[tuple[str, str, dict]]) -> LlmResponse:
    """Build a tool_use LlmResponse. calls = [(id, name, input_dict), ...]"""
    blocks = [
        LlmContentBlock(
            type="tool_use",
            tool_use=LlmToolUseBlock(id=call_id, name=name, input=inp),
        )
        for call_id, name, inp in calls
    ]
    return LlmResponse(
        content=blocks,
        stop_reason=LlmStopReason.LLM_STOP_REASON_TOOL_USE,
    )


def _base_request(
    *,
    selected_paid_price: Money | None = None,
    selected_delivery_days: int | None = None,
) -> CalculateShippingOptionsRequest:
    kwargs = {
        "order_id": _ORDER_ID,
        "customer_id": _CUSTOMER_ID,
        "to_address": _TO_ADDRESS,
        "items": _ITEMS,
    }
    if selected_paid_price is not None or selected_delivery_days is not None:
        kwargs["selected_shipment"] = Shipment(
            easypost=EasyPostShipment(
                shipment_id="shp_selected",
                selected_rate=EasyPostRate(
                    rate_id="rate_selected",
                    delivery_days=selected_delivery_days if selected_delivery_days is not None else 5,
                ),
            ),
            paid_price=selected_paid_price or Money(currency="USD", units=0),
        )
    return CalculateShippingOptionsRequest(**kwargs)


_START_REQUEST = StartShippingAgentRequest(
    customer_id=_CUSTOMER_ID,
    execution_options=ShippingAgentExecutionOptions(cache_ttl_secs=1800),
)

_WF_RETRY = RetryPolicy(maximum_attempts=1)

_INTEGRATIONS_ENDPOINT = "oms-integrations-v1"


@asynccontextmanager
async def _test_env() -> AsyncIterator[WorkflowEnvironment]:
    """Start a time-skipping test environment with the integrations Nexus endpoint registered."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        spec = nexus_v1.EndpointSpec(name=_INTEGRATIONS_ENDPOINT)
        spec.target.worker.namespace = env.client.namespace
        spec.target.worker.task_queue = "fulfillment"
        await env.client.operator_service.create_nexus_endpoint(
            operator_v1.CreateNexusEndpointRequest(spec=spec)
        )
        yield env


async def _start_agent(client: Client, wf_id: str = _CUSTOMER_ID) -> object:
    return await client.start_workflow(
        ShippingAgent.run,
        _START_REQUEST,
        id=wf_id,
        task_queue=_WF_TASK_QUEUE,
        retry_policy=_WF_RETRY,
    )


# ─── Mock activities ──────────────────────────────────────────────────────────

_LOOKUP_RESULT = LookupInventoryAddressResponse(
    address=_FROM_ADDRESS,
)

_VERIFY_RESULT = VerifyAddressResponse(
    address=Address(
        easypost=EasyPostAddress(
            id="adr_origin",
            street1=_FROM_ADDRESS.easypost.street1,
            city=_FROM_ADDRESS.easypost.city,
            state=_FROM_ADDRESS.easypost.state,
            zip=_FROM_ADDRESS.easypost.zip,
            country=_FROM_ADDRESS.easypost.country,
            residential=False,
            coordinate=Coordinate(latitude=40.734, longitude=-74.172),
        ),
    )
)

_RATES_RESULT = GetShippingRatesResponse(
    shipment_id="shp_001",
    options=[
        ShippingOption(
            id="rate_001", carrier="UPS", service_level="Ground",
            cost=Money(currency="USD", units=1200), estimated_days=5, rate_id="rate_001",
        ),
    ],
)


@service_handler(service=InventoryService)
class MockInventoryService:
    @sync_operation
    async def lookupInventoryAddress(
        self, ctx: StartOperationContext, req: LookupInventoryAddressRequest
    ) -> LookupInventoryAddressResponse:
        return _LOOKUP_RESULT

    @sync_operation
    async def findAlternateWarehouse(
        self, ctx: StartOperationContext, req: FindAlternateWarehouseRequest
    ) -> FindAlternateWarehouseResponse:
        return FindAlternateWarehouseResponse()


@activity.defn(name="verify_address")
async def mock_verify_address(req: VerifyAddressRequest) -> VerifyAddressResponse:
    return _VERIFY_RESULT


@activity.defn(name="get_carrier_rates")
async def mock_get_carrier_rates(req: GetShippingRatesRequest) -> GetShippingRatesResponse:
    return _RATES_RESULT


@activity.defn(name="get_location_events")
async def mock_get_location_events(req: GetLocationEventsRequest) -> GetLocationEventsResponse:
    return GetLocationEventsResponse(
        summary=LocationRiskSummary(
            overall_risk_level=RiskLevel.RISK_LEVEL_NONE,
            peak_rank=0,
            total_event_count=0,
            unscheduled_event_count=0,
            events_by_category={},
        ),
        events=[],
        window_from=req.active_from,
        window_to=req.active_to,
        timezone=req.timezone,
    )


@activity.defn(name="build_system_prompt")
async def mock_build_system_prompt(req: BuildSystemPromptRequest) -> BuildSystemPromptResponse:
    return BuildSystemPromptResponse(system_prompt="You are a shipping advisor.")


def _make_workers(
    client: Client,
    call_llm_impl,
    inventory_handler=None,
) -> list[Worker]:
    """Create one worker per task queue, all with the same mocked activities."""
    common_activities = [
        mock_build_system_prompt,
        mock_verify_address,
        mock_get_carrier_rates,
        mock_get_location_events,
        call_llm_impl,
    ]
    return [
        Worker(
            client,
            task_queue="fulfillment",
            workflows=[ShippingAgent],
            activities=common_activities,
            nexus_service_handlers=[inventory_handler or MockInventoryService()],
            workflow_failure_exception_types=[Exception],
        ),
        Worker(
            client,
            task_queue="fulfillment-shipping",
            activities=common_activities,
        ),
        Worker(
            client,
            task_queue="agents",
            activities=common_activities,
        ),
    ]


# ─── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_hit_skips_llm() -> None:
    """Second Update with same inputs returns cache_hit=True without calling call_llm."""
    llm_call_count = 0

    @activity.defn(name="call_llm")
    async def counting_call_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal llm_call_count
        llm_call_count += 1
        return _finalize_response(_PROCEED_INPUT)

    async with _test_env() as env:
        workers = _make_workers(env.client, counting_call_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)

            req = _base_request()
            resp1: CalculateShippingOptionsResponse = await handle.execute_update(
                ShippingAgent.calculate_shipping_options, req
            )
            assert resp1.cache_hit is False
            assert llm_call_count == 1

            resp2: CalculateShippingOptionsResponse = await handle.execute_update(
                ShippingAgent.calculate_shipping_options, req
            )
            assert resp2.cache_hit is True
            assert llm_call_count == 1  # call_llm NOT called again


@pytest.mark.asyncio
async def test_lookup_always_called() -> None:
    """lookup_inventory_address is always called to resolve the origin warehouse."""
    lookup_called = False

    @service_handler(service=InventoryService)
    class TrackingInventory:
        @sync_operation
        async def lookupInventoryAddress(
            self, ctx: StartOperationContext, req: LookupInventoryAddressRequest
        ) -> LookupInventoryAddressResponse:
            nonlocal lookup_called
            lookup_called = True
            return _LOOKUP_RESULT

        @sync_operation
        async def findAlternateWarehouse(
            self, ctx: StartOperationContext, req: FindAlternateWarehouseRequest
        ) -> FindAlternateWarehouseResponse:
            return FindAlternateWarehouseResponse()

    @activity.defn(name="call_llm")
    async def simple_llm(messages: list, tools: list) -> LlmResponse:
        return _finalize_response(_PROCEED_INPUT)

    async with _test_env() as env:
        common = [mock_build_system_prompt, mock_verify_address, mock_get_carrier_rates,
                  mock_get_location_events, simple_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, nexus_service_handlers=[TrackingInventory()],
                   workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-shipping", activities=common),
            Worker(env.client, task_queue="agents", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request()
            await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert lookup_called


@pytest.mark.asyncio
async def test_cart_path_calls_lookup() -> None:
    """When from_address is absent, LLM calls lookup_inventory_address first."""
    lookup_called = False
    turn = 0

    @service_handler(service=InventoryService)
    class TrackingInventory:
        @sync_operation
        async def lookupInventoryAddress(
            self, ctx: StartOperationContext, req: LookupInventoryAddressRequest
        ) -> LookupInventoryAddressResponse:
            nonlocal lookup_called
            lookup_called = True
            return _LOOKUP_RESULT

        @sync_operation
        async def findAlternateWarehouse(
            self, ctx: StartOperationContext, req: FindAlternateWarehouseRequest
        ) -> FindAlternateWarehouseResponse:
            return FindAlternateWarehouseResponse()

    @activity.defn(name="call_llm")
    async def cart_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            return _tool_use_response([
                ("tu_1", "lookup_inventory_address", {"items": [{"sku_id": "ELEC-001", "quantity": 2}]})
            ])
        return _finalize_response(_PROCEED_INPUT)

    async with _test_env() as env:
        common = [mock_build_system_prompt, mock_verify_address, mock_get_carrier_rates,
                  mock_get_location_events, cart_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, nexus_service_handlers=[TrackingInventory()],
                   workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-shipping", activities=common),
            Worker(env.client, task_queue="agents", activities=common),
        ):
            handle = await _start_agent(env.client)
            # Cart path: no from_address
            req = _base_request()
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert lookup_called
    assert resp.cache_hit is False


@pytest.mark.asyncio
async def test_sequential_tool_dispatch() -> None:
    """Single tool_use block per turn is dispatched one at a time."""
    call_order: list[str] = []
    turn = 0

    @service_handler(service=InventoryService)
    class TrackingInventory:
        @sync_operation
        async def lookupInventoryAddress(
            self, ctx: StartOperationContext, req: LookupInventoryAddressRequest
        ) -> LookupInventoryAddressResponse:
            return _LOOKUP_RESULT

        @sync_operation
        async def findAlternateWarehouse(
            self, ctx: StartOperationContext, req: FindAlternateWarehouseRequest
        ) -> FindAlternateWarehouseResponse:
            call_order.append("find_alternate_warehouse")
            return FindAlternateWarehouseResponse()

    @activity.defn(name="get_carrier_rates")
    async def tracking_rates(req: GetShippingRatesRequest) -> GetShippingRatesResponse:
        call_order.append("get_carrier_rates")
        return _RATES_RESULT

    @activity.defn(name="call_llm")
    async def sequential_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            return _tool_use_response([
                ("tu_1", "find_alternate_warehouse",
                 {"items": [{"sku_id": "ELEC-001", "quantity": 1}], "current_address_id": "adr_wh_east_01"}),
            ])
        if turn == 2:
            return _tool_use_response([
                ("tu_2", "get_carrier_rates",
                 {"from_easypost_id": "adr_wh_cent_01", "to_easypost_id": "adr_dest", "items": []}),
            ])
        return _finalize_response(_PROCEED_INPUT)

    async with _test_env() as env:
        common = [mock_build_system_prompt, mock_verify_address, tracking_rates,
                  mock_get_location_events, sequential_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, nexus_service_handlers=[TrackingInventory()],
                   workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-shipping", activities=common),
            Worker(env.client, task_queue="agents", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request()
            await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert call_order == ["find_alternate_warehouse", "get_carrier_rates"]


@pytest.mark.asyncio
async def test_concurrent_activity_dispatch() -> None:
    """Two tool_use blocks in one LLM response → both activities dispatched concurrently."""
    events_call_count = 0
    turn = 0

    @activity.defn(name="get_location_events")
    async def tracking_events(req: GetLocationEventsRequest) -> GetLocationEventsResponse:
        nonlocal events_call_count
        events_call_count += 1
        return GetLocationEventsResponse(
            summary=LocationRiskSummary(
                overall_risk_level=RiskLevel.RISK_LEVEL_NONE,
                peak_rank=0, total_event_count=0, unscheduled_event_count=0, events_by_category={},
            ),
            events=[], window_from=req.active_from, window_to=req.active_to, timezone=req.timezone,
        )

    @activity.defn(name="call_llm")
    async def concurrent_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            # Return two get_location_events calls in a single response
            return _tool_use_response([
                ("tu_1", "get_location_events", {
                    "coordinate": {"latitude": 40.712, "longitude": -74.006},
                    "within_km": 50,
                    "active_from": "2026-04-17T00:00:00Z",
                    "active_to": "2026-04-22T00:00:00Z",
                    "timezone": "America/New_York",
                }),
                ("tu_2", "get_location_events", {
                    "coordinate": {"latitude": 40.734, "longitude": -74.172},
                    "within_km": 50,
                    "active_from": "2026-04-17T00:00:00Z",
                    "active_to": "2026-04-22T00:00:00Z",
                    "timezone": "America/New_York",
                }),
            ])
        return _finalize_response(_PROCEED_INPUT)

    async with _test_env() as env:
        common = [mock_build_system_prompt, mock_verify_address, mock_get_carrier_rates,
                  tracking_events, concurrent_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, nexus_service_handlers=[MockInventoryService()],
                   workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-shipping", activities=common),
            Worker(env.client, task_queue="agents", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request()
            await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    # Both location event calls from the same LLM turn must have been dispatched
    assert events_call_count == 2


@pytest.mark.asyncio
async def test_proceed_outcome() -> None:
    @activity.defn(name="call_llm")
    async def proceed_llm(messages: list, tools: list) -> LlmResponse:
        return _finalize_response(_PROCEED_INPUT)

    async with _test_env() as env:
        workers = _make_workers(env.client, proceed_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)
            req = _base_request()
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.outcome == RecommendationOutcome.PROCEED


@pytest.mark.asyncio
async def test_margin_spike_outcome() -> None:
    """MARGIN_SPIKE accepted after find_alternate_warehouse is called first."""
    turn = 0

    @activity.defn(name="call_llm")
    async def margin_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            return _tool_use_response([
                ("tu_alt", "find_alternate_warehouse",
                 {"items": [{"sku_id": "ELEC-001", "quantity": 2}], "current_address_id": "adr_wh_east_01"}),
            ])
        return _finalize_response(_MARGIN_SPIKE_INPUT)

    async with _test_env() as env:
        workers = _make_workers(env.client, margin_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)
            req = _base_request(selected_paid_price=Money(currency="USD", units=1))
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.outcome == RecommendationOutcome.MARGIN_SPIKE
    assert resp.recommendation.margin_delta_cents == 1500


@pytest.mark.asyncio
async def test_sla_breach_outcome() -> None:
    """SLA_BREACH accepted after find_alternate_warehouse is called first."""
    turn = 0

    @activity.defn(name="call_llm")
    async def sla_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            return _tool_use_response([
                ("tu_alt", "find_alternate_warehouse",
                 {"items": [{"sku_id": "ELEC-001", "quantity": 2}], "current_address_id": "adr_wh_east_01"}),
            ])
        return _finalize_response(_SLA_BREACH_INPUT)

    async with _test_env() as env:
        workers = _make_workers(env.client, sla_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)
            req = _base_request(selected_delivery_days=2)
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.outcome == RecommendationOutcome.SLA_BREACH
    assert resp.cache_hit is False


@pytest.mark.asyncio
async def test_options_accumulate_across_primary_and_alternate_rate_calls() -> None:
    """The final response must include whichever rate the LLM recommends, even after alternate lookup."""
    turn = 0
    primary_rate_id = "rate_wh_east_01_nyc_ground"
    alternate_rate_id = "rate_wh_east_02_nyc_2day"

    @activity.defn(name="get_carrier_rates")
    async def route_rates(req: GetShippingRatesRequest) -> GetShippingRatesResponse:
        if req.from_easypost_id == "adr_wh_east_02":
            return GetShippingRatesResponse(
                shipment_id="shp_adr_wh_east_02_to_adr_dest_nyc_01",
                options=[
                    ShippingOption(
                        id=alternate_rate_id,
                        carrier="FedEx",
                        service_level="2Day",
                        cost=Money(currency="USD", units=990),
                        estimated_days=2,
                        rate_id=alternate_rate_id,
                    ),
                ],
            )
        return GetShippingRatesResponse(
            shipment_id="shp_adr_wh_east_01_to_adr_dest_nyc_01",
            options=[
                ShippingOption(
                    id=primary_rate_id,
                    carrier="UPS",
                    service_level="Ground",
                    cost=Money(currency="USD", units=780),
                    estimated_days=2,
                    rate_id=primary_rate_id,
                ),
            ],
        )

    @service_handler(service=InventoryService)
    class AlternateInventory:
        @sync_operation
        async def lookupInventoryAddress(
            self, ctx: StartOperationContext, req: LookupInventoryAddressRequest
        ) -> LookupInventoryAddressResponse:
            return _LOOKUP_RESULT

        @sync_operation
        async def findAlternateWarehouse(
            self, ctx: StartOperationContext, req: FindAlternateWarehouseRequest
        ) -> FindAlternateWarehouseResponse:
            return FindAlternateWarehouseResponse(
                address=Address(easypost=EasyPostAddress(id="adr_wh_east_02"))
            )

    @activity.defn(name="call_llm")
    async def sla_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            return _tool_use_response([
                ("tu_primary", "get_carrier_rates",
                 {"from_easypost_id": "adr_wh_east_01", "to_easypost_id": "adr_dest", "items": []}),
            ])
        if turn == 2:
            return _tool_use_response([
                ("tu_alt", "find_alternate_warehouse",
                 {"items": [{"sku_id": "ELEC-001", "quantity": 2}], "current_address_id": "adr_wh_east_01"}),
            ])
        if turn == 3:
            return _tool_use_response([
                ("tu_alt_rates", "get_carrier_rates",
                 {"from_easypost_id": "adr_wh_east_02", "to_easypost_id": "adr_dest", "items": []}),
            ])
        return _finalize_response({
            "outcome": "SLA_BREACH",
            "recommended_option_id": primary_rate_id,
            "reasoning": "No rate can satisfy same-day delivery.",
            "margin_delta_cents": 0,
            "origin_risk_level": "RISK_LEVEL_NONE",
            "destination_risk_level": "RISK_LEVEL_NONE",
        })

    async with _test_env() as env:
        common = [mock_build_system_prompt, mock_verify_address, route_rates,
                  mock_get_location_events, sla_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, nexus_service_handlers=[AlternateInventory()],
                   workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-shipping", activities=common),
            Worker(env.client, task_queue="agents", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request(selected_delivery_days=0)
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.recommended_option_id == primary_rate_id
    assert [option.id for option in resp.options] == [primary_rate_id, alternate_rate_id]


@pytest.mark.asyncio
async def test_margin_spike_enforces_alternate_warehouse() -> None:
    """MARGIN_SPIKE finalize without find_alternate_warehouse is rejected; second attempt accepted."""
    finalize_attempts = 0
    alternate_called = False
    turn = 0

    @service_handler(service=InventoryService)
    class TrackingInventory:
        @sync_operation
        async def lookupInventoryAddress(
            self, ctx: StartOperationContext, req: LookupInventoryAddressRequest
        ) -> LookupInventoryAddressResponse:
            return _LOOKUP_RESULT

        @sync_operation
        async def findAlternateWarehouse(
            self, ctx: StartOperationContext, req: FindAlternateWarehouseRequest
        ) -> FindAlternateWarehouseResponse:
            nonlocal alternate_called
            alternate_called = True
            return FindAlternateWarehouseResponse()

    @activity.defn(name="call_llm")
    async def enforced_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal finalize_attempts, turn
        turn += 1
        # Turn 1: try to finalize MARGIN_SPIKE without calling find_alternate_warehouse
        if turn == 1:
            finalize_attempts += 1
            return _finalize_response(_MARGIN_SPIKE_INPUT, tool_id="tu_rejected")
        # Turn 2: after receiving rejection, call find_alternate_warehouse
        if turn == 2:
            return _tool_use_response([
                ("tu_alt", "find_alternate_warehouse",
                 {"items": [{"sku_id": "ELEC-001", "quantity": 2}], "current_address_id": "adr_wh_east_01"}),
            ])
        # Turn 3: finalize accepted now that find_alternate_warehouse was called
        finalize_attempts += 1
        return _finalize_response(_MARGIN_SPIKE_INPUT, tool_id="tu_accepted")

    async with _test_env() as env:
        common = [mock_build_system_prompt, mock_verify_address, mock_get_carrier_rates,
                  mock_get_location_events, enforced_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, nexus_service_handlers=[TrackingInventory()],
                   workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-shipping", activities=common),
            Worker(env.client, task_queue="agents", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request(selected_paid_price=Money(currency="USD", units=1))
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.outcome == RecommendationOutcome.MARGIN_SPIKE
    assert alternate_called, "find_alternate_warehouse must have been called"
    assert finalize_attempts == 2, "first finalize rejected, second accepted"


@pytest.mark.asyncio
async def test_sla_breach_enforces_alternate_warehouse() -> None:
    """SLA_BREACH finalize without find_alternate_warehouse is rejected; second attempt accepted."""
    finalize_attempts = 0
    alternate_called = False
    turn = 0

    @service_handler(service=InventoryService)
    class TrackingInventory:
        @sync_operation
        async def lookupInventoryAddress(
            self, ctx: StartOperationContext, req: LookupInventoryAddressRequest
        ) -> LookupInventoryAddressResponse:
            return _LOOKUP_RESULT

        @sync_operation
        async def findAlternateWarehouse(
            self, ctx: StartOperationContext, req: FindAlternateWarehouseRequest
        ) -> FindAlternateWarehouseResponse:
            nonlocal alternate_called
            alternate_called = True
            return FindAlternateWarehouseResponse()

    @activity.defn(name="call_llm")
    async def enforced_sla_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal finalize_attempts, turn
        turn += 1
        if turn == 1:
            finalize_attempts += 1
            return _finalize_response(_SLA_BREACH_INPUT, tool_id="tu_rejected")
        if turn == 2:
            return _tool_use_response([
                ("tu_alt", "find_alternate_warehouse",
                 {"items": [{"sku_id": "ELEC-001", "quantity": 2}], "current_address_id": "adr_wh_east_01"}),
            ])
        finalize_attempts += 1
        return _finalize_response(_SLA_BREACH_INPUT, tool_id="tu_accepted")

    async with _test_env() as env:
        common = [mock_build_system_prompt, mock_verify_address, mock_get_carrier_rates,
                  mock_get_location_events, enforced_sla_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, nexus_service_handlers=[TrackingInventory()],
                   workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-shipping", activities=common),
            Worker(env.client, task_queue="agents", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request(selected_delivery_days=2)
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.outcome == RecommendationOutcome.SLA_BREACH
    assert alternate_called, "find_alternate_warehouse must have been called"
    assert finalize_attempts == 2, "first finalize rejected, second accepted"


@pytest.mark.asyncio
async def test_ttl_expiry_triggers_refetch() -> None:
    """After TTL expires, a subsequent Update re-invokes call_llm."""
    llm_call_count = 0

    @activity.defn(name="call_llm")
    async def counting_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal llm_call_count
        llm_call_count += 1
        return _finalize_response(_PROCEED_INPUT)

    # Use very short TTL (1 second) and time-skipping env to expire it
    short_ttl_start = StartShippingAgentRequest(
        customer_id=_CUSTOMER_ID,
        execution_options=ShippingAgentExecutionOptions(cache_ttl_secs=1),
    )

    async with _test_env() as env:
        workers = _make_workers(env.client, counting_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await env.client.start_workflow(
                ShippingAgent.run,
                short_ttl_start,
                id=f"{_CUSTOMER_ID}-ttl",
                task_queue=_WF_TASK_QUEUE,
                retry_policy=_WF_RETRY,
            )

            req = _base_request()

            # First call — cache miss, LLM called
            resp1 = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)
            assert resp1.cache_hit is False
            assert llm_call_count == 1

            # Skip time past TTL
            await env.sleep(timedelta(seconds=2))

            # Second call — TTL expired, LLM called again
            resp2 = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)
            assert resp2.cache_hit is False
            assert llm_call_count == 2
