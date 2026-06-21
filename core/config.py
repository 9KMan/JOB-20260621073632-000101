# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://ap_user:ap_password@localhost:5432/ap_automation",
        description="Async PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=10, ge=1, description="Connection pool size")
    database_max_overflow: int = Field(default=20, ge=0, description="Max overflow connections")
    database_pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    database_pool_recycle: int = Field(default=3600, ge=0, description="Pool recycle time in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="change-me-in-production-use-strong-secret",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: Literal["HS256"] = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Access token expiry in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, ge=1, description="Refresh token expiry in days"
    )

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        case_sensitive=False,
    )


class MatchingThresholds(BaseSettings):
    """Matching threshold configuration."""

    threshold_high: float = Field(
        default=95.0, ge=0, le=100, description="Auto-approve threshold percentage"
    )
    threshold_mid: float = Field(
        default=70.0, ge=0, le=100, description="1-click review threshold percentage"
    )
    threshold_low: float = Field(
        default=40.0, ge=0, le=100, description="Exception threshold percentage"
    )
    tolerance_price: float = Field(
        default=5.0, ge=0, description="Price match tolerance percentage"
    )
    tolerance_qty: float = Field(
        default=10.0, ge=0, description="Quantity match tolerance percentage"
    )

    model_config = SettingsConfigDict(
        env_prefix="THRESHOLD_",
        case_sensitive=False,
    )


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = Field(default="AP Automation Engine", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_description: str = Field(
        default="AP Automation Core Engine for FinaRo",
        description="Application description",
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log level"
    )
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    matching: MatchingThresholds = Field(default_factory=MatchingThresholds)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase."""
        return v.upper()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience function for dependency injection
def get_database_settings() -> DatabaseSettings:
    """Get database settings."""
    return get_settings().database


def get_jwt_settings() -> JWTSettings:
    """Get JWT settings."""
    return get_settings().jwt


def get_matching_settings() -> MatchingThresholds:
    """Get matching threshold settings."""
    return get_settings().matching
