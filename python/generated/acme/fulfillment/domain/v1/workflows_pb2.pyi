import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATUS_UNSPECIFIED: _ClassVar[Status]
    STATUS_PENDING: _ClassVar[Status]
    STATUS_ALLOCATING: _ClassVar[Status]
    STATUS_SHIPPING_SELECTED: _ClassVar[Status]
    STATUS_COMPLETED: _ClassVar[Status]
    STATUS_FAILED: _ClassVar[Status]
STATUS_UNSPECIFIED: Status
STATUS_PENDING: Status
STATUS_ALLOCATING: Status
STATUS_SHIPPING_SELECTED: Status
STATUS_COMPLETED: Status
STATUS_FAILED: Status

class FulfillOrderRequest(_message.Message):
    __slots__ = ("order_id", "customer_id", "items", "payment_rrn", "shipping_address", "created_at")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_RRN_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    customer_id: str
    items: _containers.RepeatedCompositeFieldContainer[Item]
    payment_rrn: str
    shipping_address: ShippingAddress
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, order_id: _Optional[str] = ..., customer_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., payment_rrn: _Optional[str] = ..., shipping_address: _Optional[_Union[ShippingAddress, _Mapping]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class FulfillOrderResponse(_message.Message):
    __slots__ = ("order_id", "status", "shipping", "allocated_items", "completed_at")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_FIELD_NUMBER: _ClassVar[int]
    ALLOCATED_ITEMS_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_AT_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    status: Status
    shipping: ShippingDetails
    allocated_items: _containers.RepeatedCompositeFieldContainer[AllocatedItem]
    completed_at: _timestamp_pb2.Timestamp
    def __init__(self, order_id: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., shipping: _Optional[_Union[ShippingDetails, _Mapping]] = ..., allocated_items: _Optional[_Iterable[_Union[AllocatedItem, _Mapping]]] = ..., completed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class Item(_message.Message):
    __slots__ = ("item_id", "sku_id", "brand_code", "quantity")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SKU_ID_FIELD_NUMBER: _ClassVar[int]
    BRAND_CODE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    sku_id: str
    brand_code: str
    quantity: int
    def __init__(self, item_id: _Optional[str] = ..., sku_id: _Optional[str] = ..., brand_code: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

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

class ShippingDetails(_message.Message):
    __slots__ = ("carrier", "service_level", "cost_cents", "estimated_days", "tracking_number")
    CARRIER_FIELD_NUMBER: _ClassVar[int]
    SERVICE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    COST_CENTS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_DAYS_FIELD_NUMBER: _ClassVar[int]
    TRACKING_NUMBER_FIELD_NUMBER: _ClassVar[int]
    carrier: str
    service_level: str
    cost_cents: int
    estimated_days: int
    tracking_number: str
    def __init__(self, carrier: _Optional[str] = ..., service_level: _Optional[str] = ..., cost_cents: _Optional[int] = ..., estimated_days: _Optional[int] = ..., tracking_number: _Optional[str] = ...) -> None: ...

class AllocatedItem(_message.Message):
    __slots__ = ("item_id", "sku_id", "quantity", "warehouse_id", "warehouse_location")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SKU_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    WAREHOUSE_ID_FIELD_NUMBER: _ClassVar[int]
    WAREHOUSE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    sku_id: str
    quantity: int
    warehouse_id: str
    warehouse_location: str
    def __init__(self, item_id: _Optional[str] = ..., sku_id: _Optional[str] = ..., quantity: _Optional[int] = ..., warehouse_id: _Optional[str] = ..., warehouse_location: _Optional[str] = ...) -> None: ...

class FindOptimalShippingRequest(_message.Message):
    __slots__ = ("destination", "items", "max_cost_cents", "max_days")
    DESTINATION_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    MAX_COST_CENTS_FIELD_NUMBER: _ClassVar[int]
    MAX_DAYS_FIELD_NUMBER: _ClassVar[int]
    destination: ShippingAddress
    items: _containers.RepeatedCompositeFieldContainer[Item]
    max_cost_cents: int
    max_days: int
    def __init__(self, destination: _Optional[_Union[ShippingAddress, _Mapping]] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., max_cost_cents: _Optional[int] = ..., max_days: _Optional[int] = ...) -> None: ...

class FindOptimalShippingResponse(_message.Message):
    __slots__ = ("options", "recommended", "reasoning")
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    options: _containers.RepeatedCompositeFieldContainer[ShippingOption]
    recommended: ShippingOption
    reasoning: str
    def __init__(self, options: _Optional[_Iterable[_Union[ShippingOption, _Mapping]]] = ..., recommended: _Optional[_Union[ShippingOption, _Mapping]] = ..., reasoning: _Optional[str] = ...) -> None: ...

class ShippingOption(_message.Message):
    __slots__ = ("carrier", "service_level", "cost_cents", "estimated_days", "score")
    CARRIER_FIELD_NUMBER: _ClassVar[int]
    SERVICE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    COST_CENTS_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_DAYS_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    carrier: str
    service_level: str
    cost_cents: int
    estimated_days: int
    score: float
    def __init__(self, carrier: _Optional[str] = ..., service_level: _Optional[str] = ..., cost_cents: _Optional[int] = ..., estimated_days: _Optional[int] = ..., score: _Optional[float] = ...) -> None: ...

class AllocateInventoryRequest(_message.Message):
    __slots__ = ("items", "destination")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    destination: ShippingAddress
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., destination: _Optional[_Union[ShippingAddress, _Mapping]] = ...) -> None: ...

class AllocateInventoryResponse(_message.Message):
    __slots__ = ("allocations", "fully_allocated", "warnings")
    ALLOCATIONS_FIELD_NUMBER: _ClassVar[int]
    FULLY_ALLOCATED_FIELD_NUMBER: _ClassVar[int]
    WARNINGS_FIELD_NUMBER: _ClassVar[int]
    allocations: _containers.RepeatedCompositeFieldContainer[AllocatedItem]
    fully_allocated: bool
    warnings: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, allocations: _Optional[_Iterable[_Union[AllocatedItem, _Mapping]]] = ..., fully_allocated: _Optional[bool] = ..., warnings: _Optional[_Iterable[str]] = ...) -> None: ...

class FindClosestWarehouseRequest(_message.Message):
    __slots__ = ("sku_id", "quantity", "destination")
    SKU_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_FIELD_NUMBER: _ClassVar[int]
    sku_id: str
    quantity: int
    destination: ShippingAddress
    def __init__(self, sku_id: _Optional[str] = ..., quantity: _Optional[int] = ..., destination: _Optional[_Union[ShippingAddress, _Mapping]] = ...) -> None: ...

class FindClosestWarehouseResponse(_message.Message):
    __slots__ = ("warehouse_id", "warehouse_location", "available_quantity", "distance_km")
    WAREHOUSE_ID_FIELD_NUMBER: _ClassVar[int]
    WAREHOUSE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_QUANTITY_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_KM_FIELD_NUMBER: _ClassVar[int]
    warehouse_id: str
    warehouse_location: str
    available_quantity: int
    distance_km: float
    def __init__(self, warehouse_id: _Optional[str] = ..., warehouse_location: _Optional[str] = ..., available_quantity: _Optional[int] = ..., distance_km: _Optional[float] = ...) -> None: ...

class FulfilledOrderEvent(_message.Message):
    __slots__ = ("customer_id", "order_id", "payment_details", "items", "shipping", "fulfilled_at")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_DETAILS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_FIELD_NUMBER: _ClassVar[int]
    FULFILLED_AT_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    order_id: str
    payment_details: PaymentDetails
    items: _containers.RepeatedCompositeFieldContainer[ItemOutput]
    shipping: ShippingDetails
    fulfilled_at: _timestamp_pb2.Timestamp
    def __init__(self, customer_id: _Optional[str] = ..., order_id: _Optional[str] = ..., payment_details: _Optional[_Union[PaymentDetails, _Mapping]] = ..., items: _Optional[_Iterable[_Union[ItemOutput, _Mapping]]] = ..., shipping: _Optional[_Union[ShippingDetails, _Mapping]] = ..., fulfilled_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PaymentDetails(_message.Message):
    __slots__ = ("rrn",)
    RRN_FIELD_NUMBER: _ClassVar[int]
    rrn: str
    def __init__(self, rrn: _Optional[str] = ...) -> None: ...

class ItemOutput(_message.Message):
    __slots__ = ("item_id", "sku_id", "brand_code", "quantity", "warehouse_id")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SKU_ID_FIELD_NUMBER: _ClassVar[int]
    BRAND_CODE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    WAREHOUSE_ID_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    sku_id: str
    brand_code: str
    quantity: int
    warehouse_id: str
    def __init__(self, item_id: _Optional[str] = ..., sku_id: _Optional[str] = ..., brand_code: _Optional[str] = ..., quantity: _Optional[int] = ..., warehouse_id: _Optional[str] = ...) -> None: ...
