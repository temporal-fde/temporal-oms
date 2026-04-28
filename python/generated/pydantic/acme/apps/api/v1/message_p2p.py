# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from datetime import datetime
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class Item(BaseModel):
    item_id: str = Field(default="")
    quantity: int = Field(default=0)

class ShippingAddress(BaseModel):
    street: str = Field(default="")
    city: str = Field(default="")
    state: str = Field(default="")
    postal_code: str = Field(default="")
    country: str = Field(default="")

class SelectedShipment(BaseModel):
    """
     SelectedShipment carries the customer's checkout selection for margin and SLA reasoning.
    """

    paid_price_cents: int = Field(default=0)# customer's paid price in minor currency units
    currency: str = Field(default="")# ISO 4217; defaults to USD if empty
    delivery_days: typing.Optional[int] = Field(default=0)# agreed transit days (SLA)
    rate_id: str = Field(default="")# EasyPost rate ID of the selected option

class Order(BaseModel):
    order_id: str = Field(default="")
    items: typing.List[Item] = Field(default_factory=list)
    shipping_address: ShippingAddress = Field(default_factory=ShippingAddress)
    selected_shipment: typing.Optional[SelectedShipment] = Field(default_factory=SelectedShipment)

class SubmitOrderRequest(BaseModel):
    """
     PUT /api/v1/commerce-app/orders/{order_id}
    """

    customer_id: str = Field(default="")
    order: Order = Field(default_factory=Order)

class SubmitOrderResponse(BaseModel):
    order_id: str = Field(default="")
    status: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)

class Metadata(BaseModel):
    order_id: str = Field(default="")

class MakePaymentRequest(BaseModel):
    """
     POST /api/v1/payments-app/orders
    """

    customer_id: str = Field(default="")
    rrn: str = Field(default="")# Retrieval Reference Number / payment_intent
    amount_cents: int = Field(default=0)
    metadata: Metadata = Field(default_factory=Metadata)

class MakePaymentResponse(BaseModel):
    order_id: str = Field(default="")
    status: str = Field(default="")
    processed_at: datetime = Field(default_factory=datetime.now)

class ListOrdersRequest(BaseModel):
    """
     GET /api/v1/commerce-app/orders
    """

    customer_id: str = Field(default="")
    page_size: int = Field(default=0)
    page_token: str = Field(default="")

class OrderSummary(BaseModel):
    order_id: str = Field(default="")
    customer_id: str = Field(default="")
    status: str = Field(default="")
    total_amount_cents: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)

class ListOrdersResponse(BaseModel):
    orders: typing.List[OrderSummary] = Field(default_factory=list)
    next_page_token: str = Field(default="")

class ListProductsRequest(BaseModel):
    """
     GET /api/v1/commerce-app/clothing
    """

    limit: int = Field(default=0)# Default 50

class Product(BaseModel):
    item_id: str = Field(default="")
    name: str = Field(default="")
    description: str = Field(default="")
    price_cents: int = Field(default=0)
    image_url: str = Field(default="")

class ListProductsResponse(BaseModel):
    items: typing.List[Product] = Field(default_factory=list)
