import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from acme.common.v1 import values_pb2 as _values_pb2
from acme.apps.domain.v1 import workflows_pb2 as _workflows_pb2
from acme.processing.domain.v1 import workflows_pb2 as _workflows_pb2_1
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

class DeliveryStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DELIVERY_STATUS_UNSPECIFIED: _ClassVar[DeliveryStatus]
    DELIVERY_STATUS_DELIVERED: _ClassVar[DeliveryStatus]
    DELIVERY_STATUS_CANCELED: _ClassVar[DeliveryStatus]

class FulfillmentStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FULFILLMENT_STATUS_UNSPECIFIED: _ClassVar[FulfillmentStatus]
    FULFILLMENT_STATUS_STARTED: _ClassVar[FulfillmentStatus]
    FULFILLMENT_STATUS_VALIDATED: _ClassVar[FulfillmentStatus]
    FULFILLMENT_STATUS_FULFILLING: _ClassVar[FulfillmentStatus]
    FULFILLMENT_STATUS_COMPLETED: _ClassVar[FulfillmentStatus]
    FULFILLMENT_STATUS_DELIVERED: _ClassVar[FulfillmentStatus]
    FULFILLMENT_STATUS_CANCELED: _ClassVar[FulfillmentStatus]
    FULFILLMENT_STATUS_FAILED: _ClassVar[FulfillmentStatus]
STATUS_UNSPECIFIED: Status
STATUS_PENDING: Status
STATUS_ALLOCATING: Status
STATUS_SHIPPING_SELECTED: Status
STATUS_COMPLETED: Status
STATUS_FAILED: Status
DELIVERY_STATUS_UNSPECIFIED: DeliveryStatus
DELIVERY_STATUS_DELIVERED: DeliveryStatus
DELIVERY_STATUS_CANCELED: DeliveryStatus
FULFILLMENT_STATUS_UNSPECIFIED: FulfillmentStatus
FULFILLMENT_STATUS_STARTED: FulfillmentStatus
FULFILLMENT_STATUS_VALIDATED: FulfillmentStatus
FULFILLMENT_STATUS_FULFILLING: FulfillmentStatus
FULFILLMENT_STATUS_COMPLETED: FulfillmentStatus
FULFILLMENT_STATUS_DELIVERED: FulfillmentStatus
FULFILLMENT_STATUS_CANCELED: FulfillmentStatus
FULFILLMENT_STATUS_FAILED: FulfillmentStatus

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
    destination: _values_pb2.Address
    items: _containers.RepeatedCompositeFieldContainer[Item]
    max_cost_cents: int
    max_days: int
    def __init__(self, destination: _Optional[_Union[_values_pb2.Address, _Mapping]] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., max_cost_cents: _Optional[int] = ..., max_days: _Optional[int] = ...) -> None: ...

class FindOptimalShippingResponse(_message.Message):
    __slots__ = ("options", "recommended", "reasoning")
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    options: _containers.RepeatedCompositeFieldContainer[ShippingOptionLegacy]
    recommended: ShippingOptionLegacy
    reasoning: str
    def __init__(self, options: _Optional[_Iterable[_Union[ShippingOptionLegacy, _Mapping]]] = ..., recommended: _Optional[_Union[ShippingOptionLegacy, _Mapping]] = ..., reasoning: _Optional[str] = ...) -> None: ...

class ShippingOptionLegacy(_message.Message):
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
    destination: _values_pb2.Address
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., destination: _Optional[_Union[_values_pb2.Address, _Mapping]] = ...) -> None: ...

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
    destination: _values_pb2.Address
    def __init__(self, sku_id: _Optional[str] = ..., quantity: _Optional[int] = ..., destination: _Optional[_Union[_values_pb2.Address, _Mapping]] = ...) -> None: ...

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

class StartOrderFulfillmentRequest(_message.Message):
    __slots__ = ("order_id", "customer_id", "options", "selected_shipping", "placed_order")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    SELECTED_SHIPPING_FIELD_NUMBER: _ClassVar[int]
    PLACED_ORDER_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    customer_id: str
    options: StartOrderFulfillmentOptions
    selected_shipping: SelectedShippingOption
    placed_order: _workflows_pb2.CompleteOrderRequest
    def __init__(self, order_id: _Optional[str] = ..., customer_id: _Optional[str] = ..., options: _Optional[_Union[StartOrderFulfillmentOptions, _Mapping]] = ..., selected_shipping: _Optional[_Union[SelectedShippingOption, _Mapping]] = ..., placed_order: _Optional[_Union[_workflows_pb2.CompleteOrderRequest, _Mapping]] = ...) -> None: ...

class StartOrderFulfillmentOptions(_message.Message):
    __slots__ = ("fulfillment_timeout_secs",)
    FULFILLMENT_TIMEOUT_SECS_FIELD_NUMBER: _ClassVar[int]
    fulfillment_timeout_secs: int
    def __init__(self, fulfillment_timeout_secs: _Optional[int] = ...) -> None: ...

class SelectedShippingOption(_message.Message):
    __slots__ = ("option_id", "price", "expected_ship_date")
    OPTION_ID_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_SHIP_DATE_FIELD_NUMBER: _ClassVar[int]
    option_id: str
    price: _values_pb2.Money
    expected_ship_date: _timestamp_pb2.Timestamp
    def __init__(self, option_id: _Optional[str] = ..., price: _Optional[_Union[_values_pb2.Money, _Mapping]] = ..., expected_ship_date: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ValidateOrderRequest(_message.Message):
    __slots__ = ("order_id", "address")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    address: _values_pb2.Address
    def __init__(self, order_id: _Optional[str] = ..., address: _Optional[_Union[_values_pb2.Address, _Mapping]] = ...) -> None: ...

class ValidateOrderResponse(_message.Message):
    __slots__ = ("address",)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: _values_pb2.Address
    def __init__(self, address: _Optional[_Union[_values_pb2.Address, _Mapping]] = ...) -> None: ...

class VerifyAddressRequest(_message.Message):
    __slots__ = ("address",)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: _values_pb2.Address
    def __init__(self, address: _Optional[_Union[_values_pb2.Address, _Mapping]] = ...) -> None: ...

class VerifyAddressResponse(_message.Message):
    __slots__ = ("address",)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: _values_pb2.Address
    def __init__(self, address: _Optional[_Union[_values_pb2.Address, _Mapping]] = ...) -> None: ...

class LoadFulfillmentOptionsRequest(_message.Message):
    __slots__ = ("order_id",)
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    def __init__(self, order_id: _Optional[str] = ...) -> None: ...

class FulfillmentOptions(_message.Message):
    __slots__ = ("shipping_margin", "integrations_endpoint", "shipping_agent_endpoint")
    SHIPPING_MARGIN_FIELD_NUMBER: _ClassVar[int]
    INTEGRATIONS_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_AGENT_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    shipping_margin: _values_pb2.Money
    integrations_endpoint: str
    shipping_agent_endpoint: str
    def __init__(self, shipping_margin: _Optional[_Union[_values_pb2.Money, _Mapping]] = ..., integrations_endpoint: _Optional[str] = ..., shipping_agent_endpoint: _Optional[str] = ...) -> None: ...

class FulfillOrderRequest(_message.Message):
    __slots__ = ("processed_order", "delivery_status_request", "selected_shipping_option_id")
    PROCESSED_ORDER_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_STATUS_REQUEST_FIELD_NUMBER: _ClassVar[int]
    SELECTED_SHIPPING_OPTION_ID_FIELD_NUMBER: _ClassVar[int]
    processed_order: ProcessedOrder
    delivery_status_request: NotifyDeliveryStatusRequest
    selected_shipping_option_id: str
    def __init__(self, processed_order: _Optional[_Union[ProcessedOrder, _Mapping]] = ..., delivery_status_request: _Optional[_Union[NotifyDeliveryStatusRequest, _Mapping]] = ..., selected_shipping_option_id: _Optional[str] = ...) -> None: ...

class ProcessedOrder(_message.Message):
    __slots__ = ("order_id", "customer_id", "state")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    customer_id: str
    state: _workflows_pb2_1.GetProcessOrderStateResponse
    def __init__(self, order_id: _Optional[str] = ..., customer_id: _Optional[str] = ..., state: _Optional[_Union[_workflows_pb2_1.GetProcessOrderStateResponse, _Mapping]] = ...) -> None: ...

class FulfillOrderResponse(_message.Message):
    __slots__ = ("tracking_number", "shipping_selection")
    TRACKING_NUMBER_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_SELECTION_FIELD_NUMBER: _ClassVar[int]
    tracking_number: str
    shipping_selection: ShippingSelection
    def __init__(self, tracking_number: _Optional[str] = ..., shipping_selection: _Optional[_Union[ShippingSelection, _Mapping]] = ...) -> None: ...

class ShippingSelection(_message.Message):
    __slots__ = ("option_id", "rate_id", "carrier", "service_level", "actual_price", "margin_delta_cents", "is_fallback", "fallback_reason")
    OPTION_ID_FIELD_NUMBER: _ClassVar[int]
    RATE_ID_FIELD_NUMBER: _ClassVar[int]
    CARRIER_FIELD_NUMBER: _ClassVar[int]
    SERVICE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_PRICE_FIELD_NUMBER: _ClassVar[int]
    MARGIN_DELTA_CENTS_FIELD_NUMBER: _ClassVar[int]
    IS_FALLBACK_FIELD_NUMBER: _ClassVar[int]
    FALLBACK_REASON_FIELD_NUMBER: _ClassVar[int]
    option_id: str
    rate_id: str
    carrier: str
    service_level: str
    actual_price: _values_pb2.Money
    margin_delta_cents: int
    is_fallback: bool
    fallback_reason: str
    def __init__(self, option_id: _Optional[str] = ..., rate_id: _Optional[str] = ..., carrier: _Optional[str] = ..., service_level: _Optional[str] = ..., actual_price: _Optional[_Union[_values_pb2.Money, _Mapping]] = ..., margin_delta_cents: _Optional[int] = ..., is_fallback: _Optional[bool] = ..., fallback_reason: _Optional[str] = ...) -> None: ...

class CancelFulfillmentOrderRequest(_message.Message):
    __slots__ = ("order_id", "reason")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    reason: str
    def __init__(self, order_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class NotifyDeliveryStatusRequest(_message.Message):
    __slots__ = ("order_id", "delivery_status", "carrier_tracking_id", "failure_reason")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_STATUS_FIELD_NUMBER: _ClassVar[int]
    CARRIER_TRACKING_ID_FIELD_NUMBER: _ClassVar[int]
    FAILURE_REASON_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    delivery_status: DeliveryStatus
    carrier_tracking_id: str
    failure_reason: str
    def __init__(self, order_id: _Optional[str] = ..., delivery_status: _Optional[_Union[DeliveryStatus, str]] = ..., carrier_tracking_id: _Optional[str] = ..., failure_reason: _Optional[str] = ...) -> None: ...

class GetFulfillmentOrderStateResponse(_message.Message):
    __slots__ = ("args", "options", "validated_address", "fulfillment_request", "shipping_selection", "tracking_number", "status", "delivery_status", "errors", "notify_delivery_status")
    ARGS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    VALIDATED_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    FULFILLMENT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    SHIPPING_SELECTION_FIELD_NUMBER: _ClassVar[int]
    TRACKING_NUMBER_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_STATUS_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    NOTIFY_DELIVERY_STATUS_FIELD_NUMBER: _ClassVar[int]
    args: StartOrderFulfillmentRequest
    options: FulfillmentOptions
    validated_address: _values_pb2.Address
    fulfillment_request: FulfillOrderRequest
    shipping_selection: ShippingSelection
    tracking_number: str
    status: FulfillmentStatus
    delivery_status: DeliveryStatus
    errors: _containers.RepeatedScalarFieldContainer[str]
    notify_delivery_status: NotifyDeliveryStatusRequest
    def __init__(self, args: _Optional[_Union[StartOrderFulfillmentRequest, _Mapping]] = ..., options: _Optional[_Union[FulfillmentOptions, _Mapping]] = ..., validated_address: _Optional[_Union[_values_pb2.Address, _Mapping]] = ..., fulfillment_request: _Optional[_Union[FulfillOrderRequest, _Mapping]] = ..., shipping_selection: _Optional[_Union[ShippingSelection, _Mapping]] = ..., tracking_number: _Optional[str] = ..., status: _Optional[_Union[FulfillmentStatus, str]] = ..., delivery_status: _Optional[_Union[DeliveryStatus, str]] = ..., errors: _Optional[_Iterable[str]] = ..., notify_delivery_status: _Optional[_Union[NotifyDeliveryStatusRequest, _Mapping]] = ...) -> None: ...

class FulfillmentItem(_message.Message):
    __slots__ = ("item_id", "sku_id", "brand_code", "quantity", "warehouse_id", "warehouse_location")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SKU_ID_FIELD_NUMBER: _ClassVar[int]
    BRAND_CODE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    WAREHOUSE_ID_FIELD_NUMBER: _ClassVar[int]
    WAREHOUSE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    sku_id: str
    brand_code: str
    quantity: int
    warehouse_id: str
    warehouse_location: str
    def __init__(self, item_id: _Optional[str] = ..., sku_id: _Optional[str] = ..., brand_code: _Optional[str] = ..., quantity: _Optional[int] = ..., warehouse_id: _Optional[str] = ..., warehouse_location: _Optional[str] = ...) -> None: ...

class HoldItemsRequest(_message.Message):
    __slots__ = ("order_id", "items")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    items: _containers.RepeatedCompositeFieldContainer[FulfillmentItem]
    def __init__(self, order_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[FulfillmentItem, _Mapping]]] = ...) -> None: ...

class HoldItemsResponse(_message.Message):
    __slots__ = ("hold_id",)
    HOLD_ID_FIELD_NUMBER: _ClassVar[int]
    hold_id: str
    def __init__(self, hold_id: _Optional[str] = ...) -> None: ...

class ReserveItemsRequest(_message.Message):
    __slots__ = ("order_id", "hold_id", "items")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    HOLD_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    hold_id: str
    items: _containers.RepeatedCompositeFieldContainer[FulfillmentItem]
    def __init__(self, order_id: _Optional[str] = ..., hold_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[FulfillmentItem, _Mapping]]] = ...) -> None: ...

class ReserveItemsResponse(_message.Message):
    __slots__ = ("reservation_id",)
    RESERVATION_ID_FIELD_NUMBER: _ClassVar[int]
    reservation_id: str
    def __init__(self, reservation_id: _Optional[str] = ...) -> None: ...

class DeductInventoryRequest(_message.Message):
    __slots__ = ("order_id", "reservation_id")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    RESERVATION_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    reservation_id: str
    def __init__(self, order_id: _Optional[str] = ..., reservation_id: _Optional[str] = ...) -> None: ...

class DeductInventoryResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: _Optional[bool] = ...) -> None: ...

class ReleaseHoldRequest(_message.Message):
    __slots__ = ("order_id", "hold_id")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    HOLD_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    hold_id: str
    def __init__(self, order_id: _Optional[str] = ..., hold_id: _Optional[str] = ...) -> None: ...

class ReleaseHoldResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: _Optional[bool] = ...) -> None: ...

class GetCarrierRatesRequest(_message.Message):
    __slots__ = ("order_id", "easypost_address_id", "items")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    EASYPOST_ADDRESS_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    easypost_address_id: str
    items: _containers.RepeatedCompositeFieldContainer[FulfillmentItem]
    def __init__(self, order_id: _Optional[str] = ..., easypost_address_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[FulfillmentItem, _Mapping]]] = ...) -> None: ...

class GetCarrierRatesResponse(_message.Message):
    __slots__ = ("shipment_id", "rates")
    SHIPMENT_ID_FIELD_NUMBER: _ClassVar[int]
    RATES_FIELD_NUMBER: _ClassVar[int]
    shipment_id: str
    rates: _containers.RepeatedCompositeFieldContainer[CarrierRate]
    def __init__(self, shipment_id: _Optional[str] = ..., rates: _Optional[_Iterable[_Union[CarrierRate, _Mapping]]] = ...) -> None: ...

class CarrierRate(_message.Message):
    __slots__ = ("rate_id", "carrier", "service_level", "cost", "estimated_days")
    RATE_ID_FIELD_NUMBER: _ClassVar[int]
    CARRIER_FIELD_NUMBER: _ClassVar[int]
    SERVICE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    COST_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_DAYS_FIELD_NUMBER: _ClassVar[int]
    rate_id: str
    carrier: str
    service_level: str
    cost: _values_pb2.Money
    estimated_days: int
    def __init__(self, rate_id: _Optional[str] = ..., carrier: _Optional[str] = ..., service_level: _Optional[str] = ..., cost: _Optional[_Union[_values_pb2.Money, _Mapping]] = ..., estimated_days: _Optional[int] = ...) -> None: ...

class PrintShippingLabelRequest(_message.Message):
    __slots__ = ("order_id", "shipment_id", "rate_id")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    SHIPMENT_ID_FIELD_NUMBER: _ClassVar[int]
    RATE_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    shipment_id: str
    rate_id: str
    def __init__(self, order_id: _Optional[str] = ..., shipment_id: _Optional[str] = ..., rate_id: _Optional[str] = ...) -> None: ...

class PrintShippingLabelResponse(_message.Message):
    __slots__ = ("tracking_number", "label_url")
    TRACKING_NUMBER_FIELD_NUMBER: _ClassVar[int]
    LABEL_URL_FIELD_NUMBER: _ClassVar[int]
    tracking_number: str
    label_url: str
    def __init__(self, tracking_number: _Optional[str] = ..., label_url: _Optional[str] = ...) -> None: ...
