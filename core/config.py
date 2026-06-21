// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded values are used.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async database connection URL",
    )
    database_url_sync: str = Field(
        default="postgresql://apuser:appass@localhost:5432/apautomation",
        description="Sync database connection URL for Alembic migrations",
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=50)
    database_pool_timeout: int = Field(default=30, ge=1)
    database_pool_recycle: int = Field(default=3600, ge=100)
    database_echo: bool = Field(default=False)

    @field_validator("database_url", "database_url_sync", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL has proper format."""
        if v and not v.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite://")):
            raise ValueError("Database URL must start with postgresql:// or postgresql+asyncpg://")
        return v


class PGbouncerSettings(BaseSettings):
    """PGBouncer connection settings (optional layer)."""

    pgbouncer_host: str | None = Field(default="localhost")
    pgbouncer_port: int = Field(default=5432, ge=1, le=65535)
    use_pgbouncer: bool = Field(default=False)


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration settings."""

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


class ToleranceSettings(BaseSettings):
    """Matching tolerance configuration settings."""

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


class ApplicationSettings(BaseSettings):
    """Main application settings."""

    app_name: str = Field(default="AP Automation Engine")
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(default="AP Automation Core Engine for FinaRo")
    environment: Literal["development", "staging", "production"] = Field(default="development")
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    # CORS settings
    cors_origins: list[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    # API settings
    api_v1_prefix: str = Field(default="/api/v1")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")


class Settings(
    DatabaseSettings,
    PGbouncerSettings,
    JWTSettings,
    ThresholdSettings,
    ToleranceSettings,
    ApplicationSettings,
):
    """Combined settings class for the application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    This function uses lru_cache to ensure settings are only
    loaded once and cached for subsequent calls.

    Returns:
        Settings: The application settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
