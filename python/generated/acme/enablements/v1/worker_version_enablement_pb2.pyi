import datetime

from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StartWorkerVersionEnablementRequest(_message.Message):
    __slots__ = ("enablement_id", "order_count", "submit_rate_per_min", "timeout")
    ENABLEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_COUNT_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_RATE_PER_MIN_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    enablement_id: str
    order_count: int
    submit_rate_per_min: int
    timeout: _duration_pb2.Duration
    def __init__(self, enablement_id: _Optional[str] = ..., order_count: _Optional[int] = ..., submit_rate_per_min: _Optional[int] = ..., timeout: _Optional[_Union[datetime.timedelta, _duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class WorkerVersionEnablementState(_message.Message):
    __slots__ = ("enablement_id", "args", "current_phase", "orders_submitted_count", "orders_per_minute", "active_versions", "last_transition_at")
    class DemoPhase(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DEMO_PHASE_UNSPECIFIED: _ClassVar[WorkerVersionEnablementState.DemoPhase]
        RUNNING_V1_ONLY: _ClassVar[WorkerVersionEnablementState.DemoPhase]
        TRANSITIONING_TO_V2: _ClassVar[WorkerVersionEnablementState.DemoPhase]
        RUNNING_BOTH: _ClassVar[WorkerVersionEnablementState.DemoPhase]
        COMPLETE: _ClassVar[WorkerVersionEnablementState.DemoPhase]
    DEMO_PHASE_UNSPECIFIED: WorkerVersionEnablementState.DemoPhase
    RUNNING_V1_ONLY: WorkerVersionEnablementState.DemoPhase
    TRANSITIONING_TO_V2: WorkerVersionEnablementState.DemoPhase
    RUNNING_BOTH: WorkerVersionEnablementState.DemoPhase
    COMPLETE: WorkerVersionEnablementState.DemoPhase
    ENABLEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PHASE_FIELD_NUMBER: _ClassVar[int]
    ORDERS_SUBMITTED_COUNT_FIELD_NUMBER: _ClassVar[int]
    ORDERS_PER_MINUTE_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_VERSIONS_FIELD_NUMBER: _ClassVar[int]
    LAST_TRANSITION_AT_FIELD_NUMBER: _ClassVar[int]
    enablement_id: str
    args: StartWorkerVersionEnablementRequest
    current_phase: WorkerVersionEnablementState.DemoPhase
    orders_submitted_count: int
    orders_per_minute: float
    active_versions: _containers.RepeatedScalarFieldContainer[str]
    last_transition_at: _timestamp_pb2.Timestamp
    def __init__(self, enablement_id: _Optional[str] = ..., args: _Optional[_Union[StartWorkerVersionEnablementRequest, _Mapping]] = ..., current_phase: _Optional[_Union[WorkerVersionEnablementState.DemoPhase, str]] = ..., orders_submitted_count: _Optional[int] = ..., orders_per_minute: _Optional[float] = ..., active_versions: _Optional[_Iterable[str]] = ..., last_transition_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class SubmitOrdersRequest(_message.Message):
    __slots__ = ("enablement_id", "submit_rate_per_min")
    ENABLEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_RATE_PER_MIN_FIELD_NUMBER: _ClassVar[int]
    enablement_id: str
    submit_rate_per_min: int
    def __init__(self, enablement_id: _Optional[str] = ..., submit_rate_per_min: _Optional[int] = ...) -> None: ...

class SubmitOrdersResponse(_message.Message):
    __slots__ = ("orders_submitted_count",)
    ORDERS_SUBMITTED_COUNT_FIELD_NUMBER: _ClassVar[int]
    orders_submitted_count: str
    def __init__(self, orders_submitted_count: _Optional[str] = ...) -> None: ...
