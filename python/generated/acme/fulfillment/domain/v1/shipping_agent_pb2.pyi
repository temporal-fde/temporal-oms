import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from acme.fulfillment.domain.v1 import values_pb2 as _values_pb2
from acme.common.v1 import values_pb2 as _values_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetLocationEventsRequest(_message.Message):
    __slots__ = ("coordinate", "within_km", "active_from", "active_to", "timezone")
    COORDINATE_FIELD_NUMBER: _ClassVar[int]
    WITHIN_KM_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FROM_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_TO_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    coordinate: _values_pb2_1.Coordinate
    within_km: float
    active_from: _timestamp_pb2.Timestamp
    active_to: _timestamp_pb2.Timestamp
    timezone: str
    def __init__(self, coordinate: _Optional[_Union[_values_pb2_1.Coordinate, _Mapping]] = ..., within_km: _Optional[float] = ..., active_from: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., active_to: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., timezone: _Optional[str] = ...) -> None: ...

class GetLocationEventsResponse(_message.Message):
    __slots__ = ("summary", "events", "window_from", "window_to", "timezone")
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    WINDOW_FROM_FIELD_NUMBER: _ClassVar[int]
    WINDOW_TO_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    summary: _values_pb2.LocationRiskSummary
    events: _containers.RepeatedCompositeFieldContainer[_values_pb2.LocationEvent]
    window_from: _timestamp_pb2.Timestamp
    window_to: _timestamp_pb2.Timestamp
    timezone: str
    def __init__(self, summary: _Optional[_Union[_values_pb2.LocationRiskSummary, _Mapping]] = ..., events: _Optional[_Iterable[_Union[_values_pb2.LocationEvent, _Mapping]]] = ..., window_from: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., window_to: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., timezone: _Optional[str] = ...) -> None: ...

class StartShippingAgentRequest(_message.Message):
    __slots__ = ("execution_options", "customer_id")
    EXECUTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    execution_options: ShippingAgentExecutionOptions
    customer_id: str
    def __init__(self, execution_options: _Optional[_Union[ShippingAgentExecutionOptions, _Mapping]] = ..., customer_id: _Optional[str] = ...) -> None: ...

class ShippingAgentExecutionOptions(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CalculateShippingOptionsRequest(_message.Message):
    __slots__ = ("address", "coordinate")
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    COORDINATE_FIELD_NUMBER: _ClassVar[int]
    address: _values_pb2_1.Address
    coordinate: _values_pb2_1.Coordinate
    def __init__(self, address: _Optional[_Union[_values_pb2_1.Address, _Mapping]] = ..., coordinate: _Optional[_Union[_values_pb2_1.Coordinate, _Mapping]] = ...) -> None: ...

class CalculateShippingOptionsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
