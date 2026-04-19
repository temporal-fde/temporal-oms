from __future__ import annotations

import os

import anthropic
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

_MODEL = "claude-sonnet-4-6"


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


def _to_llm_response(resp: anthropic.types.Message) -> LlmResponse:
    stop_reason = (
        LlmStopReason.LLM_STOP_REASON_TOOL_USE
        if resp.stop_reason == "tool_use"
        else LlmStopReason.LLM_STOP_REASON_END_TURN
    )
    blocks: list[LlmContentBlock] = []
    for block_obj in resp.content:
        block = LlmContentBlock(type=block_obj.type)
        if block_obj.type == "text":
            block.text = LlmTextBlock(text=block_obj.text)
        elif block_obj.type == "tool_use":
            block.tool_use = LlmToolUseBlock(
                id=block_obj.id,
                name=block_obj.name,
                input=dict(block_obj.input),
            )
        blocks.append(block)
    return LlmResponse(content=blocks, stop_reason=stop_reason)


class LlmActivities:
    """Temporal activity that calls the Anthropic Claude API.

    The workflow never imports from anthropic — all vendor types are converted
    here; the agentic loop works entirely with llm_p2p types.
    """

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )

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
            messages=message_params,
            tools=tool_params,
        )
        return _to_llm_response(resp)
