from __future__ import annotations

from types import SimpleNamespace

import pytest

from acme.common.v1.llm_p2p import (
    LlmContentBlock,
    LlmMessage,
    LlmRole,
    LlmStopReason,
    LlmTextBlock,
    LlmToolDefinition,
    LlmToolResultBlock,
    LlmToolUseBlock,
)
from src.agents.activities import llm


def test_openai_message_params_preserve_tool_call_contract() -> None:
    messages = [
        LlmMessage(
            role=LlmRole.LLM_ROLE_USER,
            content=[LlmContentBlock(type="text", text=LlmTextBlock(text="recommend"))],
        ),
        LlmMessage(
            role=LlmRole.LLM_ROLE_ASSISTANT,
            content=[
                LlmContentBlock(
                    type="tool_use",
                    tool_use=LlmToolUseBlock(
                        id="call_1",
                        name="get_carrier_rates",
                        input={"from_easypost_id": "adr_from"},
                    ),
                ),
                LlmContentBlock(
                    type="tool_use",
                    tool_use=LlmToolUseBlock(
                        id="call_2",
                        name="get_location_events",
                        input={"within_km": 50.0},
                    ),
                ),
            ],
        ),
        LlmMessage(
            role=LlmRole.LLM_ROLE_USER,
            content=[
                LlmContentBlock(
                    type="tool_result",
                    tool_result=LlmToolResultBlock(
                        tool_use_id="call_1",
                        content='{"options": []}',
                    ),
                ),
                LlmContentBlock(
                    type="tool_result",
                    tool_result=LlmToolResultBlock(
                        tool_use_id="call_2",
                        content='{"events": []}',
                    ),
                ),
            ],
        ),
    ]

    params = llm._to_openai_message_params(messages)

    assert params == [
        {"role": "user", "content": "recommend"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_carrier_rates",
                        "arguments": '{"from_easypost_id": "adr_from"}',
                    },
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {
                        "name": "get_location_events",
                        "arguments": '{"within_km": 50.0}',
                    },
                },
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": '{"options": []}',
        },
        {
            "role": "tool",
            "tool_call_id": "call_2",
            "content": '{"events": []}',
        },
    ]


def test_openai_tool_param_uses_existing_schema() -> None:
    tool = LlmToolDefinition(
        name="finalize_recommendation",
        description="Submit final answer",
        input_schema={
            "type": "object",
            "properties": {"outcome": {"type": "string"}},
            "required": ["outcome"],
        },
    )

    assert llm._to_openai_tool_param(tool) == {
        "type": "function",
        "function": {
            "name": "finalize_recommendation",
            "description": "Submit final answer",
            "parameters": tool.input_schema,
        },
    }


def test_openai_llm_response_maps_tool_calls_to_internal_response() -> None:
    resp = SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="tool_calls",
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[
                        SimpleNamespace(
                            id="call_1",
                            type="function",
                            function=SimpleNamespace(
                                name="finalize_recommendation",
                                arguments='{"outcome": "PROCEED"}',
                            ),
                        )
                    ],
                ),
            )
        ]
    )

    result = llm._to_openai_llm_response(resp)

    assert result.stop_reason == LlmStopReason.LLM_STOP_REASON_TOOL_USE
    assert len(result.content) == 1
    block = result.content[0]
    assert block.type == "tool_use"
    assert block.tool_use.id == "call_1"
    assert block.tool_use.name == "finalize_recommendation"
    assert block.tool_use.input == {"outcome": "PROCEED"}


def test_llm_activities_selects_openai_client(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, str] = {}

    class FakeOpenAILlmClient:
        def __init__(self, *, api_key: str, model: str) -> None:
            created["api_key"] = api_key
            created["model"] = model

    monkeypatch.setattr(llm, "_OpenAILlmClient", FakeOpenAILlmClient)
    monkeypatch.setattr(llm.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(llm.settings, "openai_model", "gpt-test")

    activities = llm.LlmActivities(provider="openai")

    assert isinstance(activities._llm_client, FakeOpenAILlmClient)
    assert created == {"api_key": "sk-test", "model": "gpt-test"}


def test_llm_activities_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported llm_provider"):
        llm.LlmActivities(provider="watson")
