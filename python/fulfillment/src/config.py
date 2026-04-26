from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.local",
            str(_ROOT / ".env"),
            str(_ROOT / ".env.local"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    temporal_fulfillment_address: str = "localhost:7233"
    temporal_fulfillment_api_key: str = ""
    temporal_fulfillment_namespace: str = "fulfillment"
    anthropic_api_key: str = ""
    easypost_api_key: str = ""
    predicthq_api_key: str = ""
    integrations_endpoint: str = "oms-integrations-v1"


settings = Settings()