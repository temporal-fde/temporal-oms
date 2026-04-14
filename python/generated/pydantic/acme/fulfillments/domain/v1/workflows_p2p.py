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

class Status(IntEnum):
    STATUS_UNSPECIFIED = 0
    STATUS_PENDING = 1
    STATUS_ALLOCATING = 2
    STATUS_SHIPPING_SELECTED = 3
    STATUS_COMPLETED = 4
    STATUS_FAILED = 5

class Item(BaseModel):
    item_id: str = Field(default="")
    sku_id: str = Field(default="")
    brand_code: str = Field(default="")
    quantity: int = Field(default=0)

class ShippingAddress(BaseModel):
    street: str = Field(default="")
    city: str = Field(default="")
    state: str = Field(default="")
    postal_code: str = Field(default="")
    country: str = Field(default="")

class FulfillOrderRequest(BaseModel):
    """
     Order Fulfillment AI Agent Workflow
    """

    order_id: str = Field(default="")
    customer_id: str = Field(default="")
    items: typing.List[Item] = Field(default_factory=list)
    payment_rrn: str = Field(default="")
    shipping_address: ShippingAddress = Field(default_factory=ShippingAddress)
    created_at: datetime = Field(default_factory=datetime.now)

class ShippingDetails(BaseModel):
    carrier: str = Field(default="")
    service_level: str = Field(default="")
    cost_cents: int = Field(default=0)
    estimated_days: int = Field(default=0)
    tracking_number: str = Field(default="")

class AllocatedItem(BaseModel):
    item_id: str = Field(default="")
    sku_id: str = Field(default="")
    quantity: int = Field(default=0)
    warehouse_id: str = Field(default="")
    warehouse_location: str = Field(default="")

class FulfillOrderResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    order_id: str = Field(default="")
    status: Status = Field(default=0)
    shipping: ShippingDetails = Field(default_factory=ShippingDetails)
    allocated_items: typing.List[AllocatedItem] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.now)

class FindOptimalShippingRequest(BaseModel):
    """
     Activity: FindOptimalShipping (AI-powered)
    """

    destination: ShippingAddress = Field(default_factory=ShippingAddress)
    items: typing.List[Item] = Field(default_factory=list)
    max_cost_cents: int = Field(default=0)
    max_days: int = Field(default=0)

class ShippingOption(BaseModel):
    carrier: str = Field(default="")
    service_level: str = Field(default="")
    cost_cents: int = Field(default=0)
    estimated_days: int = Field(default=0)
    score: float = Field(default=0.0)# AI-computed score

class FindOptimalShippingResponse(BaseModel):
    options: typing.List[ShippingOption] = Field(default_factory=list)
    recommended: ShippingOption = Field(default_factory=ShippingOption)# AI-selected
    reasoning: str = Field(default="")# LLM explanation

class AllocateInventoryRequest(BaseModel):
    """
     Activity: AllocateInventory
    """

    items: typing.List[Item] = Field(default_factory=list)
    destination: ShippingAddress = Field(default_factory=ShippingAddress)

class AllocateInventoryResponse(BaseModel):
    allocations: typing.List[AllocatedItem] = Field(default_factory=list)
    fully_allocated: bool = Field(default=False)
    warnings: typing.List[str] = Field(default_factory=list)

class FindClosestWarehouseRequest(BaseModel):
    """
     Activity: FindClosestWarehouse
    """

    sku_id: str = Field(default="")
    quantity: int = Field(default=0)
    destination: ShippingAddress = Field(default_factory=ShippingAddress)

class FindClosestWarehouseResponse(BaseModel):
    warehouse_id: str = Field(default="")
    warehouse_location: str = Field(default="")
    available_quantity: int = Field(default=0)
    distance_km: float = Field(default=0.0)

class PaymentDetails(BaseModel):
    rrn: str = Field(default="")

class ItemOutput(BaseModel):
    item_id: str = Field(default="")
    sku_id: str = Field(default="")
    brand_code: str = Field(default="")
    quantity: int = Field(default=0)
    warehouse_id: str = Field(default="")

class FulfilledOrderEvent(BaseModel):
    """
     Kafka Output Message
    """

    customer_id: str = Field(default="")
    order_id: str = Field(default="")
    payment_details: PaymentDetails = Field(default_factory=PaymentDetails)
    items: typing.List[ItemOutput] = Field(default_factory=list)
    shipping: ShippingDetails = Field(default_factory=ShippingDetails)
    fulfilled_at: datetime = Field(default_factory=datetime.now)
