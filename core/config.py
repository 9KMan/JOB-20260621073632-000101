# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AP Automation Engine"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False)
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)

    # PGBouncer (optional)
    pgbouncer_host: Optional[str] = Field(default=None)
    pgbouncer_port: int = Field(default=5432)

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # Matching Thresholds
    threshold_high: float = Field(
        default=95.0,
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: float = Field(
        default=70.0,
        description="1-click review threshold (percentage)",
    )
    threshold_low: float = Field(
        default=40.0,
        description="Exception threshold (percentage)",
    )

    # Matching Tolerances
    tolerance_price: float = Field(
        default=5.0,
        description="Price match tolerance (percentage)",
    )
    tolerance_qty: float = Field(
        default=10.0,
        description="Quantity match tolerance (percentage)",
    )

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default=["*"])

    # Logging
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
