# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from datetime import datetime
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class Money(BaseModel):
    currency: str = Field(default="")# ISO 4217 currency code (USD, EUR, JPY, etc.)
    units: int = Field(default=0)# Amount in minor units (ISO 4217 exponent)

class Address(BaseModel):
    street: str = Field(default="")
    city: str = Field(default="")
    state: str = Field(default="")
    postal_code: str = Field(default="")
    country: str = Field(default="")# ISO 3166-1 alpha-2

class TimeRange(BaseModel):
    start: datetime = Field(default_factory=datetime.now)
    end: datetime = Field(default_factory=datetime.now)

class Pagination(BaseModel):
    page_size: int = Field(default=0)
    page_token: str = Field(default="")

class ErrorDetails(BaseModel):
    code: str = Field(default="")
    message: str = Field(default="")
    metadata: "typing.Dict[str, str]" = Field(default_factory=dict)

class Coordinate(BaseModel):
    """
     Coordinate is a WGS-84 geographic position (longitude/latitude decimal degrees).
    """

    latitude: float = Field(default=0.0)
    longitude: float = Field(default=0.0)
