# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
Never hardcode sensitive values.
"""

from functools import lru_cache
from typing import Any

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
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/apautomation",
        description="PostgreSQL connection string for async operations",
    )
    database_echo: bool = False

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="changeme-in-production",
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Matching Thresholds
    threshold_high: float = Field(
        default=90.0,
        ge=0,
        le=100,
        description="Auto-approve threshold percentage",
    )
    threshold_mid: float = Field(
        default=70.0,
        ge=0,
        le=100,
        description="1-click review threshold percentage",
    )
    threshold_low: float = Field(
        default=50.0,
        ge=0,
        le=100,
        description="Exception threshold percentage",
    )

    # Tolerance Settings
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

    # PGBouncer (optional)
    pgbo_host: str | None = None
    pgbo_port: int | None = None

    @property
    def effective_database_url(self) -> str:
        """Return database URL, using PGBouncer if configured."""
        if self.pgbo_host and self.pgbo_port:
            base = f"postgresql+asyncpg://{self.pgbo_host}:{self.pgbo_port}"
            db_path = self.database_url.split("/")[-1]
            return f"{base}/{db_path}"
        return self.database_url

    @property
    def sync_database_url(self) -> str:
        """Return synchronous database URL for Alembic migrations."""
        url = self.database_url
        return url.replace("postgresql+asyncpg://", "postgresql://")

    def get_threshold_decision(self, score: float) -> str:
        """Determine decision based on matching score.

        Args:
            score: Matching score percentage (0-100)

        Returns:
            Decision string: 'AUTO_APPROVED', 'REVIEW', or 'EXCEPTION'
        """
        if score >= self.threshold_high:
            return "AUTO_APPROVED"
        elif score >= self.threshold_mid:
            return "REVIEW"
        else:
            return "EXCEPTION"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
