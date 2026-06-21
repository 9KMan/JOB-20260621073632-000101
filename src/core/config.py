# src/core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
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
    app_name: str = "AP Automation Core"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        validation_alias="DATABASE_URL",
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_echo: bool = False

    # Authentication
    jwt_secret_key: str = Field(
        default="change-me-in-production-32-chars-min",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Matching Thresholds
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
        description="One-click review threshold (score >= threshold_mid)",
    )
    threshold_low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= threshold_low)",
    )

    # Matching Tolerances
    tolerance_price: float = Field(
        default=5.0,
        ge=0.0,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0.0,
        description="Quantity match tolerance percentage",
    )

    # PGBouncer (optional override)
    pgbouncer_host: str | None = Field(default=None, validation_alias="PGBOUNCER_HOST")
    pgbouncer_port: int = 6432

    @field_validator("threshold_high", "threshold_mid", "threshold_low", mode="before")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        """Ensure thresholds are between 0 and 1."""
        if isinstance(v, str):
            v = float(v)
        return max(0.0, min(1.0, v))

    def get_pg_url(self) -> str:
        """Get PostgreSQL URL, respecting PGBouncer if configured."""
        if self.pgbouncer_host:
            return self.database_url.replace(
                "@", f"@{self.pgbouncer_host}:{self.pgbouncer_port}/"
            )
        return self.database_url

    @property
    def async_database_url(self) -> str:
        """Ensure asyncpg driver is used."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
