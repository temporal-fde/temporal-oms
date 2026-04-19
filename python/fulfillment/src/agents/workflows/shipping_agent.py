from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from acme.common.v1.llm_p2p import (
        LlmContentBlock,
        LlmMessage,
        LlmResponse,
        LlmRole,
        LlmStopReason,
        LlmTextBlock,
        LlmToolDefinition,
        LlmToolResultBlock,
    )
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
        ShippingLineItem,
        ShippingOption,
        ShippingOptionsCache,
        ShippingOptionsResult,
        ShippingRecommendation,
        StartShippingAgentRequest,
    )
    from acme.fulfillment.domain.v1.workflows_p2p import VerifyAddressRequest, VerifyAddressResponse
    from src.agents.activities.easypost import EasyPostActivities
    from src.agents.activities.inventory import LookupInventoryActivities
    from src.agents.activities.location_events import LocationEventsActivities

_DEFAULT_CACHE_TTL_SECS = 1800
_ACTIVITY_TIMEOUT = timedelta(seconds=30)
_LLM_TIMEOUT = timedelta(seconds=120)
_ACTIVITY_RETRY = RetryPolicy(maximum_attempts=3)


def _activity_name(method) -> str:
    """Return the Temporal-registered name for an @activity.defn class method.

    Reads __temporal_activity_definition set by the decorator so the name is
    always derived from the activity definition — renaming the method or
    changing the explicit name= kwarg propagates automatically.
    """
    defn = getattr(method, "__temporal_activity_definition", None)
    return defn.name if defn else method.__name__


# Dispatch table: registered activity name → (unbound method, request type, result type, task queue)
# Add new LLM tools here — the if/elif chain in _dispatch_tool and the tool definitions
# both derive from this single source of truth.
_TOOL_SPECS: dict[str, tuple] = {
    _activity_name(LookupInventoryActivities.lookup_inventory_location): (
        LookupInventoryActivities.lookup_inventory_location,
        LookupInventoryLocationRequest,
        LookupInventoryLocationResponse,
        "fulfillment",
    ),
    _activity_name(EasyPostActivities.verify_address): (
        EasyPostActivities.verify_address,
        VerifyAddressRequest,
        VerifyAddressResponse,
        "fulfillment-easypost",
    ),
    _activity_name(EasyPostActivities.get_carrier_rates): (
        EasyPostActivities.get_carrier_rates,
        GetShippingRatesRequest,
        GetShippingRatesResponse,
        "fulfillment-easypost",
    ),
    _activity_name(LocationEventsActivities.get_location_events): (
        LocationEventsActivities.get_location_events,
        GetLocationEventsRequest,
        GetLocationEventsResponse,
        "fulfillment-predicthq",
    ),
}


def _cache_key(
    easypost_address_id: str,
    items: list[ShippingLineItem],
    postal_code: str,
    country: str,
) -> str:
    sorted_items = sorted(
        [(item.sku_id, item.quantity) for item in items],
        key=lambda x: x[0],
    )
    raw = f"{easypost_address_id}:{sorted_items}:{postal_code}:{country}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _parse_recommendation(text: str) -> ShippingRecommendation:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        stripped = "\n".join(inner).strip()

    data = json.loads(stripped)
    outcome_str = data.get("outcome", "RECOMMENDATION_OUTCOME_UNSPECIFIED")
    try:
        outcome = RecommendationOutcome[outcome_str]
    except KeyError:
        raise ApplicationError(
            f"Invalid RecommendationOutcome from LLM: {outcome_str!r}",
            non_retryable=True,
        )

    return ShippingRecommendation(
        outcome=outcome,
        recommended_option_id=data.get("recommended_option_id", ""),
        reasoning=data.get("reasoning", ""),
        margin_delta_cents=int(data.get("margin_delta_cents", 0)),
    )


def _build_system_prompt(request: CalculateShippingOptionsRequest) -> str:
    margin_rule = (
        f"MARGIN RULE: If any available rate cost exceeds the customer paid price "
        f"({request.customer_paid_price.units} {request.customer_paid_price.currency} "
        f"in minor currency units), outcome MUST be MARGIN_SPIKE; "
        f"set margin_delta_cents to the overage."
        if (request.customer_paid_price and request.customer_paid_price.units > 0)
        else "MARGIN RULE: No customer paid price — skip margin spike logic."
    )

    sla_rule = (
        f"SLA RULE: If no rate delivers within {request.transit_days_sla} days, outcome MUST be SLA_BREACH."
        if (request.transit_days_sla and request.transit_days_sla > 0)
        else "SLA RULE: No transit SLA specified."
    )

    return "\n\n".join([
        "You are a shipping advisor for an e-commerce fulfillment system.",
        margin_rule,
        sla_rule,
        (
            "PATH RULE: Warehouse addresses are pre-verified — easypost_address.id is already set. "
            "If from_address is present in the request, use its easypost_address.id directly — "
            "do NOT call lookup_inventory_location or verify_address for the origin. "
            "If from_address is absent, call lookup_inventory_location first; the returned address "
            "will also have easypost_address.id pre-populated — skip verify_address. "
            "Only call verify_address for an address that explicitly lacks easypost_address."
        ),
        (
            "CONCURRENCY: Call multiple tools in a single response when there are no dependencies "
            "between them (e.g. verify_address for origin AND get_location_events for destination)."
        ),
        (
            "FINAL RESPONSE: When you have all data, respond with ONLY a JSON object:\n"
            '{"outcome":"<PROCEED|CHEAPER_AVAILABLE|FASTER_AVAILABLE|MARGIN_SPIKE|SLA_BREACH>",'
            '"recommended_option_id":"<id>","reasoning":"<text>",'
            '"margin_delta_cents":<int>,'
            '"origin_risk_level":"<RISK_LEVEL_NONE|RISK_LEVEL_LOW|RISK_LEVEL_MODERATE|RISK_LEVEL_HIGH|RISK_LEVEL_CRITICAL>",'
            '"destination_risk_level":"<RISK_LEVEL_NONE|RISK_LEVEL_LOW|RISK_LEVEL_MODERATE|RISK_LEVEL_HIGH|RISK_LEVEL_CRITICAL>"}'
        ),
    ])


# Resolved once at import time — used for tool-result post-processing in the agentic loop.
_NAME_LOOKUP = _activity_name(LookupInventoryActivities.lookup_inventory_location)
_NAME_RATES  = _activity_name(EasyPostActivities.get_carrier_rates)

# LLM-facing descriptions for each tool — keyed by the same activity name used in _TOOL_SPECS.
_TOOL_DESCRIPTIONS: dict[str, str] = {
    _activity_name(LookupInventoryActivities.lookup_inventory_location): (
        "Resolve sku_ids to a warehouse location and address. "
        "Call this first when from_address is not provided."
    ),
    _activity_name(EasyPostActivities.verify_address): (
        "Verify a raw shipping address via EasyPost. "
        "Returns an EasyPost address ID and lat/lng coordinates required for get_location_events."
    ),
    _activity_name(EasyPostActivities.get_carrier_rates): (
        "Create an EasyPost shipment and retrieve available carrier rates."
    ),
    _activity_name(LocationEventsActivities.get_location_events): (
        "Query PredictHQ for supply chain risk events near a coordinate "
        "(severe weather, disasters, airport delays, etc.) within the ship-to-delivery window. "
        "Call for BOTH origin and destination to get full risk context."
    ),
}


def _build_tool_definitions() -> list[LlmToolDefinition]:
    return [
        LlmToolDefinition(
            name=name,
            description=_TOOL_DESCRIPTIONS[name],
            input_schema=req_type.model_json_schema(),
        )
        for name, (_, req_type, _, _) in _TOOL_SPECS.items()
    ]


async def _dispatch_tool(block: LlmContentBlock) -> str:
    """Dispatch a single tool_use block to its Temporal activity and return JSON result.

    Tool name → activity method, request/result types, and task queue all come from
    _TOOL_SPECS — derived from @activity.defn metadata, not hardcoded strings.
    """
    name = block.tool_use.name
    spec = _TOOL_SPECS.get(name)
    if spec is None:
        raise ApplicationError(f"Unknown tool: {name!r}", non_retryable=True)

    method, req_type, result_type, task_queue = spec
    req = req_type(**block.tool_use.input)
    result = await workflow.execute_activity(
        method,
        args=[req],
        result_type=result_type,
        task_queue=task_queue,
        start_to_close_timeout=_ACTIVITY_TIMEOUT,
        retry_policy=_ACTIVITY_RETRY,
    )
    return result.model_dump_json()


@workflow.defn(name="ShippingAgent")
class ShippingAgent:
    """Long-running per-customer shipping advisor workflow.

    WorkflowID: customer_id
    Caches shipping rate calculations by content hash with a configurable TTL.
    """

    def __init__(self) -> None:
        self._cache: dict[str, ShippingOptionsResult] = {}
        self._cache_meta: dict[str, datetime] = {}
        self._cache_ttl_secs: int = _DEFAULT_CACHE_TTL_SECS

    @workflow.run
    async def run(self, request: StartShippingAgentRequest) -> None:
        if request.execution_options and request.execution_options.cache_ttl_secs:
            self._cache_ttl_secs = int(request.execution_options.cache_ttl_secs)
        # Long-running agent: never exits on its own
        await workflow.wait_condition(lambda: False)

    @workflow.query
    def get_options(self) -> ShippingOptionsCache:
        return ShippingOptionsCache(results=dict(self._cache))

    @workflow.update
    async def calculate_shipping_options(
        self, request: CalculateShippingOptionsRequest
    ) -> CalculateShippingOptionsResponse:
        # Fulfillment path early cache check — from_address with easypost_address.id present
        from_ep_id = (
            request.from_address.easypost_address.id
            if (request.from_address and request.from_address.easypost_address)
            else ""
        )
        if from_ep_id:
            key = _cache_key(
                from_ep_id,
                list(request.items),
                request.to_address.postal_code,
                request.to_address.country,
            )
            if self._is_cache_valid(key):
                cached = self._cache[key]
                return CalculateShippingOptionsResponse(
                    recommendation=cached.recommendation,
                    options=list(cached.options),
                    cache_hit=True,
                )

        system_prompt = _build_system_prompt(request)
        tools = _build_tool_definitions()

        # Initial user message
        has_from = bool(request.from_address and request.from_address.street)
        from_desc = (
            f"{request.from_address.street}, {request.from_address.city}, "
            f"{request.from_address.state} {request.from_address.postal_code} {request.from_address.country}"
            if has_from
            else "NOT PROVIDED — call lookup_inventory_location first"
        )
        items_desc = ", ".join(f"{i.sku_id}×{i.quantity}" for i in request.items)
        ep_note = (
            f"\nto_address easypost_id (already verified): {request.to_address.easypost_address.id}"
            if (request.to_address.easypost_address and request.to_address.easypost_address.id)
            else ""
        )
        task_text = (
            f"Calculate shipping options for order {request.order_id}.\n"
            f"to_address: {request.to_address.street}, {request.to_address.city}, "
            f"{request.to_address.state} {request.to_address.postal_code} {request.to_address.country}"
            f"{ep_note}\n"
            f"from_address: {from_desc}\n"
            f"items: {items_desc}\n"
        )
        # System instructions are embedded in the first user message (call_llm has no system param)
        user_text = system_prompt + "\n\n---\n\n" + task_text

        messages: list[LlmMessage] = [
            LlmMessage(
                role=LlmRole.LLM_ROLE_USER,
                content=[LlmContentBlock(type="text", text=LlmTextBlock(text=user_text))],
            )
        ]

        resolved_ep_id: str = from_ep_id  # populated from cart path lookup_inventory_location result
        all_options: list[ShippingOption] = []
        recommendation: ShippingRecommendation | None = None

        while True:
            llm_response: LlmResponse = await workflow.execute_activity(
                "call_llm",
                args=[messages, tools],
                result_type=LlmResponse,
                task_queue="fulfillment",
                start_to_close_timeout=_LLM_TIMEOUT,
                retry_policy=_ACTIVITY_RETRY,
            )

            messages.append(LlmMessage(
                role=LlmRole.LLM_ROLE_ASSISTANT,
                content=list(llm_response.content),
            ))

            if llm_response.stop_reason == LlmStopReason.LLM_STOP_REASON_END_TURN:
                for block in llm_response.content:
                    if block.type == "text":
                        recommendation = _parse_recommendation(block.text.text)
                        break
                break

            if llm_response.stop_reason == LlmStopReason.LLM_STOP_REASON_TOOL_USE:
                tool_blocks = [b for b in llm_response.content if b.type == "tool_use"]

                # Dispatch all tool calls in this batch concurrently
                tool_results: list[str] = list(await asyncio.gather(
                    *[_dispatch_tool(b) for b in tool_blocks]
                ))

                # Extract easypost_address.id from lookup_inventory_location (cart path)
                # and options from get_carrier_rates for cache storage.
                for block, result_json in zip(tool_blocks, tool_results):
                    if block.tool_use.name == _NAME_LOOKUP and not resolved_ep_id:
                        try:
                            data = json.loads(result_json)
                            ep = (data.get("address") or {}).get("easypost_address") or {}
                            resolved_ep_id = ep.get("id", "")
                        except json.JSONDecodeError:
                            pass
                    if block.tool_use.name == _NAME_RATES:
                        try:
                            data = json.loads(result_json)
                            all_options = [ShippingOption(**o) for o in data.get("options", [])]
                        except Exception:
                            pass

                # Cart path post-location cache check (once easypost_address.id is resolved)
                if resolved_ep_id and not from_ep_id:
                    key = _cache_key(
                        resolved_ep_id,
                        list(request.items),
                        request.to_address.postal_code,
                        request.to_address.country,
                    )
                    if self._is_cache_valid(key):
                        cached = self._cache[key]
                        return CalculateShippingOptionsResponse(
                            recommendation=cached.recommendation,
                            options=list(cached.options),
                            cache_hit=True,
                        )

                messages.append(LlmMessage(
                    role=LlmRole.LLM_ROLE_USER,
                    content=[
                        LlmContentBlock(
                            type="tool_result",
                            tool_result=LlmToolResultBlock(
                                tool_use_id=b.tool_use.id,
                                content=r,
                            ),
                        )
                        for b, r in zip(tool_blocks, tool_results)
                    ],
                ))

        if recommendation is None:
            raise ApplicationError("LLM did not produce a recommendation", non_retryable=False)

        final_key = _cache_key(
            resolved_ep_id or "unknown",
            list(request.items),
            request.to_address.postal_code,
            request.to_address.country,
        )
        now = workflow.now()
        self._cache[final_key] = ShippingOptionsResult(
            recommendation=recommendation,
            options=all_options,
            cached_at=now,
        )
        self._cache_meta[final_key] = now

        return CalculateShippingOptionsResponse(
            recommendation=recommendation,
            options=all_options,
            cache_hit=False,
        )

    @calculate_shipping_options.validator
    def validate_calculate_shipping_options(
        self, request: CalculateShippingOptionsRequest
    ) -> None:
        if not request.order_id:
            raise ValueError("order_id is required")
        if not request.customer_id:
            raise ValueError("customer_id is required")
        if not request.to_address:
            raise ValueError("to_address is required")
        if not request.items:
            raise ValueError("at least one item is required")

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache_meta:
            return False
        return workflow.now() - self._cache_meta[key] <= timedelta(seconds=self._cache_ttl_secs)
