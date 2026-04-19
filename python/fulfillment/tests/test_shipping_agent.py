"""Unit tests for ShippingAgent workflow.

Uses Temporal Python test framework with mocked activities.
All tests run with retry_policy.maximum_attempts=1 and treat all exceptions as failures.
"""
from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
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
from acme.common.v1.values_p2p import Address, Coordinate, EasyPostAddress, Money
from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    CalculateShippingOptionsRequest,
    CalculateShippingOptionsResponse,
    GetLocationEventsRequest,
    GetLocationEventsResponse,
    GetShippingRatesRequest,
    GetShippingRatesResponse,
    LookupInventoryLocationRequest,
    LookupInventoryLocationResponse,
    RecommendationOutcome,
    ShippingAgentExecutionOptions,
    ShippingLineItem,
    ShippingOption,
    ShippingOptionsResult,
    ShippingRecommendation,
    StartShippingAgentRequest,
)
from acme.fulfillment.domain.v1.values_p2p import LocationRiskSummary, RiskLevel
from acme.fulfillment.domain.v1.workflows_p2p import (
    VerifyAddressRequest,
    VerifyAddressResponse,
)
from src.agents.workflows.shipping_agent import ShippingAgent

# ─── Constants ────────────────────────────────────────────────────────────────

_WF_TASK_QUEUE = "fulfillment"
_CUSTOMER_ID = "customer-test-1"
_ORDER_ID = "order-test-1"
_LOCATION_ID = "WH-EAST-01"

_TO_ADDRESS = Address(
    street="123 Main St",
    city="New York",
    state="NY",
    postal_code="10001",
    country="US",
    easypost_address=EasyPostAddress(
        id="adr_dest",
        residential=True,
        verified=True,
        coordinate=Coordinate(latitude=40.712, longitude=-74.006),
    ),
)

_FROM_ADDRESS = Address(
    street="100 Commerce Drive",
    city="Newark",
    state="NJ",
    postal_code="07102",
    country="US",
)

_ITEMS = [ShippingLineItem(sku_id="ELEC-001", quantity=2)]

_PROCEED_JSON = json.dumps({
    "outcome": "PROCEED",
    "recommended_option_id": "rate_001",
    "reasoning": "The selected rate is within budget and meets SLA.",
    "margin_delta_cents": -500,
    "origin_risk_level": "RISK_LEVEL_NONE",
    "destination_risk_level": "RISK_LEVEL_LOW",
})

_MARGIN_SPIKE_JSON = json.dumps({
    "outcome": "MARGIN_SPIKE",
    "recommended_option_id": "rate_002",
    "reasoning": "Original rate exceeds customer paid price.",
    "margin_delta_cents": 1500,
    "origin_risk_level": "RISK_LEVEL_NONE",
    "destination_risk_level": "RISK_LEVEL_NONE",
})

_SLA_BREACH_JSON = json.dumps({
    "outcome": "SLA_BREACH",
    "recommended_option_id": "",
    "reasoning": "No available rate meets the 2-day SLA.",
    "margin_delta_cents": 0,
    "origin_risk_level": "RISK_LEVEL_NONE",
    "destination_risk_level": "RISK_LEVEL_NONE",
})

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _end_turn_response(text: str) -> LlmResponse:
    return LlmResponse(
        content=[LlmContentBlock(type="text", text=LlmTextBlock(text=text))],
        stop_reason=LlmStopReason.LLM_STOP_REASON_END_TURN,
    )


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
    from_address: Address | None = None,
    location_id: str = "",
    customer_paid_price: Money | None = None,
    transit_days_sla: int = 0,
) -> CalculateShippingOptionsRequest:
    return CalculateShippingOptionsRequest(
        order_id=_ORDER_ID,
        customer_id=_CUSTOMER_ID,
        to_address=_TO_ADDRESS,
        items=_ITEMS,
        from_address=from_address,
        location_id=location_id,
        customer_paid_price=customer_paid_price,
        transit_days_sla=transit_days_sla,
    )


_START_REQUEST = StartShippingAgentRequest(
    customer_id=_CUSTOMER_ID,
    execution_options=ShippingAgentExecutionOptions(cache_ttl_secs=1800),
)

_WF_RETRY = RetryPolicy(maximum_attempts=1)


async def _start_agent(client: Client, wf_id: str = _CUSTOMER_ID) -> object:
    return await client.start_workflow(
        ShippingAgent.run,
        _START_REQUEST,
        id=wf_id,
        task_queue=_WF_TASK_QUEUE,
        retry_policy=_WF_RETRY,
    )


# ─── Mock activities ──────────────────────────────────────────────────────────

_LOOKUP_RESULT = LookupInventoryLocationResponse(
    location_id=_LOCATION_ID,
    address=_FROM_ADDRESS,
)

_VERIFY_RESULT = VerifyAddressResponse(
    address=Address(
        street=_FROM_ADDRESS.street,
        city=_FROM_ADDRESS.city,
        state=_FROM_ADDRESS.state,
        postal_code=_FROM_ADDRESS.postal_code,
        country=_FROM_ADDRESS.country,
        easypost_address=EasyPostAddress(
            id="adr_origin",
            residential=False,
            verified=True,
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


@activity.defn(name="lookup_inventory_location")
async def mock_lookup_inventory_location(
    req: LookupInventoryLocationRequest,
) -> LookupInventoryLocationResponse:
    return _LOOKUP_RESULT


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


def _make_workers(
    client: Client,
    call_llm_impl,
) -> list[Worker]:
    """Create one worker per task queue, all with the same mocked activities."""
    common_activities = [
        mock_lookup_inventory_location,
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
            workflow_failure_exception_types=[Exception],
        ),
        Worker(
            client,
            task_queue="fulfillment-easypost",
            activities=common_activities,
        ),
        Worker(
            client,
            task_queue="fulfillment-predicthq",
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
        return _end_turn_response(_PROCEED_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        workers = _make_workers(env.client, counting_call_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)

            req = _base_request(from_address=_FROM_ADDRESS, location_id=_LOCATION_ID)
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
async def test_fulfillment_path_skips_lookup() -> None:
    """When from_address and location_id are provided, lookup_inventory_location is never called."""
    lookup_called = False

    @activity.defn(name="lookup_inventory_location")
    async def tracking_lookup(req: LookupInventoryLocationRequest) -> LookupInventoryLocationResponse:
        nonlocal lookup_called
        lookup_called = True
        return _LOOKUP_RESULT

    @activity.defn(name="call_llm")
    async def simple_llm(messages: list, tools: list) -> LlmResponse:
        return _end_turn_response(_PROCEED_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        common = [tracking_lookup, mock_verify_address, mock_get_carrier_rates,
                  mock_get_location_events, simple_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-easypost", activities=common),
            Worker(env.client, task_queue="fulfillment-predicthq", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request(from_address=_FROM_ADDRESS, location_id=_LOCATION_ID)
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.cache_hit is False
    assert not lookup_called


@pytest.mark.asyncio
async def test_cart_path_calls_lookup() -> None:
    """When from_address is absent, LLM calls lookup_inventory_location first."""
    lookup_called = False
    turn = 0

    @activity.defn(name="lookup_inventory_location")
    async def tracking_lookup(req: LookupInventoryLocationRequest) -> LookupInventoryLocationResponse:
        nonlocal lookup_called
        lookup_called = True
        return _LOOKUP_RESULT

    @activity.defn(name="call_llm")
    async def cart_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            return _tool_use_response([
                ("tu_1", "lookup_inventory_location", {"items": [{"sku_id": "ELEC-001", "quantity": 2}]})
            ])
        return _end_turn_response(_PROCEED_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        common = [tracking_lookup, mock_verify_address, mock_get_carrier_rates,
                  mock_get_location_events, cart_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-easypost", activities=common),
            Worker(env.client, task_queue="fulfillment-predicthq", activities=common),
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

    @activity.defn(name="verify_address")
    async def tracking_verify(req: VerifyAddressRequest) -> VerifyAddressResponse:
        call_order.append("verify_address")
        return _VERIFY_RESULT

    @activity.defn(name="get_carrier_rates")
    async def tracking_rates(req: GetShippingRatesRequest) -> GetShippingRatesResponse:
        call_order.append("get_carrier_rates")
        return _RATES_RESULT

    @activity.defn(name="call_llm")
    async def sequential_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal turn
        turn += 1
        if turn == 1:
            return _tool_use_response([("tu_1", "verify_address", {"address": {}})])
        if turn == 2:
            return _tool_use_response([("tu_2", "get_carrier_rates",
                                        {"from_easypost_id": "adr_origin", "to_easypost_id": "adr_dest",
                                         "items": []})])
        return _end_turn_response(_PROCEED_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        common = [mock_lookup_inventory_location, tracking_verify, tracking_rates,
                  mock_get_location_events, sequential_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-easypost", activities=common),
            Worker(env.client, task_queue="fulfillment-predicthq", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request(from_address=_FROM_ADDRESS, location_id=_LOCATION_ID)
            await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert call_order == ["verify_address", "get_carrier_rates"]


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
        return _end_turn_response(_PROCEED_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        common = [mock_lookup_inventory_location, mock_verify_address, mock_get_carrier_rates,
                  tracking_events, concurrent_llm]
        async with (
            Worker(env.client, task_queue="fulfillment", workflows=[ShippingAgent],
                   activities=common, workflow_failure_exception_types=[Exception]),
            Worker(env.client, task_queue="fulfillment-easypost", activities=common),
            Worker(env.client, task_queue="fulfillment-predicthq", activities=common),
        ):
            handle = await _start_agent(env.client)
            req = _base_request(from_address=_FROM_ADDRESS, location_id=_LOCATION_ID)
            await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    # Both location event calls from the same LLM turn must have been dispatched
    assert events_call_count == 2


@pytest.mark.asyncio
async def test_proceed_outcome() -> None:
    @activity.defn(name="call_llm")
    async def proceed_llm(messages: list, tools: list) -> LlmResponse:
        return _end_turn_response(_PROCEED_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        workers = _make_workers(env.client, proceed_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)
            req = _base_request(from_address=_FROM_ADDRESS, location_id=_LOCATION_ID)
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.outcome == RecommendationOutcome.PROCEED


@pytest.mark.asyncio
async def test_margin_spike_outcome() -> None:
    @activity.defn(name="call_llm")
    async def margin_llm(messages: list, tools: list) -> LlmResponse:
        return _end_turn_response(_MARGIN_SPIKE_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        workers = _make_workers(env.client, margin_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)
            req = _base_request(
                from_address=_FROM_ADDRESS,
                location_id=_LOCATION_ID,
                customer_paid_price=Money(currency="USD", units=1000),
            )
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    assert resp.recommendation.outcome == RecommendationOutcome.MARGIN_SPIKE
    assert resp.recommendation.margin_delta_cents == 1500


@pytest.mark.asyncio
async def test_sla_breach_outcome() -> None:
    """SLA_BREACH is returned to caller — not raised as an exception."""
    @activity.defn(name="call_llm")
    async def sla_llm(messages: list, tools: list) -> LlmResponse:
        return _end_turn_response(_SLA_BREACH_JSON)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        workers = _make_workers(env.client, sla_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await _start_agent(env.client)
            req = _base_request(
                from_address=_FROM_ADDRESS,
                location_id=_LOCATION_ID,
                transit_days_sla=2,
            )
            resp = await handle.execute_update(ShippingAgent.calculate_shipping_options, req)

    # Returned as recommendation — fulfillment.Order decides what to do
    assert resp.recommendation.outcome == RecommendationOutcome.SLA_BREACH
    assert resp.cache_hit is False


@pytest.mark.asyncio
async def test_ttl_expiry_triggers_refetch() -> None:
    """After TTL expires, a subsequent Update re-invokes call_llm."""
    llm_call_count = 0

    @activity.defn(name="call_llm")
    async def counting_llm(messages: list, tools: list) -> LlmResponse:
        nonlocal llm_call_count
        llm_call_count += 1
        return _end_turn_response(_PROCEED_JSON)

    # Use very short TTL (1 second) and time-skipping env to expire it
    short_ttl_start = StartShippingAgentRequest(
        customer_id=_CUSTOMER_ID,
        execution_options=ShippingAgentExecutionOptions(cache_ttl_secs=1),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        workers = _make_workers(env.client, counting_llm)
        async with workers[0], workers[1], workers[2]:
            handle = await env.client.start_workflow(
                ShippingAgent.run,
                short_ttl_start,
                id=f"{_CUSTOMER_ID}-ttl",
                task_queue=_WF_TASK_QUEUE,
                retry_policy=_WF_RETRY,
            )

            req = _base_request(from_address=_FROM_ADDRESS, location_id=_LOCATION_ID)

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
