from __future__ import annotations

import re
from typing import Any

from google.protobuf.json_format import MessageToDict, ParseDict
from pydantic import BaseModel
from temporalio.converter import BinaryProtoPayloadConverter, JSONProtoPayloadConverter

from ._registry import REGISTRY

_MSGTODICT_OPTS: dict[str, Any] = {
    "preserving_proto_field_name": True,
    "always_print_fields_with_no_presence": True,
    "use_integers_for_enums": True,
}

# Matches a naive ISO datetime string (no timezone indicator).
# protobuf's Timestamp parser uses rfind('-') to locate the timezone,
# so naive strings like "2026-04-25T15:35:45.123456" would match the date
# separator instead of a timezone offset, causing a parse error.
_NAIVE_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$")


def _fix_timestamps(obj: Any) -> Any:
    """Recursively walk a JSON-mode model_dump dict and append 'Z' to naive datetimes."""
    if isinstance(obj, dict):
        return {k: _fix_timestamps(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fix_timestamps(v) for v in obj]
    if isinstance(obj, str) and _NAIVE_DT_RE.match(obj):
        return obj + "Z"
    return obj


def _to_pb2(value: BaseModel, pb2_cls: type) -> Any:
    return ParseDict(_fix_timestamps(value.model_dump(mode="json", exclude_unset=True)), pb2_cls())


class PydanticJsonProtoPayloadConverter(JSONProtoPayloadConverter):
    """json/protobuf slot — adds Pydantic _p2p ↔ pb2 bridge to the SDK converter."""

    def to_payload(self, value: Any):
        if isinstance(value, BaseModel):
            pb2_cls = REGISTRY.get(type(value))
            if pb2_cls is None:
                return None  # hand-written model — fall through to json/plain
            return super().to_payload(_to_pb2(value, pb2_cls))
        return super().to_payload(value)

    def from_payload(self, payload, type_hint=None):
        pb2 = super().from_payload(payload)
        if isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
            return type_hint.model_validate(MessageToDict(pb2, **_MSGTODICT_OPTS))
        return pb2


class PydanticBinaryProtoPayloadConverter(BinaryProtoPayloadConverter):
    """binary/protobuf slot — adds Pydantic _p2p ↔ pb2 bridge to the SDK converter."""

    def to_payload(self, value: Any):
        if isinstance(value, BaseModel):
            pb2_cls = REGISTRY.get(type(value))
            if pb2_cls is None:
                return None
            return super().to_payload(_to_pb2(value, pb2_cls))
        return super().to_payload(value)

    def from_payload(self, payload, type_hint=None):
        pb2 = super().from_payload(payload)
        if isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
            return type_hint.model_validate(MessageToDict(pb2, **_MSGTODICT_OPTS))
        return pb2
