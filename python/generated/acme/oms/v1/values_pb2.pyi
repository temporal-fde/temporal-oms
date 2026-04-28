from acme.common.v1 import values_pb2 as _values_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Order(_message.Message):
    __slots__ = ()
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    SELECTED_SHIPMENT_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    items: _containers.RepeatedCompositeFieldContainer[Item]
    shipping_address: _values_pb2.Address
    selected_shipment: _values_pb2.Shipment
    def __init__(self, order_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., shipping_address: _Optional[_Union[_values_pb2.Address, _Mapping]] = ..., selected_shipment: _Optional[_Union[_values_pb2.Shipment, _Mapping]] = ...) -> None: ...

class Payment(_message.Message):
    __slots__ = ()
    RRN_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    rrn: str
    amount: _values_pb2.Money
    def __init__(self, rrn: _Optional[str] = ..., amount: _Optional[_Union[_values_pb2.Money, _Mapping]] = ...) -> None: ...

class Item(_message.Message):
    __slots__ = ()
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    quantity: int
    def __init__(self, item_id: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...
