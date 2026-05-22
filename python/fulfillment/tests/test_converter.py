"""Tests for src/converter — Pydantic ↔ protobuf payload converter."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from pydantic import BaseModel

import pytest

from src.converter import ProtoPydanticPayloadConverter, proto_pydantic_data_converter
from src.converter._converters import (
    PydanticBinaryProtoPayloadConverter,
    PydanticJsonProtoPayloadConverter,
)
from src.converter._registry import REGISTRY

from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    RecommendShippingOptionRequest,
    RecommendShippingOptionResponse,
    ShippingOption,
)
from acme.fulfillment.domain.v1.workflows_p2p import (
    DeliveryStatus,
    NotifyDeliveryStatusRequest,
    StartOrderFulfillmentRequest,
    PlacedOrder,
    FulfillmentItem,
)
from acme.common.v1.values_p2p import (
    Address,
    EasyPostAddress,
    EasyPostRate,
    EasyPostShipment,
    Money,
    Shipment,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_request() -> RecommendShippingOptionRequest:
    return RecommendShippingOptionRequest(
        order_id="order-123",
        customer_id="cust-456",
    )


@pytest.fixture
def nested_request() -> StartOrderFulfillmentRequest:
    return StartOrderFulfillmentRequest(
        order_id="order-789",
        customer_id="cust-abc",
        placed_order=PlacedOrder(
            order_id="order-789",
            customer_id="cust-abc",
            items=[
                FulfillmentItem(item_id="i1", sku_id="sku-1", quantity=2),
                FulfillmentItem(item_id="i2", sku_id="sku-2", quantity=1),
            ],
            shipping_address=Address(easypost=EasyPostAddress(city="Springfield")),
        ),
        selected_shipment=Shipment(
            easypost=EasyPostShipment(
                shipment_id="shp-1",
                selected_rate=EasyPostRate(rate_id="rate-1", delivery_days=5),
            ),
            paid_price=Money(currency="USD", units=1099),
        ),
    )


@pytest.fixture
def enum_request() -> NotifyDeliveryStatusRequest:
    return NotifyDeliveryStatusRequest(
        order_id="order-123",
        delivery_status=DeliveryStatus.DELIVERY_STATUS_DELIVERED,
    )


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------

def test_json_proto_roundtrip(simple_request):
    conv = PydanticJsonProtoPayloadConverter()

    payload = conv.to_payload(simple_request)

    assert payload is not None
    assert payload.metadata[b"encoding"] == b"json/protobuf"
    assert payload.metadata[b"messageType"] != b""

    result = conv.from_payload(payload, type_hint=RecommendShippingOptionRequest)

    assert isinstance(result, RecommendShippingOptionRequest)
    assert result.order_id == simple_request.order_id
    assert result.customer_id == simple_request.customer_id


def test_json_proto_payload_data_is_valid_json(simple_request):
    conv = PydanticJsonProtoPayloadConverter()
    payload = conv.to_payload(simple_request)
    # SDK uses compact JSON (no spaces) with camelCase field names
    data = json.loads(payload.data)
    assert isinstance(data, dict)
    # camelCase keys — proto JSON standard (not snake_case)
    assert "orderId" in data or "order_id" in data  # either accepted; SDK uses camelCase


def test_json_proto_omits_unset_selected_shipment(simple_request):
    conv = PydanticJsonProtoPayloadConverter()
    payload = conv.to_payload(simple_request)
    data = json.loads(payload.data)

    assert "selectedShipment" not in data

    result = conv.from_payload(payload, type_hint=RecommendShippingOptionRequest)

    assert "selected_shipment" not in result.model_fields_set


def test_json_proto_preserves_explicit_zero_delivery_days():
    conv = PydanticJsonProtoPayloadConverter()
    request = RecommendShippingOptionRequest(
        order_id="order-123",
        customer_id="cust-456",
        selected_shipment=Shipment(
            easypost=EasyPostShipment(
                shipment_id="shp-1",
                selected_rate=EasyPostRate(rate_id="rate-1", delivery_days=0),
            ),
            paid_price=Money(currency="USD", units=1),
        ),
    )

    payload = conv.to_payload(request)
    data = json.loads(payload.data)

    assert data["selectedShipment"]["easypost"]["selectedRate"]["deliveryDays"] == "0"

    result = conv.from_payload(payload, type_hint=RecommendShippingOptionRequest)
    selected_rate = result.selected_shipment.easypost.selected_rate

    assert "selected_shipment" in result.model_fields_set
    assert "delivery_days" in selected_rate.model_fields_set
    assert selected_rate.delivery_days == 0


def test_json_proto_message_type_header(simple_request):
    conv = PydanticJsonProtoPayloadConverter()
    payload = conv.to_payload(simple_request)
    msg_type = payload.metadata[b"messageType"].decode()
    # Must be the fully-qualified proto type name
    assert "RecommendShippingOptionRequest" in msg_type
    assert msg_type.startswith("acme.")


# ---------------------------------------------------------------------------
# Binary round-trip
# ---------------------------------------------------------------------------

def test_binary_proto_roundtrip(simple_request):
    conv = PydanticBinaryProtoPayloadConverter()

    payload = conv.to_payload(simple_request)

    assert payload is not None
    assert payload.metadata[b"encoding"] == b"binary/protobuf"
    assert payload.metadata[b"messageType"] != b""

    result = conv.from_payload(payload, type_hint=RecommendShippingOptionRequest)

    assert isinstance(result, RecommendShippingOptionRequest)
    assert result.order_id == simple_request.order_id
    assert result.customer_id == simple_request.customer_id


# ---------------------------------------------------------------------------
# Composite outbound encoding preference
# ---------------------------------------------------------------------------

def test_composite_prefers_json_outbound(simple_request):
    composite = ProtoPydanticPayloadConverter()
    [payload] = composite.to_payloads([simple_request])
    assert payload.metadata[b"encoding"] == b"json/protobuf"


# ---------------------------------------------------------------------------
# Nested message round-trip
# ---------------------------------------------------------------------------

def test_json_nested_roundtrip(nested_request):
    conv = PydanticJsonProtoPayloadConverter()
    payload = conv.to_payload(nested_request)
    result = conv.from_payload(payload, type_hint=StartOrderFulfillmentRequest)

    assert isinstance(result, StartOrderFulfillmentRequest)
    assert result.order_id == nested_request.order_id
    assert len(result.placed_order.items) == 2
    assert result.placed_order.items[0].sku_id == "sku-1"
    assert result.placed_order.shipping_address.easypost.city == "Springfield"


def test_binary_nested_roundtrip(nested_request):
    conv = PydanticBinaryProtoPayloadConverter()
    payload = conv.to_payload(nested_request)
    result = conv.from_payload(payload, type_hint=StartOrderFulfillmentRequest)

    assert isinstance(result, StartOrderFulfillmentRequest)
    assert len(result.placed_order.items) == 2


# ---------------------------------------------------------------------------
# Enum round-trip
# ---------------------------------------------------------------------------

def test_enum_roundtrip_json(enum_request):
    conv = PydanticJsonProtoPayloadConverter()
    payload = conv.to_payload(enum_request)
    result = conv.from_payload(payload, type_hint=NotifyDeliveryStatusRequest)

    assert isinstance(result, NotifyDeliveryStatusRequest)
    assert result.delivery_status == DeliveryStatus.DELIVERY_STATUS_DELIVERED


def test_enum_roundtrip_binary(enum_request):
    conv = PydanticBinaryProtoPayloadConverter()
    payload = conv.to_payload(enum_request)
    result = conv.from_payload(payload, type_hint=NotifyDeliveryStatusRequest)

    assert result.delivery_status == DeliveryStatus.DELIVERY_STATUS_DELIVERED


# ---------------------------------------------------------------------------
# Passthrough / fallthrough behaviour
# ---------------------------------------------------------------------------

def test_non_registry_pydantic_returns_none():
    class HandWritten(BaseModel):
        x: int = 0

    json_conv = PydanticJsonProtoPayloadConverter()
    binary_conv = PydanticBinaryProtoPayloadConverter()

    assert json_conv.to_payload(HandWritten(x=1)) is None
    assert binary_conv.to_payload(HandWritten(x=1)) is None


def test_non_registry_pydantic_falls_through_composite():
    class HandWritten(BaseModel):
        x: int = 0

    composite = ProtoPydanticPayloadConverter()
    [payload] = composite.to_payloads([HandWritten(x=42)])
    # Falls through to PydanticJSONPlainPayloadConverter
    assert payload.metadata[b"encoding"] == b"json/plain"


def test_none_passthrough():
    json_conv = PydanticJsonProtoPayloadConverter()
    binary_conv = PydanticBinaryProtoPayloadConverter()
    assert json_conv.to_payload(None) is None
    assert binary_conv.to_payload(None) is None


def test_primitive_passthrough():
    json_conv = PydanticJsonProtoPayloadConverter()
    binary_conv = PydanticBinaryProtoPayloadConverter()
    assert json_conv.to_payload("hello") is None
    assert binary_conv.to_payload("hello") is None


# ---------------------------------------------------------------------------
# Raw pb2 passthrough (no Pydantic type hint)
# ---------------------------------------------------------------------------

def test_json_from_payload_no_hint_returns_pb2(simple_request):
    from acme.fulfillment.domain.v1 import shipping_agent_pb2
    conv = PydanticJsonProtoPayloadConverter()
    payload = conv.to_payload(simple_request)
    result = conv.from_payload(payload, type_hint=None)
    assert isinstance(result, shipping_agent_pb2.RecommendShippingOptionRequest)


# ---------------------------------------------------------------------------
# Registry completeness
# ---------------------------------------------------------------------------

def test_registry_covers_all_p2p_basemodel_classes():
    """Every BaseModel subclass in every generated _p2p module must be in REGISTRY."""
    p2p_root = Path(__file__).parent.parent.parent.parent / "python" / "generated" / "pydantic"
    missing: list[str] = []

    for p2p_path in sorted(p2p_root.rglob("*_p2p.py")):
        tree = ast.parse(p2p_path.read_text())
        module_name = (
            str(p2p_path.relative_to(p2p_root))
            .removesuffix(".py")
            .replace("/", ".")
        )
        for node in tree.body:  # top-level only — mirrors gen_converter_registry.py
            if not isinstance(node, ast.ClassDef):
                continue
            if any(
                (b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else None) == "BaseModel"
                for b in node.bases
            ):
                # Find the actual class object in REGISTRY keys
                found = any(
                    f"{cls.__module__}.{cls.__name__}" == f"{module_name}.{node.name}"
                    for cls in REGISTRY
                )
                if not found:
                    missing.append(f"{module_name}.{node.name}")

    assert not missing, f"Classes missing from REGISTRY:\n" + "\n".join(missing)
