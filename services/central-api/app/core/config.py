from functools import lru_cache

from pydantic import SecretStr
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "HealthCore API"
    database_url: SecretStr | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def empty_database_url_is_unset(cls, value: object) -> object:
        return None if value == "" else value

    def require_database_url(self) -> str:
        if self.database_url is None:
            raise RuntimeError("DATABASE_URL is required for database operations")
        return self.database_url.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()