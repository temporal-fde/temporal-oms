from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from pydantic import BaseModel
from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from acme.common.v1.llm_p2p import LlmContentBlock, LlmToolDefinition


@dataclass
class ToolSpec:
    name: str
    description: str
    req_type: type[BaseModel]
    dispatch: Callable[[BaseModel], Awaitable[BaseModel]]


class ToolSpecs:
    def __init__(self, *specs: ToolSpec) -> None:
        self._by_name: dict[str, ToolSpec] = {}
        for spec in specs:
            if spec.name in self._by_name:
                raise ValueError(f"Duplicate tool name: {spec.name!r}")
            self._by_name[spec.name] = spec

    def definitions(self) -> list[LlmToolDefinition]:
        return [
            LlmToolDefinition(
                name=spec.name,
                description=spec.description,
                input_schema=spec.req_type.model_json_schema(),
            )
            for spec in self._by_name.values()
        ]

    async def dispatch(self, block: LlmContentBlock) -> str:
        name = block.tool_use.name
        spec = self._by_name.get(name)
        if spec is None:
            raise ApplicationError(f"Unknown tool: {name!r}", non_retryable=True)
        req = spec.req_type(**block.tool_use.input)
        result = await spec.dispatch(req)
        return result.model_dump_json()


def activity_name(method: Any) -> str:
    defn = getattr(method, "__temporal_activity_definition", None)
    return defn.name if defn else method.__name__


def activity_tool(
    name: str,
    description: str,
    method: Any,
    req_type: type[BaseModel],
    result_type: type[BaseModel],
    **execute_kwargs: Any,
) -> ToolSpec:
    async def _dispatch(req: BaseModel) -> BaseModel:
        return await workflow.execute_activity(
            method,
            args=[req],
            result_type=result_type,
            **execute_kwargs,
        )

    return ToolSpec(name=name, description=description, req_type=req_type, dispatch=_dispatch)


def local_activity_tool(
    name: str,
    description: str,
    method: Any,
    req_type: type[BaseModel],
    result_type: type[BaseModel],
    **execute_kwargs: Any,
) -> ToolSpec:
    async def _dispatch(req: BaseModel) -> BaseModel:
        return await workflow.execute_local_activity(
            method,
            args=[req],
            result_type=result_type,
            **execute_kwargs,
        )

    return ToolSpec(name=name, description=description, req_type=req_type, dispatch=_dispatch)


def nexus_tool(
    name: str,
    description: str,
    endpoint: str,
    operation: Any,
    req_type: type[BaseModel],
    result_type: type[BaseModel],
    **execute_kwargs: Any,
) -> ToolSpec:
    async def _dispatch(req: BaseModel) -> BaseModel:
        raise NotImplementedError("nexus_tool not yet implemented")

    return ToolSpec(name=name, description=description, req_type=req_type, dispatch=_dispatch)


def child_workflow_tool(
    name: str,
    description: str,
    workflow_type: Any,
    req_type: type[BaseModel],
    result_type: type[BaseModel],
    id_fn: Optional[Callable[[BaseModel], str]] = None,
    **execute_kwargs: Any,
) -> ToolSpec:
    async def _dispatch(req: BaseModel) -> BaseModel:
        return await workflow.execute_child_workflow(
            workflow_type,
            args=[req],
            result_type=result_type,
            id=id_fn(req) if id_fn else None,
            **execute_kwargs,
        )

    return ToolSpec(name=name, description=description, req_type=req_type, dispatch=_dispatch)
