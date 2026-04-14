# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
from values_p2p import Money
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

class Order(BaseModel):
    order_id: str = Field(default="")
    items: typing.List[Item] = Field(default_factory=list)
    shipping_address: ShippingAddress = Field(default_factory=ShippingAddress)

class Payment(BaseModel):
    rrn: str = Field(default="")
    amount: Money = Field(default_factory=Money)
