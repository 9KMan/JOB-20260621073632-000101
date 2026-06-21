# core/config.py
"""
Configuration management using pydantic-settings.

All configuration is loaded from environment variables.
Never hardcode secrets or connection strings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
    )

    url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async database URL for SQLAlchemy async engine",
    )

    sync_url: str = Field(
        default="postgresql+psycopg2://apuser:appassword@localhost:5432/apautomation",
        description="Sync database URL for Alembic migrations",
    )

    pool_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Connection pool size",
    )

    max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum overflow connections",
    )

    pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Pool timeout in seconds",
    )

    pool_recycle: int = Field(
        default=3600,
        ge=0,
        description="Pool recycle time in seconds (0 = never)",
    )

    echo: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)",
    )

    @field_validator("url", "sync_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL has proper scheme."""
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v


class PgbouncerSettings(BaseSettings):
    """PGBouncer connection settings (optional)."""

    model_config = SettingsConfigDict(
        env_prefix="PGBOUNCER_",
        case_sensitive=False,
    )

    host: str = Field(
        default="localhost",
        description="PGBouncer host",
    )

    port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="PGBouncer port",
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        case_sensitive=False,
    )

    secret_key: str = Field(
        default="dev-secret-key-change-in-production-minimum-32-chars",
        description="Secret key for JWT signing (HS256)",
        min_length=32,
    )

    algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="JWT algorithm",
    )

    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiry in minutes",
    )

    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiry in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration."""

    model_config = SettingsConfigDict(
        env_prefix="THRESHOLD_",
        case_sensitive=False,
    )

    high: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold (percentage)",
    )

    mid: int = Field(
        default=70,
        ge=0,
        le=100,
        description="One-click review threshold (percentage)",
    )

    low: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Exception threshold (percentage)",
    )

    @field_validator("high", "mid", "low", mode="after")
    @classmethod
    def validate_threshold_order(cls, v: int, info) -> int:
        """Ensure thresholds are in valid range."""
        if not 0 <= v <= 100:
            raise ValueError(f"{info.field_name} must be between 0 and 100")
        return v


class ToleranceSettings(BaseSettings):
    """Matching tolerance configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TOLERANCE_",
        case_sensitive=False,
    )

    price: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Price match tolerance percentage",
    )

    quantity: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Quantity match tolerance percentage",
    )


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
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
        description="Debug mode",
    )

    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment",
    )

    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
    )

    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS",
    )

    cors_allow_methods: list[str] = Field(
        default=["*"],
        description="Allowed CORS methods",
    )

    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed CORS headers",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Sub-settings
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database connection settings",
    )

    pgbouncer: PgbouncerSettings = Field(
        default_factory=PgbouncerSettings,
        description="PGBouncer connection settings",
    )

    jwt: JWTSettings = Field(
        default_factory=JWTSettings,
        description="JWT authentication settings",
    )

    threshold: ThresholdSettings = Field(
        default_factory=ThresholdSettings,
        description="Matching threshold configuration",
    )

    tolerance: ToleranceSettings = Field(
        default_factory=ToleranceSettings,
        description="Matching tolerance configuration",
    )


@lru_cache
def get_settings() -> AppSettings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are only loaded once
    and reused across the application lifecycle.
    
    Returns:
        AppSettings: The application settings instance.
    """
    return AppSettings()


# Convenience alias
Settings = AppSettings
