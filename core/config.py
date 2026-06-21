# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="PostgreSQL connection URL with asyncpg driver",
    )
    database_pool_size: int = Field(default=20, ge=1, description="Connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Max pool overflow")
    database_pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, ge=1, description="Refresh token expiration in days"
    )

    model_config = SettingsConfigDict(env_prefix="JWT_")


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration settings."""

    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= threshold_high)",
    )
    threshold_mid: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (score >= threshold_mid)",
    )
    threshold_low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= threshold_low)",
    )
    tolerance_price: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance percentage",
    )

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, text)",
    )

    model_config = SettingsConfigDict(env_prefix="LOG_")


class AppSettings(BaseSettings):
    """Main application settings."""

    app_name: str = Field(default="AP Automation Core Engine", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_description: str = Field(
        default="AP Automation Core Engine for FinaRo - Invoice Matching System",
        description="Application description",
    )
    debug: bool = Field(default=False, description="Debug mode")
    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class Settings(BaseSettings):
    """Combined settings for the application."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    thresholds: ThresholdSettings = Field(default_factory=ThresholdSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    app: AppSettings = Field(default_factory=AppSettings)

    @classmethod
    def from_env(cls, prefix: Optional[str] = None) -> "Settings":
        """Load settings from environment variables."""
        return cls()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings.from_env()
