from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    temporal_address: str = "localhost:7233"
    anthropic_api_key: str = ""
    easypost_api_key: str = ""
    predicthq_api_key: str = ""
    warehouse_config_path: str | None = None


settings = Settings()