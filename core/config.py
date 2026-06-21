# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass123@localhost:5432/apautomation",
        description="PostgreSQL connection URL with asyncpg driver",
    )
    database_pool_size: int = Field(default=20, ge=1, description="Connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Max overflow connections")
    database_pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="changeme-in-production",
        description="Secret key for JWT signing (HS256)",
        min_length=32,
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Access token expiry in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, ge=1, description="Refresh token expiry in days"
    )

    model_config = SettingsConfigDict(env_prefix="JWT_")


class ThresholdSettings(BaseSettings):
    """Matching threshold settings for score-based routing."""

    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= this value)",
    )
    threshold_mid: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="One-click review threshold (score >= this value)",
    )
    threshold_low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= this value)",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        """Ensure thresholds are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0 and 1")
        return v

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")


class ToleranceSettings(BaseSettings):
    """Matching tolerance settings for price/quantity comparisons."""

    tolerance_price: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as percentage (0.02 = 2%)",
    )
    tolerance_qty: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as percentage (0.05 = 5%)",
    )

    model_config = SettingsConfigDict(env_prefix="TOLERANCE_")


class AppSettings(BaseSettings):
    """Main application settings."""

    app_name: str = Field(default="AP Automation Engine", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(
    AppSettings,
    DatabaseSettings,
    JWTSettings,
    ThresholdSettings,
    ToleranceSettings,
):
    """Combined settings class with all configuration.

    Settings are loaded from environment variables with appropriate prefixes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate threshold ordering
        if not (self.threshold_low <= self.threshold_mid <= self.threshold_high):
            raise ValueError(
                "Invalid threshold ordering: threshold_low <= threshold_mid <= threshold_high"
            )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
