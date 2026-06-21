# core/config.py
"""Application configuration via pydantic-settings.

All configuration is driven by environment variables.
No secrets are hardcoded.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async PostgreSQL connection URL",
    )
    pool_size: int = Field(default=20, ge=1, description="Connection pool size")
    max_overflow: int = Field(default=10, ge=0, description="Max overflow connections")
    pool_timeout: int = Field(default=30, ge=1, description="Pool acquire timeout in seconds")
    pool_recycle: int = Field(default=3600, ge=0, description="Connection recycle in seconds")
    echo: bool = Field(default=False, description="Echo SQL queries (dev only)")

    sync_url: str | None = Field(
        default=None,
        description="Sync PostgreSQL URL for Alembic migrations",
    )

    @property
    def async_url(self) -> str:
        """Return the async database URL."""
        return self.url


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str = Field(
        default="change-me-in-production-use-at-least-32-random-chars",
        description="HS256 signing secret key",
        min_length=32,
    )
    algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="JWT algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiry in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        description="Refresh token expiry in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold settings for score-based routing."""

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")

    high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= THRESHOLD_HIGH)",
    )
    mid: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (score >= THRESHOLD_MID)",
    )
    low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= THRESHOLD_LOW)",
    )

    def route_decision(self, score: float) -> str:
        """Route a matching score to a decision tier.

        Args:
            score: Normalized match score between 0.0 and 1.0.

        Returns:
            Decision tier: "auto_approved", "review", or "exception".
        """
        if score >= self.high:
            return "auto_approved"
        elif score >= self.mid:
            return "review"
        elif score >= self.low:
            return "exception"
        else:
            return "rejected"


class ToleranceSettings(BaseSettings):
    """Tolerance settings for matching comparisons."""

    model_config = SettingsConfigDict(env_prefix="TOLERANCE_")

    price: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as decimal fraction (2% default)",
    )
    qty: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as decimal fraction (5% default)",
    )
    description: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Description similarity threshold (Jaccard / fuzzy)",
    )


class AppSettings(BaseSettings):
    """Main application settings composing all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    app_name: str = Field(default="AP Automation Core Engine", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(default=False, description="Debug mode")

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> AppSettings:
    """Get cached application settings singleton."""
    return AppSettings()


# Convenience import
settings = get_settings()
