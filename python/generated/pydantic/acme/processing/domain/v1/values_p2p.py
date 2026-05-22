# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from enum import IntEnum
from pydantic import BaseModel

class Errors(IntEnum):
    ERRORS_UNSPECIFIED = 0
    ERRORS_INVALID_ARGUMENTS = 1
    ERRORS_ORDER_VALIDATION_FAILED = 2
    ERRORS_KAFKA_ERROR = 3
