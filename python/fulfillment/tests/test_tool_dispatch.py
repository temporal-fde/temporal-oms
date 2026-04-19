"""Unit tests for agents.dispatch.tool_dispatch."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError
from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

from src.agents.dispatch import (
    ToolSpec,
    ToolSpecs,
    activity_name,
    activity_tool,
    child_workflow_tool,
    local_activity_tool,
    nexus_tool,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

class ReqModel(BaseModel):
    value: str


class ResultModel(BaseModel):
    result: str


def _make_block(name: str, inp: dict) -> MagicMock:
    block = MagicMock()
    block.tool_use.name = name
    block.tool_use.input = inp
    return block


# ─── activity_name ────────────────────────────────────────────────────────────

def test_activity_name_returns_registered_name() -> None:
    @activity.defn(name="my_registered_name")
    async def my_method(req: ReqModel) -> ResultModel:
        pass

    assert activity_name(my_method) == "my_registered_name"


def test_activity_name_falls_back_to_dunder_name() -> None:
    async def plain_function(req: ReqModel) -> ResultModel:
        pass

    assert activity_name(plain_function) == "plain_function"


# ─── activity_tool ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_activity_tool_dispatch_calls_execute_activity() -> None:
    """Dispatch calls execute_activity with exact method, result_type, and execute_kwargs — no extras."""
    timeout = timedelta(seconds=30)
    retry = RetryPolicy(maximum_attempts=3)
    method = MagicMock()
    expected = ResultModel(result="ok")

    with patch.object(workflow, "execute_activity", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = expected

        tool = activity_tool(
            name="my_activity",
            description="does stuff",
            method=method,
            req_type=ReqModel,
            result_type=ResultModel,
            task_queue="my-queue",
            start_to_close_timeout=timeout,
            retry_policy=retry,
        )
        req = ReqModel(value="hello")
        result = await tool.dispatch(req)

    mock_exec.assert_called_once_with(
        method,
        args=[req],
        result_type=ResultModel,
        task_queue="my-queue",
        start_to_close_timeout=timeout,
        retry_policy=retry,
    )
    assert result == expected


# ─── local_activity_tool ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_local_activity_tool_dispatch_calls_execute_local_activity() -> None:
    timeout = timedelta(seconds=10)
    retry = RetryPolicy(maximum_attempts=2)
    method = MagicMock()
    expected = ResultModel(result="local")

    with patch.object(workflow, "execute_local_activity", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = expected

        tool = local_activity_tool(
            name="my_local",
            description="fast local",
            method=method,
            req_type=ReqModel,
            result_type=ResultModel,
            start_to_close_timeout=timeout,
            retry_policy=retry,
        )
        req = ReqModel(value="local_val")
        result = await tool.dispatch(req)

    mock_exec.assert_called_once_with(
        method,
        args=[req],
        result_type=ResultModel,
        start_to_close_timeout=timeout,
        retry_policy=retry,
    )
    assert result == expected


# ─── nexus_tool ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nexus_tool_dispatch_raises_not_implemented() -> None:
    tool = nexus_tool(
        name="my_nexus",
        description="nexus op",
        endpoint="my-endpoint",
        operation=MagicMock(),
        req_type=ReqModel,
        result_type=ResultModel,
        schedule_to_close_timeout=timedelta(seconds=60),
    )

    with pytest.raises(NotImplementedError):
        await tool.dispatch(ReqModel(value="x"))


# ─── child_workflow_tool ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_child_workflow_tool_with_id_fn() -> None:
    wf_type = MagicMock()
    expected = ResultModel(result="child")

    with patch.object(workflow, "execute_child_workflow", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = expected

        tool = child_workflow_tool(
            name="my_child_wf",
            description="long running",
            workflow_type=wf_type,
            req_type=ReqModel,
            result_type=ResultModel,
            id_fn=lambda req: f"wf-{req.value}",
            task_queue="child-queue",
        )
        req = ReqModel(value="test")
        result = await tool.dispatch(req)

    mock_exec.assert_called_once_with(
        wf_type,
        args=[req],
        result_type=ResultModel,
        id="wf-test",
        task_queue="child-queue",
    )
    assert result == expected


@pytest.mark.asyncio
async def test_child_workflow_tool_without_id_fn() -> None:
    wf_type = MagicMock()

    with patch.object(workflow, "execute_child_workflow", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = ResultModel(result="child")

        tool = child_workflow_tool(
            name="my_child_wf",
            description="long running",
            workflow_type=wf_type,
            req_type=ReqModel,
            result_type=ResultModel,
            task_queue="child-queue",
        )
        req = ReqModel(value="test")
        await tool.dispatch(req)

    mock_exec.assert_called_once_with(
        wf_type,
        args=[req],
        result_type=ResultModel,
        id=None,
        task_queue="child-queue",
    )


@pytest.mark.asyncio
async def test_child_workflow_tool_execute_kwargs_forwarded() -> None:
    """All execute_kwargs supplied at builder time appear verbatim in the SDK call."""
    wf_type = MagicMock()
    exec_timeout = timedelta(hours=2)
    retry = RetryPolicy(maximum_attempts=5)

    with patch.object(workflow, "execute_child_workflow", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = ResultModel(result="ok")

        tool = child_workflow_tool(
            name="wf",
            description="d",
            workflow_type=wf_type,
            req_type=ReqModel,
            result_type=ResultModel,
            task_queue="q",
            execution_timeout=exec_timeout,
            retry_policy=retry,
        )
        await tool.dispatch(ReqModel(value="x"))

    _, kwargs = mock_exec.call_args
    assert kwargs["task_queue"] == "q"
    assert kwargs["execution_timeout"] == exec_timeout
    assert kwargs["retry_policy"] == retry
    assert kwargs["id"] is None
    assert kwargs["result_type"] is ResultModel


# ─── ToolSpecs ────────────────────────────────────────────────────────────────

def test_toolspecs_definitions_correct_name_description_schema() -> None:
    tool = activity_tool(
        name="my_tool",
        description="A test tool",
        method=MagicMock(),
        req_type=ReqModel,
        result_type=ResultModel,
        task_queue="q",
        start_to_close_timeout=timedelta(seconds=10),
    )
    specs = ToolSpecs(tool)
    defs = specs.definitions()

    assert len(defs) == 1
    assert defs[0].name == "my_tool"
    assert defs[0].description == "A test tool"
    assert defs[0].input_schema == ReqModel.model_json_schema()


@pytest.mark.asyncio
async def test_toolspecs_dispatch_happy_path() -> None:
    expected = ResultModel(result="dispatched")

    with patch.object(workflow, "execute_activity", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = expected

        tool = activity_tool(
            name="happy_tool",
            description="happy",
            method=MagicMock(),
            req_type=ReqModel,
            result_type=ResultModel,
            task_queue="q",
            start_to_close_timeout=timedelta(seconds=10),
        )
        specs = ToolSpecs(tool)
        block = _make_block("happy_tool", {"value": "hello"})
        result = await specs.dispatch(block)

    assert result == expected.model_dump_json()


@pytest.mark.asyncio
async def test_toolspecs_dispatch_unknown_name_raises_application_error() -> None:
    specs = ToolSpecs()
    block = _make_block("nonexistent_tool", {})

    with pytest.raises(ApplicationError) as exc_info:
        await specs.dispatch(block)

    assert exc_info.value.non_retryable is True
    assert "nonexistent_tool" in str(exc_info.value)


@pytest.mark.asyncio
async def test_toolspecs_dispatch_does_not_catch_validation_error() -> None:
    class StrictModel(BaseModel):
        required_int: int

    tool = activity_tool(
        name="strict_tool",
        description="strict",
        method=MagicMock(),
        req_type=StrictModel,
        result_type=ResultModel,
        task_queue="q",
        start_to_close_timeout=timedelta(seconds=10),
    )
    specs = ToolSpecs(tool)
    block = _make_block("strict_tool", {"required_int": "not_an_int"})

    with pytest.raises(ValidationError):
        await specs.dispatch(block)


def test_toolspecs_duplicate_name_raises() -> None:
    tool1 = ToolSpec(
        name="dup",
        description="first",
        req_type=ReqModel,
        dispatch=AsyncMock(),
    )
    tool2 = ToolSpec(
        name="dup",
        description="second",
        req_type=ReqModel,
        dispatch=AsyncMock(),
    )

    with pytest.raises(ValueError, match="dup"):
        ToolSpecs(tool1, tool2)
