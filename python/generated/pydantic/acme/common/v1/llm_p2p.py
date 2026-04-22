# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class LlmRole(IntEnum):
    """
     LlmRole identifies the author of a conversation message.
    """
    LLM_ROLE_UNSPECIFIED = 0
    LLM_ROLE_USER = 1
    LLM_ROLE_ASSISTANT = 2


class LlmStopReason(IntEnum):
    """
     LlmStopReason indicates why the model stopped generating.
    """
    LLM_STOP_REASON_UNSPECIFIED = 0
    LLM_STOP_REASON_END_TURN = 1
    LLM_STOP_REASON_TOOL_USE = 2

class LlmTextBlock(BaseModel):
    """
     LlmTextBlock carries a plain text response from the model.
    """

    text: str = Field(default="")

class LlmToolUseBlock(BaseModel):
    """
     LlmToolUseBlock carries a single tool call issued by the model.
 input uses google.protobuf.Struct so Pydantic generates Dict[str, Any].
    """

    id: str = Field(default="")
    name: str = Field(default="")
    input: typing.Dict[str, typing.Any] = Field(default_factory=dict)

class LlmToolResultBlock(BaseModel):
    """
     LlmToolResultBlock carries the result of a tool call back to the model.
    """

    tool_use_id: str = Field(default="")
    content: str = Field(default="")

class LlmContentBlock(BaseModel):
    """
     LlmContentBlock is a discriminated union of the three block types.

 type is a string discriminator set explicitly by call_llm ("text" | "tool_use" | "tool_result").
 No oneof is used: protobuf-to-pydantic v0.3.3.1 assigns default_factory to every message
 field inside a oneof, making all fields non-None — field-presence checks are unusable.
 The agentic loop reads block.type to determine which nested field to access.
    """

    type: str = Field(default="")# "text" | "tool_use" | "tool_result"
    text: LlmTextBlock = Field(default_factory=LlmTextBlock)
    tool_use: LlmToolUseBlock = Field(default_factory=LlmToolUseBlock)
    tool_result: LlmToolResultBlock = Field(default_factory=LlmToolResultBlock)

class LlmMessage(BaseModel):
    """
     LlmMessage is a single turn in a conversation.
    """

    model_config = ConfigDict(validate_default=True)
    role: LlmRole = Field(default=0)
    content: typing.List[LlmContentBlock] = Field(default_factory=list)

class LlmResponse(BaseModel):
    """
     LlmResponse is the model's reply to a messages list.
    """

    model_config = ConfigDict(validate_default=True)
    content: typing.List[LlmContentBlock] = Field(default_factory=list)
    stop_reason: LlmStopReason = Field(default=0)

class LlmToolDefinition(BaseModel):
    """
     LlmToolDefinition describes a tool the model may call.
 input_schema uses google.protobuf.Struct so Pydantic generates Dict[str, Any].
    """

    name: str = Field(default="")
    description: str = Field(default="")
    input_schema: typing.Dict[str, typing.Any] = Field(default_factory=dict)
