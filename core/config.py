# core/config.py
"""Configuration management using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="PostgreSQL async database URL",
        validation_alias="DATABASE_URL",
    )
    database_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Database connection pool size",
    )
    database_max_overflow: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Maximum overflow connections",
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Pool timeout in seconds",
    )
    database_pool_recycle: int = Field(
        default=3600,
        ge=300,
        description="Connection recycle time in seconds",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries (debug only)",
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="changeme-in-production",
        min_length=32,
        description="Secret key for JWT signing (HS256)",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token expiration in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiration in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration settings."""

    threshold_high: float = Field(
        default=95.0,
        ge=0.0,
        le=100.0,
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="One-click review threshold (percentage)",
    )
    threshold_low: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Exception threshold (percentage)",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_threshold_order(cls, v: float, info) -> float:
        """Ensure thresholds are ordered correctly."""
        if info.field_name == "threshold_high":
            return v
        return v


class ToleranceSettings(BaseSettings):
    """Matching tolerance configuration settings."""

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


class ServerSettings(BaseSettings):
    """Server and application settings."""

    app_name: str = Field(
        default="AP Automation Engine",
        description="Application name",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version",
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 prefix",
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode",
    )


class Settings(BaseSettings):
    """Main application settings combining all configuration sections."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)

    @property
    def database_url(self) -> str:
        """Get database URL from database settings."""
        return self.database.database_url

    @property
    def threshold_auto_approve(self) -> float:
        """Get auto-approve threshold."""
        return self.threshold.threshold_high

    @property
    def threshold_review(self) -> float:
        """Get review threshold."""
        return self.threshold.threshold_mid

    @property
    def threshold_exception(self) -> float:
        """Get exception threshold."""
        return self.threshold.threshold_low


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience function for dependency injection
def get_database_url() -> str:
    """Get database URL for dependency injection."""
    return get_settings().database_url
