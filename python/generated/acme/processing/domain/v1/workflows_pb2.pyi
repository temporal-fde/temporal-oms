import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from acme.oms.v1 import message_pb2 as _message_pb2
from acme.oms.v1 import values_pb2 as _values_pb2
from acme.common.v1 import values_pb2 as _values_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProcessOrderRequest(_message.Message):
    __slots__ = ("timestamp", "options", "order_id", "customer_id", "order", "payment")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    options: ProcessOrderRequestExecutionOptions
    order_id: str
    customer_id: str
    order: _values_pb2.Order
    payment: _values_pb2.Payment
    def __init__(self, timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., options: _Optional[_Union[ProcessOrderRequestExecutionOptions, _Mapping]] = ..., order_id: _Optional[str] = ..., customer_id: _Optional[str] = ..., order: _Optional[_Union[_values_pb2.Order, _Mapping]] = ..., payment: _Optional[_Union[_values_pb2.Payment, _Mapping]] = ...) -> None: ...

class ProcessOrderRequestExecutionOptions(_message.Message):
    __slots__ = ("processing_timeout_secs", "oms_properties")
    PROCESSING_TIMEOUT_SECS_FIELD_NUMBER: _ClassVar[int]
    OMS_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    processing_timeout_secs: int
    oms_properties: _message_pb2.OmsProperties
    def __init__(self, processing_timeout_secs: _Optional[int] = ..., oms_properties: _Optional[_Union[_message_pb2.OmsProperties, _Mapping]] = ...) -> None: ...

class GetProcessOrderStateResponse(_message.Message):
    __slots__ = ("args", "validation", "enrichment", "fulfillment", "errors")
    ARGS_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    ENRICHMENT_FIELD_NUMBER: _ClassVar[int]
    FULFILLMENT_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    args: _containers.RepeatedCompositeFieldContainer[ProcessOrderRequest]
    validation: ValidateOrderResponse
    enrichment: EnrichOrderResponse
    fulfillment: FulfillOrderResponse
    errors: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, args: _Optional[_Iterable[_Union[ProcessOrderRequest, _Mapping]]] = ..., validation: _Optional[_Union[ValidateOrderResponse, _Mapping]] = ..., enrichment: _Optional[_Union[EnrichOrderResponse, _Mapping]] = ..., fulfillment: _Optional[_Union[FulfillOrderResponse, _Mapping]] = ..., errors: _Optional[_Iterable[str]] = ...) -> None: ...

class EnrichOrderRequest(_message.Message):
    __slots__ = ("order",)
    ORDER_FIELD_NUMBER: _ClassVar[int]
    order: _values_pb2.Order
    def __init__(self, order: _Optional[_Union[_values_pb2.Order, _Mapping]] = ...) -> None: ...

class EnrichOrderResponse(_message.Message):
    __slots__ = ("order", "items")
    ORDER_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    order: _values_pb2.Order
    items: _containers.RepeatedCompositeFieldContainer[EnrichedItem]
    def __init__(self, order: _Optional[_Union[_values_pb2.Order, _Mapping]] = ..., items: _Optional[_Iterable[_Union[EnrichedItem, _Mapping]]] = ...) -> None: ...

class ValidateOrderRequest(_message.Message):
    __slots__ = ("validation_timeout_secs", "customer_id", "order")
    VALIDATION_TIMEOUT_SECS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    validation_timeout_secs: int
    customer_id: str
    order: _values_pb2.Order
    def __init__(self, validation_timeout_secs: _Optional[int] = ..., customer_id: _Optional[str] = ..., order: _Optional[_Union[_values_pb2.Order, _Mapping]] = ...) -> None: ...

class ValidateOrderResponse(_message.Message):
    __slots__ = ("order", "manual_correction_needed", "support_ticket_id", "validation_failures")
    ORDER_FIELD_NUMBER: _ClassVar[int]
    MANUAL_CORRECTION_NEEDED_FIELD_NUMBER: _ClassVar[int]
    SUPPORT_TICKET_ID_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FAILURES_FIELD_NUMBER: _ClassVar[int]
    order: _values_pb2.Order
    manual_correction_needed: bool
    support_ticket_id: str
    validation_failures: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, order: _Optional[_Union[_values_pb2.Order, _Mapping]] = ..., manual_correction_needed: _Optional[bool] = ..., support_ticket_id: _Optional[str] = ..., validation_failures: _Optional[_Iterable[str]] = ...) -> None: ...

class EnrichedItem(_message.Message):
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

class CompletePaymentRequest(_message.Message):
    __slots__ = ("rrn", "amount_cents")
    RRN_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_CENTS_FIELD_NUMBER: _ClassVar[int]
    rrn: str
    amount_cents: int
    def __init__(self, rrn: _Optional[str] = ..., amount_cents: _Optional[int] = ...) -> None: ...

class CompletePaymentResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: _Optional[bool] = ..., message: _Optional[str] = ...) -> None: ...

class ValidatePaymentRequest(_message.Message):
    __slots__ = ("rrn", "expected_amount_cents")
    RRN_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_AMOUNT_CENTS_FIELD_NUMBER: _ClassVar[int]
    rrn: str
    expected_amount_cents: int
    def __init__(self, rrn: _Optional[str] = ..., expected_amount_cents: _Optional[int] = ...) -> None: ...

class ValidatePaymentResponse(_message.Message):
    __slots__ = ("valid", "payment_status", "actual_amount_cents")
    VALID_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_STATUS_FIELD_NUMBER: _ClassVar[int]
    ACTUAL_AMOUNT_CENTS_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    payment_status: str
    actual_amount_cents: int
    def __init__(self, valid: _Optional[bool] = ..., payment_status: _Optional[str] = ..., actual_amount_cents: _Optional[int] = ...) -> None: ...

class FulfillOrderRequest(_message.Message):
    __slots__ = ("customer_id", "order", "items")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    order: _values_pb2.Order
    items: _containers.RepeatedCompositeFieldContainer[EnrichedItem]
    def __init__(self, customer_id: _Optional[str] = ..., order: _Optional[_Union[_values_pb2.Order, _Mapping]] = ..., items: _Optional[_Iterable[_Union[EnrichedItem, _Mapping]]] = ...) -> None: ...

class FulfillOrderResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitializeSupportTeam(_message.Message):
    __slots__ = ("validation_requests",)
    VALIDATION_REQUESTS_FIELD_NUMBER: _ClassVar[int]
    validation_requests: _containers.RepeatedCompositeFieldContainer[ManuallyValidateOrderRequest]
    def __init__(self, validation_requests: _Optional[_Iterable[_Union[ManuallyValidateOrderRequest, _Mapping]]] = ...) -> None: ...

class ManuallyValidateOrderRequest(_message.Message):
    __slots__ = ("customer_id", "order", "workflow_id", "activity_id")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    WORKFLOW_ID_FIELD_NUMBER: _ClassVar[int]
    ACTIVITY_ID_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    order: _values_pb2.Order
    workflow_id: str
    activity_id: str
    def __init__(self, customer_id: _Optional[str] = ..., order: _Optional[_Union[_values_pb2.Order, _Mapping]] = ..., workflow_id: _Optional[str] = ..., activity_id: _Optional[str] = ...) -> None: ...

class ManuallyValidateOrderResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CompleteOrderValidationRequest(_message.Message):
    __slots__ = ("validation_request", "validation_response")
    VALIDATION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    validation_request: ManuallyValidateOrderRequest
    validation_response: ValidateOrderResponse
    def __init__(self, validation_request: _Optional[_Union[ManuallyValidateOrderRequest, _Mapping]] = ..., validation_response: _Optional[_Union[ValidateOrderResponse, _Mapping]] = ...) -> None: ...

class GetSupportTeamStateResponse(_message.Message):
    __slots__ = ("validation_requests",)
    VALIDATION_REQUESTS_FIELD_NUMBER: _ClassVar[int]
    validation_requests: _containers.RepeatedCompositeFieldContainer[ManuallyValidateOrderRequest]
    def __init__(self, validation_requests: _Optional[_Iterable[_Union[ManuallyValidateOrderRequest, _Mapping]]] = ...) -> None: ...
