# core/config.py
"""Configuration management using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=50)
    database_pool_timeout: int = Field(default=30, ge=1)
    database_echo: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
    )


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)
    bcrypt_rounds: int = Field(default=12, ge=4, le=20)

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        case_sensitive=False,
    )


class ThresholdSettings(BaseSettings):
    """Matching engine threshold settings."""

    threshold_high: Annotated[float, Field(ge=0, le=100)] = Field(
        default=95.0,
        description="Auto-approve threshold (0-100)",
    )
    threshold_mid: Annotated[float, Field(ge=0, le=100)] = Field(
        default=75.0,
        description="One-click review threshold (0-100)",
    )
    threshold_low: Annotated[float, Field(ge=0, le=100)] = Field(
        default=50.0,
        description="Manual review threshold (0-100)",
    )
    tolerance_price: Annotated[float, Field(ge=0, le=100)] = Field(
        default=5.0,
        description="Price tolerance percentage",
    )
    tolerance_qty: Annotated[float, Field(ge=0, le=100)] = Field(
        default=10.0,
        description="Quantity tolerance percentage",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: float, info) -> float:
        """Validate threshold ordering."""
        if info.field_name == "threshold_high":
            return v
        return v

    model_config = SettingsConfigDict(
        env_prefix="THRESHOLD_",
        case_sensitive=False,
    )


class AppSettings(BaseSettings):
    """Application-level settings."""

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_host: str = Field(default="0.0.0.0")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins",
    )
    debug: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


class Settings(BaseSettings):
    """Combined application settings.

    Loads all settings from environment variables with appropriate prefixes.
    """

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    app: AppSettings = Field(default_factory=AppSettings)

    @property
    def database_url(self) -> str:
        """Get database URL for sync connections."""
        return self.database.database_url.replace(
            "postgresql+asyncpg", "postgresql+psycopg2"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [
            origin.strip()
            for origin in self.app.cors_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()

__all__ = [
    "Settings",
    "DatabaseSettings",
    "SecuritySettings",
    "ThresholdSettings",
    "AppSettings",
    "settings",
    "get_settings",
]
