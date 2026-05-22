import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Money(_message.Message):
    __slots__ = ()
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    UNITS_FIELD_NUMBER: _ClassVar[int]
    currency: str
    units: int
    def __init__(self, currency: _Optional[str] = ..., units: _Optional[int] = ...) -> None: ...

class EasyPostAddress(_message.Message):
    __slots__ = ()
    ID_FIELD_NUMBER: _ClassVar[int]
    STREET1_FIELD_NUMBER: _ClassVar[int]
    STREET2_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ZIP_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    RESIDENTIAL_FIELD_NUMBER: _ClassVar[int]
    COORDINATE_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    COMPANY_FIELD_NUMBER: _ClassVar[int]
    id: str
    street1: str
    street2: str
    city: str
    state: str
    zip: str
    country: str
    residential: bool
    coordinate: Coordinate
    timezone: str
    company: str
    def __init__(self, id: _Optional[str] = ..., street1: _Optional[str] = ..., street2: _Optional[str] = ..., city: _Optional[str] = ..., state: _Optional[str] = ..., zip: _Optional[str] = ..., country: _Optional[str] = ..., residential: _Optional[bool] = ..., coordinate: _Optional[_Union[Coordinate, _Mapping]] = ..., timezone: _Optional[str] = ..., company: _Optional[str] = ...) -> None: ...

class EasyPostRate(_message.Message):
    __slots__ = ()
    RATE_ID_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_DAYS_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_DATE_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_DATE_GUARANTEED_FIELD_NUMBER: _ClassVar[int]
    rate_id: str
    delivery_days: int
    delivery_date: _timestamp_pb2.Timestamp
    delivery_date_guaranteed: bool
    def __init__(self, rate_id: _Optional[str] = ..., delivery_days: _Optional[int] = ..., delivery_date: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., delivery_date_guaranteed: _Optional[bool] = ...) -> None: ...

class EasyPostShipment(_message.Message):
    __slots__ = ()
    SHIPMENT_ID_FIELD_NUMBER: _ClassVar[int]
    SELECTED_RATE_FIELD_NUMBER: _ClassVar[int]
    shipment_id: str
    selected_rate: EasyPostRate
    def __init__(self, shipment_id: _Optional[str] = ..., selected_rate: _Optional[_Union[EasyPostRate, _Mapping]] = ...) -> None: ...

class Address(_message.Message):
    __slots__ = ()
    EASYPOST_FIELD_NUMBER: _ClassVar[int]
    easypost: EasyPostAddress
    def __init__(self, easypost: _Optional[_Union[EasyPostAddress, _Mapping]] = ...) -> None: ...

class Shipment(_message.Message):
    __slots__ = ()
    EASYPOST_FIELD_NUMBER: _ClassVar[int]
    PAID_PRICE_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_DATE_FIELD_NUMBER: _ClassVar[int]
    easypost: EasyPostShipment
    paid_price: Money
    delivery_date: _timestamp_pb2.Timestamp
    def __init__(self, easypost: _Optional[_Union[EasyPostShipment, _Mapping]] = ..., paid_price: _Optional[_Union[Money, _Mapping]] = ..., delivery_date: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class TimeRange(_message.Message):
    __slots__ = ()
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    def __init__(self, start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Pagination(_message.Message):
    __slots__ = ()
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    page_size: int
    page_token: str
    def __init__(self, page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ErrorDetails(_message.Message):
    __slots__ = ()
    class MetadataEntry(_message.Message):
        __slots__ = ()
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    code: str
    message: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, code: _Optional[str] = ..., message: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Coordinate(_message.Message):
    __slots__ = ()
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    latitude: float
    longitude: float
    def __init__(self, latitude: _Optional[float] = ..., longitude: _Optional[float] = ...) -> None: ...
