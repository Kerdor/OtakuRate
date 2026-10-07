from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["dev", "test", "prod"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OTAKURATE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = "dev"
    database_url: str | None = None
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.environment == "test":
            self.database_url = "sqlite:///:memory:"
            self.debug = False
            return self

        if self.environment == "prod":
            if not self.database_url or not self.database_url.strip():
                raise ValueError(
                    "OTAKURATE_DATABASE_URL is required in production."
                )
            self.debug = False
            return self

        if not self.database_url:
            self.database_url = "sqlite:///./otakurate.db"

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
