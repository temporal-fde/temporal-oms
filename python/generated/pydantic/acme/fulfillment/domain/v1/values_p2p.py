# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class Errors(IntEnum):
    ERROR_UNSPECIFIED = 0
    ERROR_UNAUTHORIZED = 1
    ERROR_FORBIDDEN = 2
    ERROR_BAD_REQUEST = 3
    ERROR_ADDRESS_VERIFY_FAILED = 4
    ERROR_INVALID_RATE = 5


class RiskLevel(IntEnum):
    """
     RiskLevel represents supply chain risk tiers the agent can reason about.
    """
    RISK_LEVEL_UNSPECIFIED = 0
    RISK_LEVEL_NONE = 1
    RISK_LEVEL_LOW = 2
    RISK_LEVEL_MODERATE = 3
    RISK_LEVEL_HIGH = 4
    RISK_LEVEL_CRITICAL = 5

class LocationEvent(BaseModel):
    """
     LocationEvent is a distilled event record for LLM risk reasoning.
 Fields are chosen for semantic clarity, not API completeness.
    """

    id: str = Field(default="")
    title: str = Field(default="")
    description: typing.Optional[str] = Field(default="")
# Event category string (e.g. "severe-weather", "airport-delays", "disasters").
    category: str = Field(default="")
# Rank (0–100): overall significance of the event.
    rank: int = Field(default=0)
    local_rank: typing.Optional[int] = Field(default=0)
# True when the event is unscheduled/emergent:
# severe-weather, disasters, terror, health-warnings, airport-delays.
    unscheduled: bool = Field(default=False)
    start: datetime = Field(default_factory=datetime.now)
    end: typing.Optional[datetime] = Field(default_factory=datetime.now)

class LocationRiskSummary(BaseModel):
    """
     LocationRiskSummary gives the agent a fast top-level read   before
 it reasons over individual events.
    """

    model_config = ConfigDict(validate_default=True)
    overall_risk_level: RiskLevel = Field(default=0)
# Rank of the single most significant event in the window (0–100).
    peak_rank: int = Field(default=0)
    total_event_count: int = Field(default=0)
    unscheduled_event_count: int = Field(default=0)
# Count of events per category string
# (e.g. {"severe-weather": 2, "airport-delays": 1}).
    events_by_category: "typing.Dict[str, int]" = Field(default_factory=dict)

class ShippingLineItem(BaseModel):
    """
     ShippingLineItem is a sku/quantity pair for shipping rate calculation.
 Simpler than FulfillmentItem (which carries warehouse/brand fields irrelevant to rate calculation).
    """

    sku_id: str = Field(default="")
    quantity: int = Field(default=0)
