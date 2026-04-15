# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from ....common.v1.values_p2p import Address
from ....common.v1.values_p2p import Money
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from workflows_p2p import CompleteOrderRequest
from workflows_p2p import GetProcessOrderStateResponse
import typing

class Status(IntEnum):
    STATUS_UNSPECIFIED = 0
    STATUS_PENDING = 1
    STATUS_ALLOCATING = 2
    STATUS_SHIPPING_SELECTED = 3
    STATUS_COMPLETED = 4
    STATUS_FAILED = 5


class DeliveryStatus(IntEnum):
    DELIVERY_STATUS_UNSPECIFIED = 0
    DELIVERY_STATUS_DELIVERED = 1
    DELIVERY_STATUS_CANCELED = 2


class FulfillmentStatus(IntEnum):
    FULFILLMENT_STATUS_UNSPECIFIED = 0
    FULFILLMENT_STATUS_STARTED = 1
    FULFILLMENT_STATUS_VALIDATED = 2
    FULFILLMENT_STATUS_FULFILLING = 3
    FULFILLMENT_STATUS_COMPLETED = 4
    FULFILLMENT_STATUS_DELIVERED = 5
    FULFILLMENT_STATUS_CANCELED = 6
    FULFILLMENT_STATUS_FAILED = 7

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

class StartOrderFulfillmentOptions(BaseModel):
    fulfillment_timeout_secs: typing.Optional[int] = Field(default=0)

class SelectedShippingOption(BaseModel):
    """
     SelectedShippingOption is the shipping option chosen by the customer at order
 placement time. Used as the baseline for margin comparison in fulfillOrder.
    """

    option_id: str = Field(default="")
    price: Money = Field(default_factory=Money)
    expected_ship_date: datetime = Field(default_factory=datetime.now)

class StartOrderFulfillmentRequest(BaseModel):
    """
     StartOrderFulfillmentRequest is the input to fulfillment.Order execute().
 Carries the full placed order from the apps domain and the customer's
 selected shipping option at order time.
    """

    order_id: str = Field(default="")
    customer_id: str = Field(default="")
    options: typing.Optional[StartOrderFulfillmentOptions] = Field(default_factory=StartOrderFulfillmentOptions)
    selected_shipping: SelectedShippingOption = Field(default_factory=SelectedShippingOption)
    placed_order: CompleteOrderRequest = Field(default_factory=CompleteOrderRequest)

class ValidateOrderRequest(BaseModel):
    """
     ValidateOrderRequest is the input to the validateOrder Update handler and
 the Nexus validateOrder operation. Carries the order_id and the customer's
 shipping address. If address.easypost_address is already set, the activity
 skips EasyPost verification.
    """

    order_id: str = Field(default="")
    address: Address = Field(default_factory=Address)

class ValidateOrderResponse(BaseModel):
    """
     ValidateOrderResponse returns the same address with easypost_address populated
 after verification. Stored in workflow state for downstream use in getCarrierRates.
    """

    address: Address = Field(default_factory=Address)

class VerifyAddressRequest(BaseModel):
    address: Address = Field(default_factory=Address)

class VerifyAddressResponse(BaseModel):
    address: Address = Field(default_factory=Address)# easypost_address populated after verification

class LoadFulfillmentOptionsRequest(BaseModel):
    order_id: str = Field(default="")

class FulfillmentOptions(BaseModel):
    """
     FulfillmentOptions carries policy loaded at workflow start via LocalActivity.
 shipping_margin is the maximum acceptable shipping cost; amounts above it
 are recorded in the margin_leak SearchAttribute.
    """

    shipping_margin: Money = Field(default_factory=Money)

class ProcessedOrder(BaseModel):
    """
     ProcessedOrder carries the result of processing.Order for use in fulfillment
 activities (carrier rates, label printing, inventory deduction).
    """

    order_id: str = Field(default="")
    customer_id: str = Field(default="")
    state: GetProcessOrderStateResponse = Field(default_factory=GetProcessOrderStateResponse)

class OrderFulfillRequest(BaseModel):
    """
     OrderFulfillRequest is the input to the fulfillOrder Update handler.
 Name is distinct from the Python-era FulfillOrderRequest in this package.
    """

    processed_order: ProcessedOrder = Field(default_factory=ProcessedOrder)

class ShippingSelection(BaseModel):
    """
     ShippingSelection records the carrier rate chosen during fulfillOrder.
 margin_delta_cents is the overage in minor currency units (set only when
 actual cost exceeds shipping_margin; also written to margin_leak SearchAttribute).
    """

    option_id: str = Field(default="")
    rate_id: str = Field(default="")
    carrier: str = Field(default="")
    service_level: str = Field(default="")
    actual_price: Money = Field(default_factory=Money)
    margin_delta_cents: int = Field(default=0)
    is_fallback: bool = Field(default=False)
    fallback_reason: str = Field(default="")

class OrderFulfillResponse(BaseModel):
    """
     OrderFulfillResponse is returned to the fulfillOrder Update caller (apps.Order).
 Name is distinct from the Python-era FulfillOrderResponse in this package.
    """

    tracking_number: str = Field(default="")
    shipping_selection: ShippingSelection = Field(default_factory=ShippingSelection)

class CancelFulfillmentOrderRequest(BaseModel):
    order_id: str = Field(default="")
    reason: str = Field(default="")

class DeliveryStatusNotification(BaseModel):
    model_config = ConfigDict(validate_default=True)
    order_id: str = Field(default="")
    delivery_status: DeliveryStatus = Field(default=0)
    carrier_tracking_id: typing.Optional[str] = Field(default="")
    failure_reason: typing.Optional[str] = Field(default="")

class GetFulfillmentOrderStateResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    args: StartOrderFulfillmentRequest = Field(default_factory=StartOrderFulfillmentRequest)
    options: FulfillmentOptions = Field(default_factory=FulfillmentOptions)
    validated_address: Address = Field(default_factory=Address)
    fulfillment_request: OrderFulfillRequest = Field(default_factory=OrderFulfillRequest)
    shipping_selection: ShippingSelection = Field(default_factory=ShippingSelection)
    tracking_number: str = Field(default="")
    status: FulfillmentStatus = Field(default=0)
    delivery_status: DeliveryStatus = Field(default=0)
    errors: typing.List[str] = Field(default_factory=list)

class FulfillmentItem(BaseModel):
    """
     FulfillmentItem is the line-item type for fulfillment activities.
 Name is distinct from the Python-era Item in this package.
 warehouse_id and warehouse_location are populated after processing completes.
    """

    item_id: str = Field(default="")
    sku_id: str = Field(default="")
    brand_code: str = Field(default="")
    quantity: int = Field(default=0)
    warehouse_id: typing.Optional[str] = Field(default="")
    warehouse_location: typing.Optional[str] = Field(default="")

class HoldItemsRequest(BaseModel):
    order_id: str = Field(default="")
    items: typing.List[FulfillmentItem] = Field(default_factory=list)

class HoldItemsResponse(BaseModel):
    hold_id: str = Field(default="")

class ReserveItemsRequest(BaseModel):
    order_id: str = Field(default="")
    hold_id: str = Field(default="")
    items: typing.List[FulfillmentItem] = Field(default_factory=list)

class ReserveItemsResponse(BaseModel):
    reservation_id: str = Field(default="")

class DeductInventoryRequest(BaseModel):
    order_id: str = Field(default="")
    reservation_id: str = Field(default="")

class DeductInventoryResponse(BaseModel):
    success: bool = Field(default=False)

class ReleaseHoldRequest(BaseModel):
    order_id: str = Field(default="")
    hold_id: str = Field(default="")

class ReleaseHoldResponse(BaseModel):
    success: bool = Field(default=False)

class GetCarrierRatesRequest(BaseModel):
    """
     GetCarrierRatesRequest creates an EasyPost Shipment and retrieves available
 carrier rates. easypost_address_id comes from state.validatedAddress.easypost_address.id.
    """

    order_id: str = Field(default="")
    easypost_address_id: str = Field(default="")
    items: typing.List[FulfillmentItem] = Field(default_factory=list)

class CarrierRate(BaseModel):
    rate_id: str = Field(default="")
    carrier: str = Field(default="")
    service_level: str = Field(default="")
    cost: Money = Field(default_factory=Money)
    estimated_days: int = Field(default=0)

class GetCarrierRatesResponse(BaseModel):
    shipment_id: str = Field(default="")# EasyPost Shipment ID, passed to printShippingLabel
    rates: typing.List[CarrierRate] = Field(default_factory=list)

class PrintShippingLabelRequest(BaseModel):
    order_id: str = Field(default="")
    shipment_id: str = Field(default="")
    rate_id: str = Field(default="")

class PrintShippingLabelResponse(BaseModel):
    tracking_number: str = Field(default="")
    label_url: str = Field(default="")
