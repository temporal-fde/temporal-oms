from __future__ import annotations

import re

import anthropic
from temporalio import activity

from src.config import settings
from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    BuildSystemPromptRequest,
    BuildSystemPromptResponse,
)
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

# _MODEL = "claude-sonnet-4-6"
_MODEL = "claude-haiku-4-5"

def _to_message_param(msg: LlmMessage) -> anthropic.types.MessageParam:
    content: list[anthropic.types.ContentBlockParam] = []
    for block in msg.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text.text})
        elif block.type == "tool_use":
            content.append({
                "type": "tool_use",
                "id": block.tool_use.id,
                "name": block.tool_use.name,
                "input": block.tool_use.input,
            })
        elif block.type == "tool_result":
            content.append({
                "type": "tool_result",
                "tool_use_id": block.tool_result.tool_use_id,
                "content": block.tool_result.content,
            })
    role = "user" if msg.role == LlmRole.LLM_ROLE_USER else "assistant"
    return {"role": role, "content": content}


def _to_tool_param(tool: LlmToolDefinition) -> anthropic.types.ToolParam:
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
    }


def _extract_text(text: str) -> str:
    match = re.search(r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    return match.group(1).strip() if match else text


def _to_llm_response(resp: anthropic.types.Message) -> LlmResponse:
    stop_reason = (
        LlmStopReason.LLM_STOP_REASON_TOOL_USE
        if resp.stop_reason == "tool_use"
        else LlmStopReason.LLM_STOP_REASON_END_TURN
    )
    blocks: list[LlmContentBlock] = []
    for block_obj in resp.content:
        if block_obj.type == "text":
            blocks.append(LlmContentBlock(
                type="text",
                text=LlmTextBlock(text=_extract_text(block_obj.text)),
            ))
        elif block_obj.type == "tool_use":
            blocks.append(LlmContentBlock(
                type="tool_use",
                tool_use=LlmToolUseBlock(
                    id=block_obj.id,
                    name=block_obj.name,
                    input=dict(block_obj.input),
                ),
            ))
    return LlmResponse(content=blocks, stop_reason=stop_reason)


class LlmActivities:
    """Temporal activity that calls the Anthropic Claude API.

    The workflow never imports from anthropic — all vendor types are converted
    here; the agentic loop works entirely with llm_p2p types.
    """

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
        )

    @activity.defn
    async def build_system_prompt(self, req: BuildSystemPromptRequest) -> BuildSystemPromptResponse:
        r = req.request
        margin_rule = (
            f"MARGIN RULE: If all available rate costs exceed the customer paid price "
            f"({r.customer_paid_price.units} {r.customer_paid_price.currency} "
            f"in minor currency units), outcome MUST be MARGIN_SPIKE; "
            f"set margin_delta_cents to the overage of the cheapest available rate."
            if (r.customer_paid_price and r.customer_paid_price.units > 0)
            else "MARGIN RULE: No customer paid price — skip margin spike logic."
        )

        sla_rule = (
            f"SLA RULE: If no rate delivers within {r.transit_days_sla} days, outcome MUST be SLA_BREACH."
            if (r.transit_days_sla and r.transit_days_sla > 0)
            else "SLA RULE: No transit SLA specified."
        )

        priority_rule = (
            "RULE PRIORITY: When multiple rules apply, resolve conflicts in this order:\n"
            "1. MARGIN_SPIKE — if all rates exceed the paid price, return MARGIN_SPIKE regardless of SLA or risk.\n"
            "2. SLA_BREACH — if no rate meets the SLA (and margin is not breached), return SLA_BREACH.\n"
            "3. RISK RULE — only applies when a rate technically meets the SLA but risk suggests it will fail."
        )

        risk_rule = (
            "RISK RULE: If get_location_events reveals severe disruptions (HIGH or CRITICAL risk) "
            "at the origin or destination that would delay transit, the original SLA is considered void. "
            "You MUST prioritize the cheapest available option (to protect margin) rather than buying "
            "a futile expedited label. Set the outcome to PROCEED and explain the risk-driven downgrade in reasoning."
        )

        prompt = "\n\n".join([
            "You are a shipping advisor for an e-commerce fulfillment system. All provided addresses are pre-verified as valid and deliverable.",
            margin_rule,
            sla_rule,
            priority_rule,
            risk_rule,
            (
                "PATH RULE: The origin and destination addresses are pre-resolved and provided in the task "
                "with their easypost_ids and coordinates. Use them directly for get_carrier_rates and "
                "get_location_events."
            ),
            (
                "CONCURRENCY: Call multiple tools in a single response when there are no dependencies "
                "between them (e.g. get_location_events for origin AND get_location_events for destination simultaneously)."
            ),
            (
                "RECOMMENDED ACTIONS:\n"
                "- If all carrier rates exceed the customer paid price, call find_alternate_warehouse "
                "before returning MARGIN_SPIKE. Only return MARGIN_SPIKE if no alternate warehouse "
                "exists or its rates also exceed the paid price.\n"
                "- If no rate meets the transit SLA, call find_alternate_warehouse before returning "
                "SLA_BREACH. A closer warehouse may offer faster options."
            ),
            (
                "LIMITATIONS:\n"
                "- If an address has no coordinates (latitude and longitude both absent or zero), "
                "skip get_location_events for that address entirely — do not attempt it."
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
        return BuildSystemPromptResponse(system_prompt=prompt)

    @activity.defn
    async def call_llm(
        self,
        messages: list[LlmMessage],
        tools: list[LlmToolDefinition],
    ) -> LlmResponse:
        message_params = [_to_message_param(m) for m in messages]
        tool_params = [_to_tool_param(t) for t in tools]

        resp = await self._client.messages.create(
            model=_MODEL,
            max_tokens=4096,
            thinking={"type": "disabled"},
            messages=message_params,
            tools=tool_params,
        )
        return _to_llm_response(resp)
