# core/config.py
"""Application configuration using pydantic-settings.

All configuration is managed via environment variables.
"""

from functools import lru_cache
from typing import List

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
    app_name: str = Field(default="ap-automation-engine", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ap_automation",
        description="Async database connection URL",
    )
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Max pool overflow")
    database_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Matching Engine Thresholds (percentages)
    threshold_high: int = Field(
        default=90,
        ge=0,
        le=100,
        description="Auto-approve threshold percentage",
    )
    threshold_mid: int = Field(
        default=70,
        ge=0,
        le=100,
        description="1-click review threshold percentage",
    )
    threshold_low: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Exception threshold percentage",
    )

    # Tolerance Settings (percentages)
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

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    # Alembic
    alembic_config: str = Field(default="alembic.ini", description="Alembic config file path")

    @property
    def thresholds(self) -> dict:
        """Return thresholds as a sorted dictionary."""
        return {
            "high": self.threshold_high,
            "mid": self.threshold_mid,
            "low": self.threshold_low,
        }

    @property
    def tolerances(self) -> dict:
        """Return tolerances as a dictionary."""
        return {
            "price": self.tolerance_price,
            "qty": self.tolerance_qty,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
