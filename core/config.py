// core/config.py
"""
Configuration management using pydantic-settings.

All configuration is loaded from environment variables.
Never hardcode secrets or configuration values.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async database connection URL for SQLAlchemy",
    )
    database_url_sync: str = Field(
        default="postgresql://apuser:appassword@localhost:5432/apautomation",
        description="Sync database connection URL for Alembic migrations",
    )
    pgbouncer_host: str = Field(
        default="localhost",
        description="PGBouncer host for connection pooling",
    )
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=0)
    echo_sql: bool = Field(default=False)

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)

    model_config = SettingsConfigDict(env_prefix="JWT_")


class MatchingThresholds(BaseSettings):
    """Matching threshold configuration for the decision engine."""

    threshold_high: float = Field(
        default=95.0,
        ge=0,
        le=100,
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: float = Field(
        default=70.0,
        ge=0,
        le=100,
        description="1-click review threshold (percentage)",
    )
    threshold_low: float = Field(
        default=40.0,
        ge=0,
        le=100,
        description="Exception threshold (percentage)",
    )
    tolerance_price: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Quantity match tolerance percentage",
    )

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")


class AppSettings(BaseSettings):
    """Application-level settings."""

    app_name: str = Field(default="AP Automation Engine")
    app_version: str = Field(default="0.1.0")
    environment: Literal["development", "staging", "production", "testing"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    api_v1_prefix: str = Field(default="/api/v1")
    cors_origins: list[str] = Field(default=["*"])
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("environment")
    @classmethod
    def set_debug_mode(cls, v: str) -> str:
        """Automatically set debug mode based on environment."""
        return v


class Settings(
    DatabaseSettings,
    JWTSettings,
    MatchingThresholds,
    AppSettings,
):
    """Combined settings class that inherits from all configuration sections."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()


# Global settings instance
settings = get_settings()
