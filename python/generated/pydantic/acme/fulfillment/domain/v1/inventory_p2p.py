# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from ....common.v1.values_p2p import Address
from .values_p2p import ShippingLineItem
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class StartInventoryRequest(BaseModel):
    pass

class LookupInventoryAddressRequest(BaseModel):
    """
     LookupInventoryAddressRequest resolves sku_ids to a warehouse address.
 V1: static config lookup; future: Inventory Locations service.
    """

    items: typing.List[ShippingLineItem] = Field(default_factory=list)
    address_id: typing.Optional[str] = Field(default="")# if present, return matching warehouse directly

class LookupInventoryAddressResponse(BaseModel):
    """
     LookupInventoryAddressResponse returns the resolved warehouse address.
 address.easypost_address is pre-populated from inventory seed data — warehouse addresses
 are pre-verified so the LLM can use easypost_address.id directly without calling verify_address.
    """

    address: Address = Field(default_factory=Address)

class FindAlternateWarehouseRequest(BaseModel):
    """
     FindAlternateWarehouseRequest asks for a warehouse that can fulfill the given
 items from a different address than the one already tried.
 V1: static config lookup; future: query Inventory Locations service and rank by proximity.
    """

    items: typing.List[ShippingLineItem] = Field(default_factory=list)
    current_address_id: str = Field(default="")# easypost_id of the origin already tried — excluded from results
    to_address_id: typing.Optional[str] = Field(default="")# destination easypost_id; V1 ignores, future ranks by proximity

class FindAlternateWarehouseResponse(BaseModel):
    """
     FindAlternateWarehouseResponse returns the best alternate warehouse address,
 or an empty address if no alternate is available.
 address.easypost_address is pre-populated so the agent can call get_carrier_rates directly.
    """

    address: typing.Optional[Address] = Field(default_factory=Address)# unset when no alternate warehouse exists
