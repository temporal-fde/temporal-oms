from __future__ import annotations

import json
from typing import TypeVar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from google.protobuf.json_format import MessageToDict, MessageToJson, Parse, ParseDict
from pydantic import BaseModel

from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    GetLocationEventsRequest,
    GetLocationEventsResponse,
    GetShippingRatesRequest,
    GetShippingRatesResponse,
)
from acme.fulfillment.domain.v1.workflows_p2p import (
    VerifyAddressRequest,
    VerifyAddressResponse,
)
from src.config import settings
from src.converter._converters import _fix_timestamps
from src.converter._registry import REGISTRY

ModelT = TypeVar("ModelT", bound=BaseModel)

_DICT_OPTS = {
    "preserving_proto_field_name": True,
    "always_print_fields_with_no_presence": True,
    "use_integers_for_enums": True,
}


class EnablementsIntegrationError(RuntimeError):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


class EnablementsIntegrationsClient:
    def __init__(self, base_url: str | None = None, timeout_secs: float = 10.0) -> None:
        self._base_url = (base_url or settings.enablements_api_base_url).rstrip("/")
        self._timeout_secs = timeout_secs

    def verify_address(self, request: VerifyAddressRequest) -> VerifyAddressResponse:
        return self._get(
            "/api/v1/integrations/shipping/verify-address",
            request,
            VerifyAddressResponse,
        )

    def get_carrier_rates(self, request: GetShippingRatesRequest) -> GetShippingRatesResponse:
        return self._get(
            "/api/v1/integrations/shipping/rates",
            request,
            GetShippingRatesResponse,
        )

    def get_location_events(self, request: GetLocationEventsRequest) -> GetLocationEventsResponse:
        return self._get(
            "/api/v1/integrations/location-events",
            request,
            GetLocationEventsResponse,
        )

    def _get(self, path: str, request_model: BaseModel, response_type: type[ModelT]) -> ModelT:
        query = urlencode({"request": _to_protobuf_json(request_model)})
        request = Request(
            f"{self._base_url}{path}?{query}",
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=self._timeout_secs) as response:
                body = response.read().decode("utf-8")
        except HTTPError as e:
            raise _to_integration_error(e) from e
        except URLError as e:
            raise EnablementsIntegrationError(503, "ENABLEMENTS_API_UNAVAILABLE", str(e)) from e
        return _from_protobuf_json(body, response_type)


def _to_protobuf_json(model: BaseModel) -> str:
    pb2_cls = REGISTRY[type(model)]
    pb2 = ParseDict(
        _fix_timestamps(model.model_dump(mode="json", exclude_unset=True)),
        pb2_cls(),
    )
    return MessageToJson(pb2, always_print_fields_with_no_presence=False)


def _from_protobuf_json(data: str, model_type: type[ModelT]) -> ModelT:
    pb2_cls = REGISTRY[model_type]
    pb2 = Parse(data or "{}", pb2_cls(), ignore_unknown_fields=True)
    return model_type.model_validate(MessageToDict(pb2, **_DICT_OPTS))


def _to_integration_error(error: HTTPError) -> EnablementsIntegrationError:
    body = error.read().decode("utf-8")
    code = ""
    message = body or str(error)
    try:
        parsed = json.loads(body)
        code = str(parsed.get("code", ""))
        message = str(parsed.get("message", message))
    except Exception:
        pass
    return EnablementsIntegrationError(error.code, code, message)
