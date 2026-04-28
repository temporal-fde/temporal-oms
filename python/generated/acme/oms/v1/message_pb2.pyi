from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OmsProperties(_message.Message):
    __slots__ = ()
    class BoundedContextConfig(_message.Message):
        __slots__ = ()
        class NexusConfig(_message.Message):
            __slots__ = ()
            class EndpointsEntry(_message.Message):
                __slots__ = ()
                KEY_FIELD_NUMBER: _ClassVar[int]
                VALUE_FIELD_NUMBER: _ClassVar[int]
                key: str
                value: str
                def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
            ENDPOINTS_FIELD_NUMBER: _ClassVar[int]
            endpoints: _containers.ScalarMap[str, str]
            def __init__(self, endpoints: _Optional[_Mapping[str, str]] = ...) -> None: ...
        NEXUS_FIELD_NUMBER: _ClassVar[int]
        nexus: OmsProperties.BoundedContextConfig.NexusConfig
        def __init__(self, nexus: _Optional[_Union[OmsProperties.BoundedContextConfig.NexusConfig, _Mapping]] = ...) -> None: ...
    APPS_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_FIELD_NUMBER: _ClassVar[int]
    RISK_FIELD_NUMBER: _ClassVar[int]
    apps: OmsProperties.BoundedContextConfig
    processing: OmsProperties.BoundedContextConfig
    risk: OmsProperties.BoundedContextConfig
    def __init__(self, apps: _Optional[_Union[OmsProperties.BoundedContextConfig, _Mapping]] = ..., processing: _Optional[_Union[OmsProperties.BoundedContextConfig, _Mapping]] = ..., risk: _Optional[_Union[OmsProperties.BoundedContextConfig, _Mapping]] = ...) -> None: ...
