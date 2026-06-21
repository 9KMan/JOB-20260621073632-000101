# core/config.py
"""Configuration management for AP Automation Engine.

Uses pydantic-settings for environment variable management with validation.
All configuration is read from environment variables - no hardcoded secrets.
"""

from functools import lru_cache
from typing import Annotated

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
    environment: str = Field(
        default="development",
        description="Application environment: development, staging, production",
    )
    app_name: str = Field(
        default="AP Automation Engine",
        description="Application name for OpenAPI docs",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="PostgreSQL connection string for async SQLAlchemy",
    )
    database_pool_size: int = Field(
        default=20,
        description="Connection pool size",
    )
    database_max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections",
    )
    database_pool_timeout: int = Field(
        default=30,
        description="Pool timeout in seconds",
    )
    pgbouncer_host: str | None = Field(
        default=None,
        description="PGBouncer host for connection pooling",
    )

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-chars",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days",
    )

    # Matching Engine Thresholds
    threshold_high: int = Field(
        default=95,
        description="Auto-approve threshold percentage (0-100)",
        ge=0,
        le=100,
    )
    threshold_mid: int = Field(
        default=70,
        description="One-click review threshold percentage (0-100)",
        ge=0,
        le=100,
    )
    threshold_low: int = Field(
        default=50,
        description="Exception threshold percentage (0-100)",
        ge=0,
        le=100,
    )

    # Matching Tolerances
    tolerance_price: float = Field(
        default=5.0,
        description="Price match tolerance percentage",
        ge=0,
        le=100,
    )
    tolerance_qty: float = Field(
        default=10.0,
        description="Quantity match tolerance percentage",
        ge=0,
        le=100,
    )

    # API
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 route prefix",
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is a known value."""
        allowed = {"development", "staging", "production", "testing"}
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.environment == "testing"

    def get_database_url_with_pgbouncer(self) -> str | None:
        """Get database URL with PGBouncer if configured."""
        if self.pgbouncer_host:
            # PGBouncer uses transaction pooling, modify URL accordingly
            return self.database_url.replace(
                "postgresql+asyncpg://",
                "postgresql+asyncpg://",
            ).replace(
                "@localhost:5432",
                f"@{self.pgbouncer_host}:6432",
            )
        return None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Type alias for dependency injection
SettingsDep = Annotated[Settings, Field(default_factory=get_settings)]
