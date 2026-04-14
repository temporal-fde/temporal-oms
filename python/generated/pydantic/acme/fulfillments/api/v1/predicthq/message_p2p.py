# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
import typing

class EventState(IntEnum):
    """
     EventState is the lifecycle state of a PredictHQ event.
    """
    EVENT_STATE_UNSPECIFIED = 0
    EVENT_STATE_ACTIVE = 1
    EVENT_STATE_DELETED = 2
    EVENT_STATE_PREDICTED = 3


class EventCategory(IntEnum):
    """
     EventCategory is the broad classification of an event.
    """
    EVENT_CATEGORY_UNSPECIFIED = 0
    EVENT_CATEGORY_ACADEMIC = 1
    EVENT_CATEGORY_SCHOOL_HOLIDAYS = 2
    EVENT_CATEGORY_PUBLIC_HOLIDAYS = 3
    EVENT_CATEGORY_OBSERVANCES = 4
    EVENT_CATEGORY_POLITICS = 5
    EVENT_CATEGORY_CONFERENCES = 6
    EVENT_CATEGORY_EXPOS = 7
    EVENT_CATEGORY_CONCERTS = 8
    EVENT_CATEGORY_FESTIVALS = 9
    EVENT_CATEGORY_PERFORMING_ARTS = 10
    EVENT_CATEGORY_SPORTS = 11
    EVENT_CATEGORY_COMMUNITY = 12
    EVENT_CATEGORY_DAYLIGHT_SAVINGS = 13
    EVENT_CATEGORY_AIRPORT_DELAYS = 14
    EVENT_CATEGORY_SEVERE_WEATHER = 15
    EVENT_CATEGORY_DISASTERS = 16
    EVENT_CATEGORY_TERROR = 17
    EVENT_CATEGORY_HEALTH_WARNINGS = 18


class GeographicScope(IntEnum):
    """
     GeographicScope is the geographic granularity of an event's location.
    """
    GEOGRAPHIC_SCOPE_UNSPECIFIED = 0
    GEOGRAPHIC_SCOPE_LOCALITY = 1
    GEOGRAPHIC_SCOPE_LOCALADMIN = 2
    GEOGRAPHIC_SCOPE_COUNTY = 3
    GEOGRAPHIC_SCOPE_REGION = 4
    GEOGRAPHIC_SCOPE_COUNTRY = 5


class DeletedReason(IntEnum):
    """
     DeletedReason indicates why an event record was removed.
    """
    DELETED_REASON_UNSPECIFIED = 0
    DELETED_REASON_CANCELLED = 1
    DELETED_REASON_INVALID = 2
    DELETED_REASON_DUPLICATE = 3
    DELETED_REASON_POSTPONED = 4


class ImpactType(IntEnum):
    """
     ImpactType is the metric used for impact pattern calculations.
    """
    IMPACT_TYPE_UNSPECIFIED = 0
    IMPACT_TYPE_PHQ_RANK = 1
    IMPACT_TYPE_PHQ_ATTENDANCE = 2
    IMPACT_TYPE_PHQ_IMPACT = 3


class ImpactPosition(IntEnum):
    """
     ImpactPosition is the temporal relationship of an industry impact to the event.
    """
    IMPACT_POSITION_UNSPECIFIED = 0
    IMPACT_POSITION_LEADING = 1
    IMPACT_POSITION_EVENT_DAY = 2
    IMPACT_POSITION_LAGGING = 3

class GeoCoordinate(BaseModel):
    """
     GeoCoordinate is a [longitude, latitude] pair (WGS-84 decimal degrees).
    """

    longitude: float = Field(default=0.0)
    latitude: float = Field(default=0.0)

class GeoRing(BaseModel):
    """
     GeoRing is an ordered list of coordinates forming a closed linear ring
 (exterior boundary or interior hole of a polygon).
    """

    coordinates: typing.List[GeoCoordinate] = Field(default_factory=list)

class GeoPolygonShape(BaseModel):
    """
     GeoPolygonShape is a GeoJSON Polygon: exterior ring followed by zero or
 more interior rings (holes).
    """

    rings: typing.List[GeoRing] = Field(default_factory=list)

class GeoMultiPolygon(BaseModel):
    """
     GeoMultiPolygon holds multiple discrete polygon shapes.
    """

    polygons: typing.List[GeoPolygonShape] = Field(default_factory=list)

class GeoCoordinateList(BaseModel):
    """
     GeoCoordinateList is a flat list of coordinates (MultiPoint / LineString).
    """

    coordinates: typing.List[GeoCoordinate] = Field(default_factory=list)

class GeoGeometry(BaseModel):
    """
     GeoGeometry is a GeoJSON geometry object. Exactly one variant is set.
    """

    _one_of_dict = {"GeoGeometry.geometry": {"fields": {"line_string", "multi_point", "multi_polygon", "point", "polygon"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    point: GeoCoordinate = Field(default_factory=GeoCoordinate)
# MultiPoint: an unordered collection of positions.
    multi_point: GeoCoordinateList = Field(default_factory=GeoCoordinateList)
# LineString: a sequence of two or more positions.
    line_string: GeoCoordinateList = Field(default_factory=GeoCoordinateList)
    polygon: GeoPolygonShape = Field(default_factory=GeoPolygonShape)
    multi_polygon: GeoMultiPolygon = Field(default_factory=GeoMultiPolygon)

class Address(BaseModel):
    """
     Address is a structured civic/postal address.
    """

# ISO 3166-1 alpha-2 country code.
    country_code: str = Field(default="")
    formatted_address: str = Field(default="")
    locality: str = Field(default="")
    region: str = Field(default="")
    postcode: str = Field(default="")

class Geo(BaseModel):
    """
     Geo contains geographic data associated with an event location.
    """

    geometry: GeoGeometry = Field(default_factory=GeoGeometry)
# Placekey in "what@where" format.
    placekey: str = Field(default="")
    address: Address = Field(default_factory=Address)

class PlaceHierarchy(BaseModel):
    """
     PlaceHierarchy holds an ordered sequence of Geonames place IDs from
 finest scope (locality) to broadest (country).
    """

    place_ids: typing.List[str] = Field(default_factory=list)

class PhqLabel(BaseModel):
    """
     PhqLabel is an AI-derived semantic label with a confidence weight.
 Weights across all labels for a given event sum to 1.0.
    """

    label: str = Field(default="")
# Confidence in the range [0.0, 1.0].
    weight: float = Field(default=0.0)

class SpendByIndustry(BaseModel):
    """
     SpendByIndustry breaks down predicted event spend (USD) by industry vertical.
    """

    accommodation: int = Field(default=0)
    hospitality: int = Field(default=0)
    transportation: int = Field(default=0)

class ImpactPatternDay(BaseModel):
    """
     ImpactPatternDay is the per-day impact value relative to an event.
    """

# Calendar date in ISO 8601 format (e.g. "2024-01-15") in event local time.
    date: str = Field(default="")
    value: int = Field(default=0)

class ImpactPattern(BaseModel):
    """
     ImpactPattern describes how a specific industry is impacted around an event,
 broken down by day and position relative to the event.
    """

    model_config = ConfigDict(validate_default=True)
    industry: str = Field(default="")
    impact_type: ImpactType = Field(default=0)
    position: ImpactPosition = Field(default=0)
    days: typing.List[ImpactPatternDay] = Field(default_factory=list)

class Entity(BaseModel):
    """
     Entity is an object associated with an event (venue, performer, organizer, airport).
    """

    entity_id: str = Field(default="")
    name: str = Field(default="")
# Broad type: organization, venue, person, airport.
    type: str = Field(default="")
# Narrower categorization within the type; may be absent.
    category: typing.Optional[str] = Field(default="")

class ParentEvent(BaseModel):
    """
     ParentEvent links a sub-event to its parent series or recurring event.
    """

    parent_event_id: str = Field(default="")

class Event(BaseModel):
    """
     Event is the primary PredictHQ event record.
    """

    model_config = ConfigDict(validate_default=True)
# --- Identifiers & metadata ---
    id: str = Field(default="")
    title: str = Field(default="")
    description: typing.Optional[str] = Field(default="")
    state: EventState = Field(default=0)
# --- Temporal fields ---
# start / end are UTC absolute timestamps.
    start: typing.Optional[datetime] = Field(default_factory=datetime.now)
    end: typing.Optional[datetime] = Field(default_factory=datetime.now)
# start_local / end_local are wall-clock times in the event's local timezone.
# Stored as ISO 8601 strings without offset (e.g. "2024-01-15T10:00:00").
    start_local: typing.Optional[str] = Field(default="")
    end_local: typing.Optional[str] = Field(default="")
# Duration in seconds.
    duration: int = Field(default=0)
# IANA TZ Database identifier (e.g. "America/New_York").
    timezone: str = Field(default="")
# predicted_end is a UTC timestamp; predicted_end_local is a local wall-clock string.
    predicted_end: typing.Optional[datetime] = Field(default_factory=datetime.now)
    predicted_end_local: typing.Optional[str] = Field(default="")
    cancelled: typing.Optional[datetime] = Field(default_factory=datetime.now)
    postponed: typing.Optional[datetime] = Field(default_factory=datetime.now)
    first_seen: datetime = Field(default_factory=datetime.now)
    updated: datetime = Field(default_factory=datetime.now)
# --- Geographic data ---
# ISO 3166-1 alpha-2 country code.
    country: str = Field(default="")
    scope: GeographicScope = Field(default=0)
# Deprecated: legacy [longitude, latitude] pair. Use geo instead.
    location: typing.List[float] = Field(default_factory=list)
    geo: typing.Optional[Geo] = Field(default_factory=Geo)
    place_hierarchies: typing.List[PlaceHierarchy] = Field(default_factory=list)
# --- Categorization ---
    category: EventCategory = Field(default=0)
# Deprecated: unstructured label strings. Use phq_labels instead.
    labels: typing.List[str] = Field(default_factory=list)
    phq_labels: typing.List[PhqLabel] = Field(default_factory=list)
# --- Impact metrics ---
# PredictHQ Rank: overall event significance (0–100).
    rank: int = Field(default=0)
# Local Rank: significance within the local area (0–100); absent for some events.
    local_rank: typing.Optional[int] = Field(default=0)
    phq_attendance: int = Field(default=0)
# Predicted total event spend in USD.
    predicted_event_spend: int = Field(default=0)
    predicted_event_spend_industries: SpendByIndustry = Field(default_factory=SpendByIndustry)
    impact_patterns: typing.List[ImpactPattern] = Field(default_factory=list)
# --- Quality indicators ---
    brand_safe: bool = Field(default=False)
# Location confidence score (1 = low, 5 = high).
    location_confidence_score: int = Field(default=0)
# Start-date confidence score (1 = low, 5 = high).
    start_date_confidence_score: int = Field(default=0)
# --- Deletion metadata ---
    deleted_reason: typing.Optional[DeletedReason] = Field(default=0)
    duplicate_of_id: typing.Optional[str] = Field(default="")
# --- Relationships ---
    entities: typing.List[Entity] = Field(default_factory=list)
    parent_event: typing.Optional[ParentEvent] = Field(default_factory=ParentEvent)

class EventsResponse(BaseModel):
    """
     EventsResponse is the paginated list envelope returned by the Events API.
    """

# Total number of matching events across all pages.
    count: int = Field(default=0)
# True when the total result count exceeds the subscription's page limit.
    overflow: bool = Field(default=False)
# URL of the previous results page; empty string when on the first page.
    previous: str = Field(default="")
# URL of the next results page; empty string when on the last page.
    next: str = Field(default="")
    results: typing.List[Event] = Field(default_factory=list)
