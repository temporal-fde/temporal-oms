# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from ....common.v1.values_p2p import Address
from ....common.v1.values_p2p import Coordinate
from .values_p2p import LocationEvent
from .values_p2p import LocationRiskSummary
from datetime import datetime
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class GetLocationEventsRequest(BaseModel):
    """
     tool for agent to augment shipping rate comps
    """

# Destination coordinates from EasyPost address verification.
    coordinate: Coordinate = Field(default_factory=Coordinate)
# Radius around the destination to search for events.
# Value is in kilometers (e.g. 2.0).
    within_km: float = Field(default=0.0)
# Delivery window: events active at any point between ship and delivery dates.
# Maps to active.gte / active.lte on the PredictHQ Events API.
    active_from: datetime = Field(default_factory=datetime.now)# ship date
    active_to: datetime = Field(default_factory=datetime.now)# expected delivery date
# IANA TZ Database identifier for the destination (e.g. "America/New_York").
# From EasyPost verifications.delivery.details.time_zone.
# Maps to active.tz on the PredictHQ Events API.
    timezone: str = Field(default="")

class GetLocationEventsResponse(BaseModel):
    """
     GetLocationEventsResponse is the tool response for the ShippingAgent LLM.
 Contains factual event and risk data only — the agent determines implications.
    """

    summary: LocationRiskSummary = Field(default_factory=LocationRiskSummary)
    events: typing.List[LocationEvent] = Field(default_factory=list)
# Echo of the queried window and timezone for agent context.
    window_from: datetime = Field(default_factory=datetime.now)
    window_to: datetime = Field(default_factory=datetime.now)
    timezone: str = Field(default="")

class ShippingAgentExecutionOptions(BaseModel):
    pass

class StartShippingAgentRequest(BaseModel):
    """
     The Shipping Agent (Workflow) args
 Right now, we can think of this agent as correlating to a Customer
 but it is plausible we would get better spread out of having a WorkflowID of `Coordinate`.
    """

    execution_options: typing.Optional[ShippingAgentExecutionOptions] = Field(default_factory=ShippingAgentExecutionOptions)
    customer_id: str = Field(default="")

class CalculateShippingOptionsRequest(BaseModel):
    """
     Update-as-a-Query
    """

    address: typing.Optional[Address] = Field(default_factory=Address)
    coordinate: typing.Optional[Coordinate] = Field(default_factory=Coordinate)

class CalculateShippingOptionsResponse(BaseModel):#  TBD after EasyPost has landed
    pass
