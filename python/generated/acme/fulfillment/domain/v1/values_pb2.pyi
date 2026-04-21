import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Errors(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ERROR_UNSPECIFIED: _ClassVar[Errors]
    ERROR_UNAUTHORIZED: _ClassVar[Errors]
    ERROR_FORBIDDEN: _ClassVar[Errors]
    ERROR_BAD_REQUEST: _ClassVar[Errors]
    ERROR_ADDRESS_VERIFY_FAILED: _ClassVar[Errors]

class RiskLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RISK_LEVEL_UNSPECIFIED: _ClassVar[RiskLevel]
    RISK_LEVEL_NONE: _ClassVar[RiskLevel]
    RISK_LEVEL_LOW: _ClassVar[RiskLevel]
    RISK_LEVEL_MODERATE: _ClassVar[RiskLevel]
    RISK_LEVEL_HIGH: _ClassVar[RiskLevel]
    RISK_LEVEL_CRITICAL: _ClassVar[RiskLevel]
ERROR_UNSPECIFIED: Errors
ERROR_UNAUTHORIZED: Errors
ERROR_FORBIDDEN: Errors
ERROR_BAD_REQUEST: Errors
ERROR_ADDRESS_VERIFY_FAILED: Errors
RISK_LEVEL_UNSPECIFIED: RiskLevel
RISK_LEVEL_NONE: RiskLevel
RISK_LEVEL_LOW: RiskLevel
RISK_LEVEL_MODERATE: RiskLevel
RISK_LEVEL_HIGH: RiskLevel
RISK_LEVEL_CRITICAL: RiskLevel

class LocationEvent(_message.Message):
    __slots__ = ("id", "title", "description", "category", "rank", "local_rank", "unscheduled", "start", "end")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    LOCAL_RANK_FIELD_NUMBER: _ClassVar[int]
    UNSCHEDULED_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    description: str
    category: str
    rank: int
    local_rank: int
    unscheduled: bool
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., title: _Optional[str] = ..., description: _Optional[str] = ..., category: _Optional[str] = ..., rank: _Optional[int] = ..., local_rank: _Optional[int] = ..., unscheduled: _Optional[bool] = ..., start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class LocationRiskSummary(_message.Message):
    __slots__ = ("overall_risk_level", "peak_rank", "total_event_count", "unscheduled_event_count", "events_by_category")
    class EventsByCategoryEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    OVERALL_RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    PEAK_RANK_FIELD_NUMBER: _ClassVar[int]
    TOTAL_EVENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    UNSCHEDULED_EVENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    EVENTS_BY_CATEGORY_FIELD_NUMBER: _ClassVar[int]
    overall_risk_level: RiskLevel
    peak_rank: int
    total_event_count: int
    unscheduled_event_count: int
    events_by_category: _containers.ScalarMap[str, int]
    def __init__(self, overall_risk_level: _Optional[_Union[RiskLevel, str]] = ..., peak_rank: _Optional[int] = ..., total_event_count: _Optional[int] = ..., unscheduled_event_count: _Optional[int] = ..., events_by_category: _Optional[_Mapping[str, int]] = ...) -> None: ...
