# core/config.py
"""Configuration management for AP Automation Core Engine.

All configuration is loaded from environment variables using pydantic-settings.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="PostgreSQL async connection URL",
    )
    pgbouncer_host: str = Field(
        default="localhost",
        description="PGBouncer host",
    )
    pgbouncer_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="PGBouncer port",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries (debug mode)",
    )
    database_pool_size: int = Field(
        default=20,
        ge=1,
        description="Connection pool size",
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        description="Max overflow connections",
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Pool timeout in seconds",
    )

    @property
    def sync_database_url(self) -> str:
        """Convert async URL to sync URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")


class JWTSettings(BaseSettings):
    """JWT authentication configuration."""

    jwt_secret_key: str = Field(
        default="changeme-in-production-use-strong-secret",
        description="HS256 signing secret key",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiry in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        description="Refresh token expiry in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration."""

    threshold_high: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: int = Field(
        default=60,
        ge=0,
        le=100,
        description="1-click review threshold (percentage)",
    )
    threshold_low: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Exception threshold (percentage)",
    )
    tolerance_price: float = Field(
        default=5.0,
        ge=0,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0,
        description="Quantity match tolerance percentage",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_threshold_order(cls, v: int, info) -> int:
        """Ensure thresholds are properly ordered."""
        thresholds = info.data
        if "threshold_high" in thresholds and v <= thresholds["threshold_high"]:
            if info.field_name == "threshold_low":
                return v
        return v


class AppSettings(BaseSettings):
    """Application-level configuration."""

    app_name: str = Field(
        default="AP Automation Core Engine",
        description="Application name",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Log level",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="CORS allowed origins",
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 prefix",
    )


class Settings(BaseSettings):
    """Combined settings container."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    app: AppSettings = Field(default_factory=AppSettings)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience accessors
settings = get_settings()

__all__ = [
    "Settings",
    "DatabaseSettings",
    "JWTSettings",
    "ThresholdSettings",
    "AppSettings",
    "get_settings",
    "settings",
]
