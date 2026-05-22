from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

from acme.common.v1.values_p2p import EasyPostRate, EasyPostShipment, Shipment
from acme.fulfillment.domain.v1.shipping_agent_p2p import GetShippingRatesRequest
from src.services import enablements_integrations as module
from src.services.enablements_integrations import (
    EnablementsIntegrationsClient,
    _to_protobuf_json,
)


class _Response:
    def __init__(self, body: dict) -> None:
        self._body = json.dumps(body).encode()

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_get_carrier_rates_calls_enablements_api(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return _Response({
            "shipmentId": "shp_1",
            "options": [
                {
                    "id": "rate_1",
                    "carrier": "UPS",
                    "serviceLevel": "Ground",
                    "cost": {"currency": "USD", "units": "1200"},
                    "estimatedDays": 2,
                    "rateId": "rate_1",
                    "shipmentId": "shp_1",
                }
            ],
        })

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    client = EnablementsIntegrationsClient("http://enablements.test", timeout_secs=3.0)
    response = client.get_carrier_rates(GetShippingRatesRequest(
        from_easypost_id="adr_from",
        to_easypost_id="adr_to",
    ))

    parsed = urlparse(captured["url"])
    assert parsed.path == "/api/v1/integrations/shipping/rates"
    assert "request" in parse_qs(parsed.query)
    assert captured["timeout"] == 3.0
    assert response.shipment_id == "shp_1"
    assert response.options[0].rate_id == "rate_1"
    assert response.options[0].cost.units == 1200


def test_request_json_preserves_explicit_zero_delivery_days() -> None:
    data = json.loads(_to_protobuf_json(GetShippingRatesRequest(
        selected_shipment=Shipment(
            easypost=EasyPostShipment(
                selected_rate=EasyPostRate(delivery_days=0),
            ),
        ),
    )))

    assert data["selectedShipment"]["easypost"]["selectedRate"]["deliveryDays"] == "0"
