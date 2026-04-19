# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from ....common.v1.values_p2p import Address
from ....common.v1.values_p2p import Coordinate
from ....common.v1.values_p2p import Money
from .values_p2p import LocationEvent
from .values_p2p import LocationRiskSummary
from .values_p2p import RiskLevel
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class RecommendationOutcome(IntEnum):
    """
     RecommendationOutcome is the LLM's decision about the shipping situation.
    """
    RECOMMENDATION_OUTCOME_UNSPECIFIED = 0
    PROCEED = 1
    CHEAPER_AVAILABLE = 2
    FASTER_AVAILABLE = 3
    MARGIN_SPIKE = 4
    SLA_BREACH = 5

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

class ShippingLineItem(BaseModel):
    """
     ShippingLineItem is a sku/quantity pair for shipping rate calculation.
 Simpler than FulfillmentItem (which carries warehouse/brand fields irrelevant to rate calculation).
    """

    sku_id: str = Field(default="")
    quantity: int = Field(default=0)

class ShippingOption(BaseModel):
    """
     ShippingOption is a single carrier rate returned by get_carrier_rates.
 id is set to rate_id so the LLM can cross-reference recommended_option_id back to the rate.
    """

    id: str = Field(default="")
    carrier: str = Field(default="")
    service_level: str = Field(default="")
    cost: Money = Field(default_factory=Money)
    estimated_days: int = Field(default=0)
    rate_id: str = Field(default="")

class ShippingRecommendation(BaseModel):
    """
     ShippingRecommendation is the structured output from the ShippingAgent agentic loop.
 The agent recommends; fulfillment.Order decides what to do with the recommendation.
    """

    model_config = ConfigDict(validate_default=True)
    outcome: RecommendationOutcome = Field(default=0)
    recommended_option_id: str = Field(default="")
    reasoning: str = Field(default="")# LLM explanation for logging and support visibility
    margin_delta_cents: int = Field(default=0)# positive = over margin, negative = savings
    origin_risk_level: RiskLevel = Field(default=0)
    destination_risk_level: RiskLevel = Field(default=0)

class ShippingAgentExecutionOptions(BaseModel):
    cache_ttl_secs: typing.Optional[int] = Field(default=0)# default 1800 (30 minutes)

class StartShippingAgentRequest(BaseModel):
    """
     The Shipping Agent (Workflow) args
 WorkflowID is customer_id — one long-running agent per customer, caching across calls.
    """

    execution_options: typing.Optional[ShippingAgentExecutionOptions] = Field(default_factory=ShippingAgentExecutionOptions)
    customer_id: str = Field(default="")

class CalculateShippingOptionsRequest(BaseModel):
    """
     CalculateShippingOptionsRequest is the Update input for the ShippingAgent agentic loop.
 Two call paths use the same message:
   Fulfillment path: from_address is provided with easypost_address already populated
                     (pre-resolved from EnrichedItem; warehouse addresses are pre-verified).
   Cart/UI path: from_address absent; LLM calls lookup_inventory_location, which returns
                 an Address with easypost_address pre-populated from seed data.
 Cache key is derived from from_address.easypost_address.id in both paths — symmetric
 with to_address, which also carries easypost_address from fulfillment.Order validateOrder.
    """

    order_id: str = Field(default="")
    customer_id: str = Field(default="")
# to_address: easypost_address pre-populated by fulfillment.Order validateOrder.
    to_address: Address = Field(default_factory=Address)
    items: typing.List[ShippingLineItem] = Field(default_factory=list)
# from_address: warehouse origin with easypost_address populated (fulfillment path);
# absent in cart path — LLM resolves via lookup_inventory_location.
    from_address: typing.Optional[Address] = Field(default_factory=Address)
    selected_shipping_option_id: typing.Optional[str] = Field(default="")
    customer_paid_price: typing.Optional[Money] = Field(default_factory=Money)
    transit_days_sla: typing.Optional[int] = Field(default=0)

class CalculateShippingOptionsResponse(BaseModel):
    """
     CalculateShippingOptionsResponse is the Update response from the ShippingAgent.
    """

    recommendation: ShippingRecommendation = Field(default_factory=ShippingRecommendation)
    options: typing.List[ShippingOption] = Field(default_factory=list)
    cache_hit: bool = Field(default=False)

class ShippingOptionsResult(BaseModel):
    """
     ShippingOptionsResult is a single cached calculation result.
    """

    recommendation: ShippingRecommendation = Field(default_factory=ShippingRecommendation)
    options: typing.List[ShippingOption] = Field(default_factory=list)
    cached_at: datetime = Field(default_factory=datetime.now)

class ShippingOptionsCache(BaseModel):
    """
     ShippingOptionsCache is the get_options Query return type.
 Keyed by content hash of (from_address.easypost_address.id, sorted items, postal_code, country).
    """

    results: "typing.Dict[str, ShippingOptionsResult]" = Field(default_factory=dict)

class LookupInventoryLocationRequest(BaseModel):
    """
     LookupInventoryLocationRequest resolves sku_ids to a warehouse address.
 V1: static config lookup; future: Inventory Locations service.
    """

    items: typing.List[ShippingLineItem] = Field(default_factory=list)
    location_id: typing.Optional[str] = Field(default="")# if present, return matching warehouse directly

class LookupInventoryLocationResponse(BaseModel):
    """
     LookupInventoryLocationResponse returns the resolved warehouse address.
 address.easypost_address is pre-populated from inventory seed data — warehouse addresses
 are pre-verified so the LLM can use easypost_address.id directly without calling verify_address.
    """

    address: Address = Field(default_factory=Address)

class GetShippingRatesRequest(BaseModel):
    """
     GetShippingRatesRequest creates an EasyPost Shipment and retrieves available carrier rates.
 Distinct from Java's GetCarrierRatesRequest — no parcel fields (V1 hardcodes default parcel
 in the activity: 1 lb, 6×6×4 in).
    """

    from_easypost_id: str = Field(default="")
    to_easypost_id: str = Field(default="")
    items: typing.List[ShippingLineItem] = Field(default_factory=list)

class GetShippingRatesResponse(BaseModel):
    shipment_id: str = Field(default="")
    options: typing.List[ShippingOption] = Field(default_factory=list)
