from __future__ import annotations

import asyncio
import json
from datetime import timedelta

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
        LlmToolResultBlock,
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
        LookupInventoryLocationRequest,
        LookupInventoryLocationResponse,
        RecommendationOutcome,
        ShippingOption,
        ShippingRecommendation,
        StartShippingAgentRequest,
    )
    from acme.fulfillment.domain.v1.workflows_p2p import VerifyAddressRequest, VerifyAddressResponse
    from src.agents.activities.easypost import EasyPostActivities
    from src.agents.activities.inventory import LookupInventoryActivities
    from src.agents.activities.llm import LlmActivities
    from src.agents.activities.location_events import LocationEventsActivities
    from src.agents.dispatch import activity_name, activity_tool, ToolSpecs

_ACTIVITY_TIMEOUT = timedelta(seconds=30)
_LLM_TIMEOUT = timedelta(seconds=120)
_ACTIVITY_RETRY = RetryPolicy(maximum_attempts=3)


_TOOLS = ToolSpecs(
    activity_tool(
        activity_name(LookupInventoryActivities.lookup_inventory_location),
        "Resolve sku_ids to a warehouse location and address. "
        "Call this first when from_address is not provided.",
        LookupInventoryActivities.lookup_inventory_location,
        LookupInventoryLocationRequest,
        LookupInventoryLocationResponse,
        task_queue="fulfillment",
        start_to_close_timeout=_ACTIVITY_TIMEOUT,
        retry_policy=_ACTIVITY_RETRY,
    ),
    activity_tool(
        activity_name(EasyPostActivities.verify_address),
        "Verify a raw shipping address via EasyPost. "
        "Returns an EasyPost address ID and lat/lng coordinates required for get_location_events.",
        EasyPostActivities.verify_address,
        VerifyAddressRequest,
        VerifyAddressResponse,
        task_queue="fulfillment-easypost",
        start_to_close_timeout=_ACTIVITY_TIMEOUT,
        retry_policy=_ACTIVITY_RETRY,
    ),
    activity_tool(
        activity_name(EasyPostActivities.get_carrier_rates),
        "Create an EasyPost shipment and retrieve available carrier rates.",
        EasyPostActivities.get_carrier_rates,
        GetShippingRatesRequest,
        GetShippingRatesResponse,
        task_queue="fulfillment-easypost",
        start_to_close_timeout=_ACTIVITY_TIMEOUT,
        retry_policy=_ACTIVITY_RETRY,
    ),
    activity_tool(
        activity_name(LocationEventsActivities.get_location_events),
        "Query PredictHQ for supply chain risk events near a coordinate "
        "(severe weather, disasters, airport delays, etc.) within the ship-to-delivery window. "
        "Call for BOTH origin and destination to get full risk context.",
        LocationEventsActivities.get_location_events,
        GetLocationEventsRequest,
        GetLocationEventsResponse,
        task_queue="fulfillment-predicthq",
        start_to_close_timeout=_ACTIVITY_TIMEOUT,
        retry_policy=_ACTIVITY_RETRY,
    ),
)


def _parse_recommendation(text: str) -> ShippingRecommendation:
    data = json.loads(text)
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



_NAME_LOOKUP = activity_name(LookupInventoryActivities.lookup_inventory_location)
_NAME_RATES  = activity_name(EasyPostActivities.get_carrier_rates)


@workflow.defn(name="ShippingAgent")
class ShippingAgent:
    """Long-running per-customer shipping advisor workflow.

    WorkflowID: customer_id
    """

    @workflow.run
    async def run(self, request: StartShippingAgentRequest) -> None:
        await workflow.wait_condition(lambda: False)

    @workflow.update
    async def calculate_shipping_options(
        self, request: CalculateShippingOptionsRequest
    ) -> CalculateShippingOptionsResponse:
        return await self._run_react_loop(request)

    async def _run_react_loop(
        self,
        request: CalculateShippingOptionsRequest,
    ) -> CalculateShippingOptionsResponse:
        prompt_response: BuildSystemPromptResponse = await workflow.execute_local_activity(
            LlmActivities.build_system_prompt,
            BuildSystemPromptRequest(request=request),
            result_type=BuildSystemPromptResponse,
            start_to_close_timeout=timedelta(seconds=5),
        )
        system_prompt = prompt_response.system_prompt
        tools = _TOOLS.definitions()

        # Pre-fetch origin and destination in parallel before the LLM loop.
        # Results are embedded directly in the task prompt so the LLM can call
        # get_carrier_rates + get_location_events concurrently on its first turn.
        to_ep = request.to_address.easypost if request.to_address else None
        needs_verify = not (to_ep and to_ep.id)

        if needs_verify:
            lookup_result, verify_result = await asyncio.gather(
                workflow.execute_activity(
                    "lookup_inventory_location",
                    args=[LookupInventoryLocationRequest(items=request.items)],
                    result_type=LookupInventoryLocationResponse,
                    task_queue="fulfillment",
                    start_to_close_timeout=_ACTIVITY_TIMEOUT,
                    retry_policy=_ACTIVITY_RETRY,
                ),
                workflow.execute_activity(
                    "verify_address",
                    args=[VerifyAddressRequest(address=request.to_address)],
                    result_type=VerifyAddressResponse,
                    task_queue="fulfillment-easypost",
                    start_to_close_timeout=_ACTIVITY_TIMEOUT,
                    retry_policy=_ACTIVITY_RETRY,
                ),
            )
            dest_ep = verify_result.address.easypost
        else:
            lookup_result = await workflow.execute_activity(
                "lookup_inventory_location",
                args=[LookupInventoryLocationRequest(items=request.items)],
                result_type=LookupInventoryLocationResponse,
                task_queue="fulfillment",
                start_to_close_timeout=_ACTIVITY_TIMEOUT,
                retry_policy=_ACTIVITY_RETRY,
            )
            dest_ep = to_ep

        origin_ep = lookup_result.address.easypost if lookup_result.address else None

        def _addr_line(ep) -> str:
            if not ep:
                return "(unknown)"
            coord = (
                f"  lat={ep.coordinate.latitude} lng={ep.coordinate.longitude}"
                if (ep.coordinate and (ep.coordinate.latitude or ep.coordinate.longitude))
                else ""
            )
            ep_id = ep.id if ep.id else "(unverified — call verify_address if needed)"
            return f"{ep.street1}, {ep.city}, {ep.state} {ep.zip}  easypost_id={ep_id}{coord}"

        items_desc = ", ".join(f"{i.sku_id}×{i.quantity}" for i in request.items)
        task_text = (
            f"Calculate shipping options for order {request.order_id}.\n"
            f"destination: {_addr_line(dest_ep)}\n"
            f"origin (resolved from inventory): {_addr_line(origin_ep)}\n"
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

        recommendation: ShippingRecommendation | None = None
        all_options: list[ShippingOption] = []

        while True:
            # ReAct: Reason — LLM evaluates state and decides next action (tool calls or final answer)
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

                # ReAct: Act — dispatch tool calls concurrently, block until all resolve
                tool_results: list[str] = list(await asyncio.gather(
                    *[_TOOLS.dispatch(b) for b in tool_blocks]
                ))

                for block, result_json in zip(tool_blocks, tool_results):
                    if block.tool_use.name == _NAME_RATES:
                        try:
                            data = json.loads(result_json)
                            all_options = [ShippingOption(**o) for o in data.get("options", [])]
                        except Exception:
                            pass

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
