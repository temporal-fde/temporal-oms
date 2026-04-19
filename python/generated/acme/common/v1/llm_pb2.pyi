from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LlmRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LLM_ROLE_UNSPECIFIED: _ClassVar[LlmRole]
    LLM_ROLE_USER: _ClassVar[LlmRole]
    LLM_ROLE_ASSISTANT: _ClassVar[LlmRole]

class LlmStopReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LLM_STOP_REASON_UNSPECIFIED: _ClassVar[LlmStopReason]
    LLM_STOP_REASON_END_TURN: _ClassVar[LlmStopReason]
    LLM_STOP_REASON_TOOL_USE: _ClassVar[LlmStopReason]
LLM_ROLE_UNSPECIFIED: LlmRole
LLM_ROLE_USER: LlmRole
LLM_ROLE_ASSISTANT: LlmRole
LLM_STOP_REASON_UNSPECIFIED: LlmStopReason
LLM_STOP_REASON_END_TURN: LlmStopReason
LLM_STOP_REASON_TOOL_USE: LlmStopReason

class LlmTextBlock(_message.Message):
    __slots__ = ("text",)
    TEXT_FIELD_NUMBER: _ClassVar[int]
    text: str
    def __init__(self, text: _Optional[str] = ...) -> None: ...

class LlmToolUseBlock(_message.Message):
    __slots__ = ("id", "name", "input")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    input: _struct_pb2.Struct
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., input: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class LlmToolResultBlock(_message.Message):
    __slots__ = ("tool_use_id", "content")
    TOOL_USE_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    tool_use_id: str
    content: str
    def __init__(self, tool_use_id: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class LlmContentBlock(_message.Message):
    __slots__ = ("type", "text", "tool_use", "tool_result")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TOOL_USE_FIELD_NUMBER: _ClassVar[int]
    TOOL_RESULT_FIELD_NUMBER: _ClassVar[int]
    type: str
    text: LlmTextBlock
    tool_use: LlmToolUseBlock
    tool_result: LlmToolResultBlock
    def __init__(self, type: _Optional[str] = ..., text: _Optional[_Union[LlmTextBlock, _Mapping]] = ..., tool_use: _Optional[_Union[LlmToolUseBlock, _Mapping]] = ..., tool_result: _Optional[_Union[LlmToolResultBlock, _Mapping]] = ...) -> None: ...

class LlmMessage(_message.Message):
    __slots__ = ("role", "content")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    role: LlmRole
    content: _containers.RepeatedCompositeFieldContainer[LlmContentBlock]
    def __init__(self, role: _Optional[_Union[LlmRole, str]] = ..., content: _Optional[_Iterable[_Union[LlmContentBlock, _Mapping]]] = ...) -> None: ...

class LlmResponse(_message.Message):
    __slots__ = ("content", "stop_reason")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    STOP_REASON_FIELD_NUMBER: _ClassVar[int]
    content: _containers.RepeatedCompositeFieldContainer[LlmContentBlock]
    stop_reason: LlmStopReason
    def __init__(self, content: _Optional[_Iterable[_Union[LlmContentBlock, _Mapping]]] = ..., stop_reason: _Optional[_Union[LlmStopReason, str]] = ...) -> None: ...

class LlmToolDefinition(_message.Message):
    __slots__ = ("name", "description", "input_schema")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    INPUT_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    input_schema: _struct_pb2.Struct
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., input_schema: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
