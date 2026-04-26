from __future__ import annotations

from temporalio.contrib.pydantic import PydanticJSONPlainPayloadConverter
from temporalio.converter import (
    BinaryNullPayloadConverter,
    BinaryPlainPayloadConverter,
    CompositePayloadConverter,
    DataConverter,
)

from ._converters import PydanticBinaryProtoPayloadConverter, PydanticJsonProtoPayloadConverter


class ProtoPydanticPayloadConverter(CompositePayloadConverter):
    """Composite converter: json/protobuf and binary/protobuf with Pydantic _p2p awareness,
    json/plain fallback via PydanticJSONPlainPayloadConverter for all other types."""

    def __init__(self) -> None:
        super().__init__(
            BinaryNullPayloadConverter(),
            BinaryPlainPayloadConverter(),
            PydanticJsonProtoPayloadConverter(),    # json/protobuf — preferred outbound for _p2p
            PydanticBinaryProtoPayloadConverter(),  # binary/protobuf — decode path for binary senders
            PydanticJSONPlainPayloadConverter(),    # json/plain — hand-written models, primitives
        )


proto_pydantic_data_converter = DataConverter(
    payload_converter_class=ProtoPydanticPayloadConverter,
)
