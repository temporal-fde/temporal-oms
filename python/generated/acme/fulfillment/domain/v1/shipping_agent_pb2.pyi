import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from acme.fulfillment.domain.v1 import values_pb2 as _values_pb2
from acme.common.v1 import values_pb2 as _values_pb2_1
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RecommendationOutcome(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RECOMMENDATION_OUTCOME_UNSPECIFIED: _ClassVar[RecommendationOutcome]
    PROCEED: _ClassVar[RecommendationOutcome]
    CHEAPER_AVAILABLE: _ClassVar[RecommendationOutcome]
    FASTER_AVAILABLE: _ClassVar[RecommendationOutcome]
    MARGIN_SPIKE: _ClassVar[RecommendationOutcome]
    SLA_BREACH: _ClassVar[RecommendationOutcome]
RECOMMENDATION_OUTCOME_UNSPECIFIED: RecommendationOutcome
PROCEED: RecommendationOutcome
CHEAPER_AVAILABLE: RecommendationOutcome
FASTER_AVAILABLE: RecommendationOutcome
MARGIN_SPIKE: RecommendationOutcome
SLA_BREACH: RecommendationOutcome

class GetLocationEventsRequest(_message.Message):
    __slots__ = ()
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
    __slots__ = ()
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

class ShippingOption(_message.Message):
    __slots__ = ()
    ID_FIELD_NUMBER: _ClassVar[int]
    CARRIER_FIELD_NUMBER: _ClassVar[int]
    SERVICE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    COST_FIELD_NUMBER: _ClassVar[int]
    ESTIMATED_DAYS_FIELD_NUMBER: _ClassVar[int]
    RATE_ID_FIELD_NUMBER: _ClassVar[int]
    SHIPMENT_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    carrier: str
    service_level: str
    cost: _values_pb2_1.Money
    estimated_days: int
    rate_id: str
    shipment_id: str
    def __init__(self, id: _Optional[str] = ..., carrier: _Optional[str] = ..., service_level: _Optional[str] = ..., cost: _Optional[_Union[_values_pb2_1.Money, _Mapping]] = ..., estimated_days: _Optional[int] = ..., rate_id: _Optional[str] = ..., shipment_id: _Optional[str] = ...) -> None: ...

class ShippingRecommendation(_message.Message):
    __slots__ = ()
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_OPTION_ID_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    MARGIN_DELTA_CENTS_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    outcome: RecommendationOutcome
    recommended_option_id: str
    reasoning: str
    margin_delta_cents: int
    origin_risk_level: _values_pb2.RiskLevel
    destination_risk_level: _values_pb2.RiskLevel
    def __init__(self, outcome: _Optional[_Union[RecommendationOutcome, str]] = ..., recommended_option_id: _Optional[str] = ..., reasoning: _Optional[str] = ..., margin_delta_cents: _Optional[int] = ..., origin_risk_level: _Optional[_Union[_values_pb2.RiskLevel, str]] = ..., destination_risk_level: _Optional[_Union[_values_pb2.RiskLevel, str]] = ...) -> None: ...

class StartShippingAgentRequest(_message.Message):
    __slots__ = ()
    EXECUTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    execution_options: ShippingAgentExecutionOptions
    customer_id: str
    def __init__(self, execution_options: _Optional[_Union[ShippingAgentExecutionOptions, _Mapping]] = ..., customer_id: _Optional[str] = ...) -> None: ...

class ShippingAgentExecutionOptions(_message.Message):
    __slots__ = ()
    CACHE_TTL_SECS_FIELD_NUMBER: _ClassVar[int]
    cache_ttl_secs: int
    def __init__(self, cache_ttl_secs: _Optional[int] = ...) -> None: ...

class CalculateShippingOptionsRequest(_message.Message):
    __slots__ = ()
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    TO_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SELECTED_SHIPPING_OPTION_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_PAID_PRICE_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_DAYS_SLA_FIELD_NUMBER: _ClassVar[int]
    order_id: str
    customer_id: str
    to_address: _values_pb2_1.Address
    items: _containers.RepeatedCompositeFieldContainer[_values_pb2.ShippingLineItem]
    selected_shipping_option_id: str
    customer_paid_price: _values_pb2_1.Money
    delivery_days_sla: int
    def __init__(self, order_id: _Optional[str] = ..., customer_id: _Optional[str] = ..., to_address: _Optional[_Union[_values_pb2_1.Address, _Mapping]] = ..., items: _Optional[_Iterable[_Union[_values_pb2.ShippingLineItem, _Mapping]]] = ..., selected_shipping_option_id: _Optional[str] = ..., customer_paid_price: _Optional[_Union[_values_pb2_1.Money, _Mapping]] = ..., delivery_days_sla: _Optional[int] = ...) -> None: ...

class CalculateShippingOptionsResponse(_message.Message):
    __slots__ = ()
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    CACHE_HIT_FIELD_NUMBER: _ClassVar[int]
    recommendation: ShippingRecommendation
    options: _containers.RepeatedCompositeFieldContainer[ShippingOption]
    cache_hit: bool
    def __init__(self, recommendation: _Optional[_Union[ShippingRecommendation, _Mapping]] = ..., options: _Optional[_Iterable[_Union[ShippingOption, _Mapping]]] = ..., cache_hit: _Optional[bool] = ...) -> None: ...

class ShippingOptionsResult(_message.Message):
    __slots__ = ()
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    CACHED_AT_FIELD_NUMBER: _ClassVar[int]
    recommendation: ShippingRecommendation
    options: _containers.RepeatedCompositeFieldContainer[ShippingOption]
    cached_at: _timestamp_pb2.Timestamp
    def __init__(self, recommendation: _Optional[_Union[ShippingRecommendation, _Mapping]] = ..., options: _Optional[_Iterable[_Union[ShippingOption, _Mapping]]] = ..., cached_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ShippingOptionsCache(_message.Message):
    __slots__ = ()
    class ResultsEntry(_message.Message):
        __slots__ = ()
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ShippingOptionsResult
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ShippingOptionsResult, _Mapping]] = ...) -> None: ...
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.MessageMap[str, ShippingOptionsResult]
    def __init__(self, results: _Optional[_Mapping[str, ShippingOptionsResult]] = ...) -> None: ...

class GetShippingRatesRequest(_message.Message):
    __slots__ = ()
    FROM_EASYPOST_ID_FIELD_NUMBER: _ClassVar[int]
    TO_EASYPOST_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    from_easypost_id: str
    to_easypost_id: str
    items: _containers.RepeatedCompositeFieldContainer[_values_pb2.ShippingLineItem]
    def __init__(self, from_easypost_id: _Optional[str] = ..., to_easypost_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[_values_pb2.ShippingLineItem, _Mapping]]] = ...) -> None: ...

class GetShippingRatesResponse(_message.Message):
    __slots__ = ()
    SHIPMENT_ID_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    shipment_id: str
    options: _containers.RepeatedCompositeFieldContainer[ShippingOption]
    def __init__(self, shipment_id: _Optional[str] = ..., options: _Optional[_Iterable[_Union[ShippingOption, _Mapping]]] = ...) -> None: ...

class BuildSystemPromptRequest(_message.Message):
    __slots__ = ()
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    request: CalculateShippingOptionsRequest
    def __init__(self, request: _Optional[_Union[CalculateShippingOptionsRequest, _Mapping]] = ...) -> None: ...

class BuildSystemPromptResponse(_message.Message):
    __slots__ = ()
    SYSTEM_PROMPT_FIELD_NUMBER: _ClassVar[int]
    system_prompt: str
    def __init__(self, system_prompt: _Optional[str] = ...) -> None: ...
