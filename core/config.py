// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Any

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
    environment: str = Field(default="development", description="Runtime environment")
    app_name: str = Field(default="AP Automation Engine", description="Application name")
    debug: bool = Field(default=False, description="Debug mode flag")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async database connection URL",
    )
    sync_database_url: str = Field(
        default="postgresql+psycopg2://apuser:appassword@localhost:5432/apautomation",
        description="Sync database connection URL (for Alembic migrations)",
    )
    database_pool_size: int = Field(default=20, ge=1, description="Connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Max pool overflow")
    database_pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL statements")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production-minimum-32-chars",
        description="JWT signing secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Access token expiry in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, ge=1, description="Refresh token expiry in days"
    )

    # Matching Engine Thresholds (0-100)
    threshold_high: int = Field(
        default=90, ge=0, le=100, description="Auto-approve threshold"
    )
    threshold_mid: int = Field(
        default=70, ge=0, le=100, description="One-click review threshold"
    )
    threshold_low: int = Field(
        default=50, ge=0, le=100, description="Exception threshold"
    )

    # Tolerance Settings (percentages)
    tolerance_price: float = Field(
        default=5.0, ge=0, description="Price match tolerance percentage"
    )
    tolerance_qty: float = Field(
        default=10.0, ge=0, description="Quantity match tolerance percentage"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else []

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return self.cors_origins

    def get_database_pool_config(self) -> dict[str, Any]:
        """Get database pool configuration dictionary."""
        return {
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_timeout": self.database_pool_timeout,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return settings


# Convenience function for dependency injection
def get_settings_dep() -> Settings:
    """FastAPI dependency for settings injection."""
    return get_settings()
