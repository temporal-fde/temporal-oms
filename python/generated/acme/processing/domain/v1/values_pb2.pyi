from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class Errors(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ERRORS_UNSPECIFIED: _ClassVar[Errors]
    ERRORS_INVALID_ARGUMENTS: _ClassVar[Errors]
    ERRORS_ORDER_VALIDATION_FAILED: _ClassVar[Errors]
    ERRORS_KAFKA_ERROR: _ClassVar[Errors]
ERRORS_UNSPECIFIED: Errors
ERRORS_INVALID_ARGUMENTS: Errors
ERRORS_ORDER_VALIDATION_FAILED: Errors
ERRORS_KAFKA_ERROR: Errors
