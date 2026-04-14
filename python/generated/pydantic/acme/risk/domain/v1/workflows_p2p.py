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
    STATUS_PASSED = 2
    STATUS_FLAGGED = 3
    STATUS_BLOCKED = 4

class PaymentContext(BaseModel):
    rrn: str = Field(default="")
    amount_cents: int = Field(default=0)
    payment_method: str = Field(default="")

class AddressContext(BaseModel):
    street: str = Field(default="")
    city: str = Field(default="")
    state: str = Field(default="")
    postal_code: str = Field(default="")
    country: str = Field(default="")

class CustomerContext(BaseModel):
    customer_id: str = Field(default="")
    previous_order_count: int = Field(default=0)
    account_created_at: datetime = Field(default_factory=datetime.now)

class FraudCheckContext(BaseModel):
    payment: PaymentContext = Field(default_factory=PaymentContext)
    address: AddressContext = Field(default_factory=AddressContext)
    customer: CustomerContext = Field(default_factory=CustomerContext)

class DetectFraudRequest(BaseModel):
    """
     Fraud Detection Workflow
    """

    order_id: str = Field(default="")
    customer_id: str = Field(default="")
    context: FraudCheckContext = Field(default_factory=FraudCheckContext)
    created_at: datetime = Field(default_factory=datetime.now)

class DetectFraudResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    order_id: str = Field(default="")
    status: Status = Field(default=0)
    risk_score: float = Field(default=0.0)
    flags: typing.List[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.now)

class PerformFraudCheckRequest(BaseModel):
    """
     UpdateWithStart: performFraudCheck
    """

    context: FraudCheckContext = Field(default_factory=FraudCheckContext)

class PerformFraudCheckResponse(BaseModel):
    passed: bool = Field(default=False)
    risk_score: float = Field(default=0.0)
    flags: typing.List[str] = Field(default_factory=list)
    recommendation: str = Field(default="")

class CheckAddressFraudRequest(BaseModel):
    """
     Activity: CheckAddressFraud
    """

    address: AddressContext = Field(default_factory=AddressContext)

class CheckAddressFraudResponse(BaseModel):
    is_fraudulent: bool = Field(default=False)
    address_risk_score: float = Field(default=0.0)
    flags: typing.List[str] = Field(default_factory=list)

class CheckPaymentFraudRequest(BaseModel):
    """
     Activity: CheckPaymentFraud
    """

    payment: PaymentContext = Field(default_factory=PaymentContext)
    customer_id: str = Field(default="")

class CheckPaymentFraudResponse(BaseModel):
    is_fraudulent: bool = Field(default=False)
    payment_risk_score: float = Field(default=0.0)
    flags: typing.List[str] = Field(default_factory=list)

class GetCustomerRiskProfileRequest(BaseModel):
    """
     Activity: GetCustomerRiskProfile
    """

    customer_id: str = Field(default="")

class GetCustomerRiskProfileResponse(BaseModel):
    customer_id: str = Field(default="")
    historical_risk_score: float = Field(default=0.0)
    fraud_incident_count: int = Field(default=0)
    successful_order_count: int = Field(default=0)
    last_order_at: datetime = Field(default_factory=datetime.now)
