from google.protobuf import timestamp_pb2 as _timestamp_pb2
from acme.fulfillment.domain.v1 import values_pb2 as _values_pb2
from acme.common.v1 import values_pb2 as _values_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StartInventoryRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LookupInventoryAddressRequest(_message.Message):
    __slots__ = ()
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_ID_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[_values_pb2.ShippingLineItem]
    address_id: str
    def __init__(self, items: _Optional[_Iterable[_Union[_values_pb2.ShippingLineItem, _Mapping]]] = ..., address_id: _Optional[str] = ...) -> None: ...

class LookupInventoryAddressResponse(_message.Message):
    __slots__ = ()
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: _values_pb2_1.Address
    def __init__(self, address: _Optional[_Union[_values_pb2_1.Address, _Mapping]] = ...) -> None: ...

class FindAlternateWarehouseRequest(_message.Message):
    __slots__ = ()
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_ADDRESS_ID_FIELD_NUMBER: _ClassVar[int]
    TO_ADDRESS_ID_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[_values_pb2.ShippingLineItem]
    current_address_id: str
    to_address_id: str
    def __init__(self, items: _Optional[_Iterable[_Union[_values_pb2.ShippingLineItem, _Mapping]]] = ..., current_address_id: _Optional[str] = ..., to_address_id: _Optional[str] = ...) -> None: ...

class FindAlternateWarehouseResponse(_message.Message):
    __slots__ = ()
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: _values_pb2_1.Address
    def __init__(self, address: _Optional[_Union[_values_pb2_1.Address, _Mapping]] = ...) -> None: ...
