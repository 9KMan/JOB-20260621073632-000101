# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async database connection URL",
    )
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    echo: bool = Field(default=False, description="Echo SQL queries")


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str = Field(
        default="supersecretkey-change-in-production",
        description="HS256 signing secret key",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    expiration_minutes: int = Field(default=30, description="Token expiration in minutes")


class ThresholdSettings(BaseSettings):
    """Matching threshold settings."""

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")

    high: float = Field(default=95.0, description="Auto-approve threshold (0-100)")
    mid: float = Field(default=75.0, description="1-click review threshold (0-100)")
    low: float = Field(default=50.0, description="Exception threshold (0-100)")


class ToleranceSettings(BaseSettings):
    """Matching tolerance settings."""

    model_config = SettingsConfigDict(env_prefix="TOLERANCE_")

    price: float = Field(default=2.0, description="Price match tolerance percentage")
    qty: float = Field(default=5.0, description="Quantity match tolerance percentage")


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = Field(default="AP Automation Engine")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()


settings = get_settings()
