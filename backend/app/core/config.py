from functools import lru_cache
from typing import Literal

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
    app_environment: Literal["development", "test", "staging", "production"] = "development"
    database_url: SecretStr | None = None

    # Telemetry is opt-in. No key falls back to the login JWT key.
    telemetry_enabled: bool = False
    telemetry_processing_region: Literal["US", "UK"] | None = None
    telemetry_endpoint: str | None = None
    telemetry_key_version: str = "v1"
    telemetry_user_key: SecretStr | None = None
    telemetry_subject_key: SecretStr | None = None
    telemetry_clinic_key: SecretStr | None = None
    telemetry_context_key: SecretStr | None = None
    telemetry_resource_key: SecretStr | None = None
    telemetry_context_ttl_seconds: int = 300

    # Shared backend: separate server-side keyrings selected from validated clinics.
    telemetry_us_user_key: SecretStr | None = None
    telemetry_us_subject_key: SecretStr | None = None
    telemetry_us_clinic_key: SecretStr | None = None
    telemetry_us_context_key: SecretStr | None = None
    telemetry_us_resource_key: SecretStr | None = None
    telemetry_us_endpoint: str | None = None
    telemetry_uk_user_key: SecretStr | None = None
    telemetry_uk_subject_key: SecretStr | None = None
    telemetry_uk_clinic_key: SecretStr | None = None
    telemetry_uk_context_key: SecretStr | None = None
    telemetry_uk_resource_key: SecretStr | None = None
    telemetry_uk_endpoint: str | None = None

    # Temporary self-issued JWT auth (see memory-bank/proposals.md).
    # Replace with the client's SSO/OIDC provider before production.
    jwt_secret_key: SecretStr = SecretStr("insecure-development-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    @field_validator("database_url", mode="before")
    @classmethod
    def empty_database_url_is_unset(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("telemetry_processing_region", mode="before")
    @classmethod
    def empty_region_is_shared(cls, value: object) -> object:
        return None if value == "" else value

    def require_database_url(self) -> str:
        if self.database_url is None:
            raise RuntimeError("DATABASE_URL is required for database operations")
        return self.database_url.get_secret_value()

    @property
    def self_issued_token_endpoint_enabled(self) -> bool:
        """Only local development and automated tests may claim arbitrary roles."""
        return self.app_environment in {"development", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
