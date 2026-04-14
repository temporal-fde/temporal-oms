import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_STATE_UNSPECIFIED: _ClassVar[EventState]
    EVENT_STATE_ACTIVE: _ClassVar[EventState]
    EVENT_STATE_DELETED: _ClassVar[EventState]
    EVENT_STATE_PREDICTED: _ClassVar[EventState]

class EventCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EVENT_CATEGORY_UNSPECIFIED: _ClassVar[EventCategory]
    EVENT_CATEGORY_ACADEMIC: _ClassVar[EventCategory]
    EVENT_CATEGORY_SCHOOL_HOLIDAYS: _ClassVar[EventCategory]
    EVENT_CATEGORY_PUBLIC_HOLIDAYS: _ClassVar[EventCategory]
    EVENT_CATEGORY_OBSERVANCES: _ClassVar[EventCategory]
    EVENT_CATEGORY_POLITICS: _ClassVar[EventCategory]
    EVENT_CATEGORY_CONFERENCES: _ClassVar[EventCategory]
    EVENT_CATEGORY_EXPOS: _ClassVar[EventCategory]
    EVENT_CATEGORY_CONCERTS: _ClassVar[EventCategory]
    EVENT_CATEGORY_FESTIVALS: _ClassVar[EventCategory]
    EVENT_CATEGORY_PERFORMING_ARTS: _ClassVar[EventCategory]
    EVENT_CATEGORY_SPORTS: _ClassVar[EventCategory]
    EVENT_CATEGORY_COMMUNITY: _ClassVar[EventCategory]
    EVENT_CATEGORY_DAYLIGHT_SAVINGS: _ClassVar[EventCategory]
    EVENT_CATEGORY_AIRPORT_DELAYS: _ClassVar[EventCategory]
    EVENT_CATEGORY_SEVERE_WEATHER: _ClassVar[EventCategory]
    EVENT_CATEGORY_DISASTERS: _ClassVar[EventCategory]
    EVENT_CATEGORY_TERROR: _ClassVar[EventCategory]
    EVENT_CATEGORY_HEALTH_WARNINGS: _ClassVar[EventCategory]

class GeographicScope(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GEOGRAPHIC_SCOPE_UNSPECIFIED: _ClassVar[GeographicScope]
    GEOGRAPHIC_SCOPE_LOCALITY: _ClassVar[GeographicScope]
    GEOGRAPHIC_SCOPE_LOCALADMIN: _ClassVar[GeographicScope]
    GEOGRAPHIC_SCOPE_COUNTY: _ClassVar[GeographicScope]
    GEOGRAPHIC_SCOPE_REGION: _ClassVar[GeographicScope]
    GEOGRAPHIC_SCOPE_COUNTRY: _ClassVar[GeographicScope]

class DeletedReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DELETED_REASON_UNSPECIFIED: _ClassVar[DeletedReason]
    DELETED_REASON_CANCELLED: _ClassVar[DeletedReason]
    DELETED_REASON_INVALID: _ClassVar[DeletedReason]
    DELETED_REASON_DUPLICATE: _ClassVar[DeletedReason]
    DELETED_REASON_POSTPONED: _ClassVar[DeletedReason]

class ImpactType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    IMPACT_TYPE_UNSPECIFIED: _ClassVar[ImpactType]
    IMPACT_TYPE_PHQ_RANK: _ClassVar[ImpactType]
    IMPACT_TYPE_PHQ_ATTENDANCE: _ClassVar[ImpactType]
    IMPACT_TYPE_PHQ_IMPACT: _ClassVar[ImpactType]

class ImpactPosition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    IMPACT_POSITION_UNSPECIFIED: _ClassVar[ImpactPosition]
    IMPACT_POSITION_LEADING: _ClassVar[ImpactPosition]
    IMPACT_POSITION_EVENT_DAY: _ClassVar[ImpactPosition]
    IMPACT_POSITION_LAGGING: _ClassVar[ImpactPosition]
EVENT_STATE_UNSPECIFIED: EventState
EVENT_STATE_ACTIVE: EventState
EVENT_STATE_DELETED: EventState
EVENT_STATE_PREDICTED: EventState
EVENT_CATEGORY_UNSPECIFIED: EventCategory
EVENT_CATEGORY_ACADEMIC: EventCategory
EVENT_CATEGORY_SCHOOL_HOLIDAYS: EventCategory
EVENT_CATEGORY_PUBLIC_HOLIDAYS: EventCategory
EVENT_CATEGORY_OBSERVANCES: EventCategory
EVENT_CATEGORY_POLITICS: EventCategory
EVENT_CATEGORY_CONFERENCES: EventCategory
EVENT_CATEGORY_EXPOS: EventCategory
EVENT_CATEGORY_CONCERTS: EventCategory
EVENT_CATEGORY_FESTIVALS: EventCategory
EVENT_CATEGORY_PERFORMING_ARTS: EventCategory
EVENT_CATEGORY_SPORTS: EventCategory
EVENT_CATEGORY_COMMUNITY: EventCategory
EVENT_CATEGORY_DAYLIGHT_SAVINGS: EventCategory
EVENT_CATEGORY_AIRPORT_DELAYS: EventCategory
EVENT_CATEGORY_SEVERE_WEATHER: EventCategory
EVENT_CATEGORY_DISASTERS: EventCategory
EVENT_CATEGORY_TERROR: EventCategory
EVENT_CATEGORY_HEALTH_WARNINGS: EventCategory
GEOGRAPHIC_SCOPE_UNSPECIFIED: GeographicScope
GEOGRAPHIC_SCOPE_LOCALITY: GeographicScope
GEOGRAPHIC_SCOPE_LOCALADMIN: GeographicScope
GEOGRAPHIC_SCOPE_COUNTY: GeographicScope
GEOGRAPHIC_SCOPE_REGION: GeographicScope
GEOGRAPHIC_SCOPE_COUNTRY: GeographicScope
DELETED_REASON_UNSPECIFIED: DeletedReason
DELETED_REASON_CANCELLED: DeletedReason
DELETED_REASON_INVALID: DeletedReason
DELETED_REASON_DUPLICATE: DeletedReason
DELETED_REASON_POSTPONED: DeletedReason
IMPACT_TYPE_UNSPECIFIED: ImpactType
IMPACT_TYPE_PHQ_RANK: ImpactType
IMPACT_TYPE_PHQ_ATTENDANCE: ImpactType
IMPACT_TYPE_PHQ_IMPACT: ImpactType
IMPACT_POSITION_UNSPECIFIED: ImpactPosition
IMPACT_POSITION_LEADING: ImpactPosition
IMPACT_POSITION_EVENT_DAY: ImpactPosition
IMPACT_POSITION_LAGGING: ImpactPosition

class GeoCoordinate(_message.Message):
    __slots__ = ("longitude", "latitude")
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    longitude: float
    latitude: float
    def __init__(self, longitude: _Optional[float] = ..., latitude: _Optional[float] = ...) -> None: ...

class GeoRing(_message.Message):
    __slots__ = ("coordinates",)
    COORDINATES_FIELD_NUMBER: _ClassVar[int]
    coordinates: _containers.RepeatedCompositeFieldContainer[GeoCoordinate]
    def __init__(self, coordinates: _Optional[_Iterable[_Union[GeoCoordinate, _Mapping]]] = ...) -> None: ...

class GeoPolygonShape(_message.Message):
    __slots__ = ("rings",)
    RINGS_FIELD_NUMBER: _ClassVar[int]
    rings: _containers.RepeatedCompositeFieldContainer[GeoRing]
    def __init__(self, rings: _Optional[_Iterable[_Union[GeoRing, _Mapping]]] = ...) -> None: ...

class GeoMultiPolygon(_message.Message):
    __slots__ = ("polygons",)
    POLYGONS_FIELD_NUMBER: _ClassVar[int]
    polygons: _containers.RepeatedCompositeFieldContainer[GeoPolygonShape]
    def __init__(self, polygons: _Optional[_Iterable[_Union[GeoPolygonShape, _Mapping]]] = ...) -> None: ...

class GeoGeometry(_message.Message):
    __slots__ = ("point", "multi_point", "line_string", "polygon", "multi_polygon")
    POINT_FIELD_NUMBER: _ClassVar[int]
    MULTI_POINT_FIELD_NUMBER: _ClassVar[int]
    LINE_STRING_FIELD_NUMBER: _ClassVar[int]
    POLYGON_FIELD_NUMBER: _ClassVar[int]
    MULTI_POLYGON_FIELD_NUMBER: _ClassVar[int]
    point: GeoCoordinate
    multi_point: GeoCoordinateList
    line_string: GeoCoordinateList
    polygon: GeoPolygonShape
    multi_polygon: GeoMultiPolygon
    def __init__(self, point: _Optional[_Union[GeoCoordinate, _Mapping]] = ..., multi_point: _Optional[_Union[GeoCoordinateList, _Mapping]] = ..., line_string: _Optional[_Union[GeoCoordinateList, _Mapping]] = ..., polygon: _Optional[_Union[GeoPolygonShape, _Mapping]] = ..., multi_polygon: _Optional[_Union[GeoMultiPolygon, _Mapping]] = ...) -> None: ...

class GeoCoordinateList(_message.Message):
    __slots__ = ("coordinates",)
    COORDINATES_FIELD_NUMBER: _ClassVar[int]
    coordinates: _containers.RepeatedCompositeFieldContainer[GeoCoordinate]
    def __init__(self, coordinates: _Optional[_Iterable[_Union[GeoCoordinate, _Mapping]]] = ...) -> None: ...

class Address(_message.Message):
    __slots__ = ("country_code", "formatted_address", "locality", "region", "postcode")
    COUNTRY_CODE_FIELD_NUMBER: _ClassVar[int]
    FORMATTED_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    LOCALITY_FIELD_NUMBER: _ClassVar[int]
    REGION_FIELD_NUMBER: _ClassVar[int]
    POSTCODE_FIELD_NUMBER: _ClassVar[int]
    country_code: str
    formatted_address: str
    locality: str
    region: str
    postcode: str
    def __init__(self, country_code: _Optional[str] = ..., formatted_address: _Optional[str] = ..., locality: _Optional[str] = ..., region: _Optional[str] = ..., postcode: _Optional[str] = ...) -> None: ...

class Geo(_message.Message):
    __slots__ = ("geometry", "placekey", "address")
    GEOMETRY_FIELD_NUMBER: _ClassVar[int]
    PLACEKEY_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    geometry: GeoGeometry
    placekey: str
    address: Address
    def __init__(self, geometry: _Optional[_Union[GeoGeometry, _Mapping]] = ..., placekey: _Optional[str] = ..., address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class PlaceHierarchy(_message.Message):
    __slots__ = ("place_ids",)
    PLACE_IDS_FIELD_NUMBER: _ClassVar[int]
    place_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, place_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class PhqLabel(_message.Message):
    __slots__ = ("label", "weight")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    label: str
    weight: float
    def __init__(self, label: _Optional[str] = ..., weight: _Optional[float] = ...) -> None: ...

class SpendByIndustry(_message.Message):
    __slots__ = ("accommodation", "hospitality", "transportation")
    ACCOMMODATION_FIELD_NUMBER: _ClassVar[int]
    HOSPITALITY_FIELD_NUMBER: _ClassVar[int]
    TRANSPORTATION_FIELD_NUMBER: _ClassVar[int]
    accommodation: int
    hospitality: int
    transportation: int
    def __init__(self, accommodation: _Optional[int] = ..., hospitality: _Optional[int] = ..., transportation: _Optional[int] = ...) -> None: ...

class ImpactPatternDay(_message.Message):
    __slots__ = ("date", "value")
    DATE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    date: str
    value: int
    def __init__(self, date: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...

class ImpactPattern(_message.Message):
    __slots__ = ("industry", "impact_type", "position", "days")
    INDUSTRY_FIELD_NUMBER: _ClassVar[int]
    IMPACT_TYPE_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    DAYS_FIELD_NUMBER: _ClassVar[int]
    industry: str
    impact_type: ImpactType
    position: ImpactPosition
    days: _containers.RepeatedCompositeFieldContainer[ImpactPatternDay]
    def __init__(self, industry: _Optional[str] = ..., impact_type: _Optional[_Union[ImpactType, str]] = ..., position: _Optional[_Union[ImpactPosition, str]] = ..., days: _Optional[_Iterable[_Union[ImpactPatternDay, _Mapping]]] = ...) -> None: ...

class Entity(_message.Message):
    __slots__ = ("entity_id", "name", "type", "category")
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    entity_id: str
    name: str
    type: str
    category: str
    def __init__(self, entity_id: _Optional[str] = ..., name: _Optional[str] = ..., type: _Optional[str] = ..., category: _Optional[str] = ...) -> None: ...

class ParentEvent(_message.Message):
    __slots__ = ("parent_event_id",)
    PARENT_EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    parent_event_id: str
    def __init__(self, parent_event_id: _Optional[str] = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ("id", "title", "description", "state", "start", "end", "start_local", "end_local", "duration", "timezone", "predicted_end", "predicted_end_local", "cancelled", "postponed", "first_seen", "updated", "country", "scope", "location", "geo", "place_hierarchies", "category", "labels", "phq_labels", "rank", "local_rank", "phq_attendance", "predicted_event_spend", "predicted_event_spend_industries", "impact_patterns", "brand_safe", "location_confidence_score", "start_date_confidence_score", "deleted_reason", "duplicate_of_id", "entities", "parent_event")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    START_LOCAL_FIELD_NUMBER: _ClassVar[int]
    END_LOCAL_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_END_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_END_LOCAL_FIELD_NUMBER: _ClassVar[int]
    CANCELLED_FIELD_NUMBER: _ClassVar[int]
    POSTPONED_FIELD_NUMBER: _ClassVar[int]
    FIRST_SEEN_FIELD_NUMBER: _ClassVar[int]
    UPDATED_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    GEO_FIELD_NUMBER: _ClassVar[int]
    PLACE_HIERARCHIES_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    PHQ_LABELS_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    LOCAL_RANK_FIELD_NUMBER: _ClassVar[int]
    PHQ_ATTENDANCE_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_EVENT_SPEND_FIELD_NUMBER: _ClassVar[int]
    PREDICTED_EVENT_SPEND_INDUSTRIES_FIELD_NUMBER: _ClassVar[int]
    IMPACT_PATTERNS_FIELD_NUMBER: _ClassVar[int]
    BRAND_SAFE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_CONFIDENCE_SCORE_FIELD_NUMBER: _ClassVar[int]
    START_DATE_CONFIDENCE_SCORE_FIELD_NUMBER: _ClassVar[int]
    DELETED_REASON_FIELD_NUMBER: _ClassVar[int]
    DUPLICATE_OF_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    PARENT_EVENT_FIELD_NUMBER: _ClassVar[int]
    id: str
    title: str
    description: str
    state: EventState
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    start_local: str
    end_local: str
    duration: int
    timezone: str
    predicted_end: _timestamp_pb2.Timestamp
    predicted_end_local: str
    cancelled: _timestamp_pb2.Timestamp
    postponed: _timestamp_pb2.Timestamp
    first_seen: _timestamp_pb2.Timestamp
    updated: _timestamp_pb2.Timestamp
    country: str
    scope: GeographicScope
    location: _containers.RepeatedScalarFieldContainer[float]
    geo: Geo
    place_hierarchies: _containers.RepeatedCompositeFieldContainer[PlaceHierarchy]
    category: EventCategory
    labels: _containers.RepeatedScalarFieldContainer[str]
    phq_labels: _containers.RepeatedCompositeFieldContainer[PhqLabel]
    rank: int
    local_rank: int
    phq_attendance: int
    predicted_event_spend: int
    predicted_event_spend_industries: SpendByIndustry
    impact_patterns: _containers.RepeatedCompositeFieldContainer[ImpactPattern]
    brand_safe: bool
    location_confidence_score: int
    start_date_confidence_score: int
    deleted_reason: DeletedReason
    duplicate_of_id: str
    entities: _containers.RepeatedCompositeFieldContainer[Entity]
    parent_event: ParentEvent
    def __init__(self, id: _Optional[str] = ..., title: _Optional[str] = ..., description: _Optional[str] = ..., state: _Optional[_Union[EventState, str]] = ..., start: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., start_local: _Optional[str] = ..., end_local: _Optional[str] = ..., duration: _Optional[int] = ..., timezone: _Optional[str] = ..., predicted_end: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., predicted_end_local: _Optional[str] = ..., cancelled: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., postponed: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., first_seen: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., country: _Optional[str] = ..., scope: _Optional[_Union[GeographicScope, str]] = ..., location: _Optional[_Iterable[float]] = ..., geo: _Optional[_Union[Geo, _Mapping]] = ..., place_hierarchies: _Optional[_Iterable[_Union[PlaceHierarchy, _Mapping]]] = ..., category: _Optional[_Union[EventCategory, str]] = ..., labels: _Optional[_Iterable[str]] = ..., phq_labels: _Optional[_Iterable[_Union[PhqLabel, _Mapping]]] = ..., rank: _Optional[int] = ..., local_rank: _Optional[int] = ..., phq_attendance: _Optional[int] = ..., predicted_event_spend: _Optional[int] = ..., predicted_event_spend_industries: _Optional[_Union[SpendByIndustry, _Mapping]] = ..., impact_patterns: _Optional[_Iterable[_Union[ImpactPattern, _Mapping]]] = ..., brand_safe: _Optional[bool] = ..., location_confidence_score: _Optional[int] = ..., start_date_confidence_score: _Optional[int] = ..., deleted_reason: _Optional[_Union[DeletedReason, str]] = ..., duplicate_of_id: _Optional[str] = ..., entities: _Optional[_Iterable[_Union[Entity, _Mapping]]] = ..., parent_event: _Optional[_Union[ParentEvent, _Mapping]] = ...) -> None: ...

class EventsResponse(_message.Message):
    __slots__ = ("count", "overflow", "previous", "next", "results")
    COUNT_FIELD_NUMBER: _ClassVar[int]
    OVERFLOW_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_FIELD_NUMBER: _ClassVar[int]
    NEXT_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    count: int
    overflow: bool
    previous: str
    next: str
    results: _containers.RepeatedCompositeFieldContainer[Event]
    def __init__(self, count: _Optional[int] = ..., overflow: _Optional[bool] = ..., previous: _Optional[str] = ..., next: _Optional[str] = ..., results: _Optional[_Iterable[_Union[Event, _Mapping]]] = ...) -> None: ...
