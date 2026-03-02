from acme.common.v1 import values_pb2 as _values_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Order(_message.Message):
    __slots__ = ("order_id", "items", "shipping_address")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    items: _containers.RepeatedCompositeFieldContainer[Item]
    shipping_address: ShippingAddress
    def __init__(self, order_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., shipping_address: _Optional[_Union[ShippingAddress, _Mapping]] = ...) -> None: ...

class Payment(_message.Message):
    __slots__ = ("rrn", "amount")
    RRN_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    rrn: str
    amount: _values_pb2.Money
    def __init__(self, rrn: _Optional[str] = ..., amount: _Optional[_Union[_values_pb2.Money, _Mapping]] = ...) -> None: ...

class Item(_message.Message):
    __slots__ = ("item_id", "quantity")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    quantity: int
    def __init__(self, item_id: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class ShippingAddress(_message.Message):
    __slots__ = ("street", "city", "state", "postal_code", "country")
    STREET_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    POSTAL_CODE_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    def __init__(self, street: _Optional[str] = ..., city: _Optional[str] = ..., state: _Optional[str] = ..., postal_code: _Optional[str] = ..., country: _Optional[str] = ...) -> None: ...
