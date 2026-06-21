# core/config.py
"""Application configuration using pydantic-settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="")

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    pgbouncer_host: Optional[str] = Field(
        default=None,
        description="PGBouncer host override",
    )
    pgbouncer_port: int = Field(
        default=5432,
        description="PGBouncer port",
    )
    echo_sql: bool = Field(
        default=False,
        description="Echo SQL statements (debug mode)",
    )
    pool_size: int = Field(
        default=20,
        description="Connection pool size",
    )
    max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections",
    )
    pool_timeout: int = Field(
        default=30,
        description="Pool timeout in seconds",
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(env_prefix="")

    jwt_secret_key: str = Field(
        default="changeme-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiry in minutes",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= this value)",
    )
    threshold_mid: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (score >= this value)",
    )
    threshold_low: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= this value)",
    )


class ToleranceSettings(BaseSettings):
    """Matching tolerance configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    tolerance_price: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as decimal (2% = 0.02)",
    )
    tolerance_qty: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as decimal (10% = 0.10)",
    )


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

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
        description="Debug mode flag",
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 prefix",
    )

    # Compose sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)


@lru_cache
def get_settings() -> AppSettings:
    """Get cached application settings singleton."""
    return AppSettings()


settings = get_settings()
