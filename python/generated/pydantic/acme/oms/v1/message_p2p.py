# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.33.6 
# Pydantic Version: 2.13.0 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class OmsProperties(BaseModel):
    class BoundedContextConfig(BaseModel):
        class NexusConfig(BaseModel):
            endpoints: "typing.Dict[str, str]" = Field(default_factory=dict)

        nexus: NexusConfig = Field(default_factory=NexusConfig)

    apps: "OmsProperties.BoundedContextConfig" = Field(default_factory=lambda : OmsProperties.BoundedContextConfig())
    processing: "OmsProperties.BoundedContextConfig" = Field(default_factory=lambda : OmsProperties.BoundedContextConfig())
    risk: "OmsProperties.BoundedContextConfig" = Field(default_factory=lambda : OmsProperties.BoundedContextConfig())
