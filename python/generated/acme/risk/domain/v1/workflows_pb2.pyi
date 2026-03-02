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
    STATUS_PASSED: _ClassVar[Status]
    STATUS_FLAGGED: _ClassVar[Status]
    STATUS_BLOCKED: _ClassVar[Status]
STATUS_UNSPECIFIED: Status
STATUS_PENDING: Status
STATUS_PASSED: Status
STATUS_FLAGGED: Status
STATUS_BLOCKED: Status

class DetectFraudRequest(_message.Message):
    __slots__ = ("order_id", "customer_id", "context", "created_at")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    customer_id: str
    context: FraudCheckContext
    created_at: _timestamp_pb2.Timestamp
    def __init__(self, order_id: _Optional[str] = ..., customer_id: _Optional[str] = ..., context: _Optional[_Union[FraudCheckContext, _Mapping]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class DetectFraudResponse(_message.Message):
    __slots__ = ("order_id", "status", "risk_score", "flags", "completed_at")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_AT_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    status: Status
    risk_score: float
    flags: _containers.RepeatedScalarFieldContainer[str]
    completed_at: _timestamp_pb2.Timestamp
    def __init__(self, order_id: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., risk_score: _Optional[float] = ..., flags: _Optional[_Iterable[str]] = ..., completed_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class FraudCheckContext(_message.Message):
    __slots__ = ("payment", "address", "customer")
    PAYMENT_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_FIELD_NUMBER: _ClassVar[int]
    payment: PaymentContext
    address: AddressContext
    customer: CustomerContext
    def __init__(self, payment: _Optional[_Union[PaymentContext, _Mapping]] = ..., address: _Optional[_Union[AddressContext, _Mapping]] = ..., customer: _Optional[_Union[CustomerContext, _Mapping]] = ...) -> None: ...

class PaymentContext(_message.Message):
    __slots__ = ("rrn", "amount_cents", "payment_method")
    RRN_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_CENTS_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_METHOD_FIELD_NUMBER: _ClassVar[int]
    rrn: str
    amount_cents: int
    payment_method: str
    def __init__(self, rrn: _Optional[str] = ..., amount_cents: _Optional[int] = ..., payment_method: _Optional[str] = ...) -> None: ...

class AddressContext(_message.Message):
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

class CustomerContext(_message.Message):
    __slots__ = ("customer_id", "previous_order_count", "account_created_at")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_ORDER_COUNT_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    previous_order_count: int
    account_created_at: _timestamp_pb2.Timestamp
    def __init__(self, customer_id: _Optional[str] = ..., previous_order_count: _Optional[int] = ..., account_created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class PerformFraudCheckRequest(_message.Message):
    __slots__ = ("context",)
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    context: FraudCheckContext
    def __init__(self, context: _Optional[_Union[FraudCheckContext, _Mapping]] = ...) -> None: ...

class PerformFraudCheckResponse(_message.Message):
    __slots__ = ("passed", "risk_score", "flags", "recommendation")
    PASSED_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    passed: bool
    risk_score: float
    flags: _containers.RepeatedScalarFieldContainer[str]
    recommendation: str
    def __init__(self, passed: _Optional[bool] = ..., risk_score: _Optional[float] = ..., flags: _Optional[_Iterable[str]] = ..., recommendation: _Optional[str] = ...) -> None: ...

class CheckAddressFraudRequest(_message.Message):
    __slots__ = ("address",)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: AddressContext
    def __init__(self, address: _Optional[_Union[AddressContext, _Mapping]] = ...) -> None: ...

class CheckAddressFraudResponse(_message.Message):
    __slots__ = ("is_fraudulent", "address_risk_score", "flags")
    IS_FRAUDULENT_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    is_fraudulent: bool
    address_risk_score: float
    flags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, is_fraudulent: _Optional[bool] = ..., address_risk_score: _Optional[float] = ..., flags: _Optional[_Iterable[str]] = ...) -> None: ...

class CheckPaymentFraudRequest(_message.Message):
    __slots__ = ("payment", "customer_id")
    PAYMENT_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    payment: PaymentContext
    customer_id: str
    def __init__(self, payment: _Optional[_Union[PaymentContext, _Mapping]] = ..., customer_id: _Optional[str] = ...) -> None: ...

class CheckPaymentFraudResponse(_message.Message):
    __slots__ = ("is_fraudulent", "payment_risk_score", "flags")
    IS_FRAUDULENT_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    is_fraudulent: bool
    payment_risk_score: float
    flags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, is_fraudulent: _Optional[bool] = ..., payment_risk_score: _Optional[float] = ..., flags: _Optional[_Iterable[str]] = ...) -> None: ...

class GetCustomerRiskProfileRequest(_message.Message):
    __slots__ = ("customer_id",)
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    def __init__(self, customer_id: _Optional[str] = ...) -> None: ...

class GetCustomerRiskProfileResponse(_message.Message):
    __slots__ = ("customer_id", "historical_risk_score", "fraud_incident_count", "successful_order_count", "last_order_at")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    HISTORICAL_RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    FRAUD_INCIDENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    SUCCESSFUL_ORDER_COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_ORDER_AT_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    historical_risk_score: float
    fraud_incident_count: int
    successful_order_count: int
    last_order_at: _timestamp_pb2.Timestamp
    def __init__(self, customer_id: _Optional[str] = ..., historical_risk_score: _Optional[float] = ..., fraud_incident_count: _Optional[int] = ..., successful_order_count: _Optional[int] = ..., last_order_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
