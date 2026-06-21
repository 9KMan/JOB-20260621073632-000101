# core/config.py
"""Application configuration via pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or connection strings.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="PostgreSQL connection URL with asyncpg driver",
    )

    # Optional PGBouncer settings
    pgbouncer_host: str | None = Field(
        default=None,
        description="PGBouncer host for connection pooling",
    )
    pgbouncer_port: int = Field(
        default=6432,
        description="PGBouncer port",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("database_url must start with 'postgresql'")
        return v


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for HS256 JWT signing",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiry in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiry in days",
    )


class MatchingThresholds(BaseSettings):
    """Matching engine threshold settings (0-100 scale)."""

    threshold_high: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold",
    )
    threshold_mid: int = Field(
        default=70,
        ge=0,
        le=100,
        description="1-click review threshold",
    )
    threshold_low: int = Field(
        default=40,
        ge=0,
        le=100,
        description="Exception threshold",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("Threshold must be between 0 and 100")
        return v


class ToleranceSettings(BaseSettings):
    """Tolerance settings for matching calculations (percentage)."""

    tolerance_price: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Quantity match tolerance percentage",
    )


class AppSettings(BaseSettings):
    """General application settings."""

    app_name: str = Field(
        default="AP Automation",
        description="Application name",
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 route prefix",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    environment: str = Field(
        default="development",
        description="Environment (development/staging/production)",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )


class Settings(
    AppSettings,
    DatabaseSettings,
    JWTSettings,
    MatchingThresholds,
    ToleranceSettings,
):
    """Combined application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()

# Type aliases for dependency injection
DatabaseUrl = Annotated[str, Field(description="Database URL")]
JWTAlgorithm = Annotated[str, Field(description="JWT algorithm")]
