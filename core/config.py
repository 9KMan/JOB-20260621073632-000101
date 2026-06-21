# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async PostgreSQL connection URL",
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL queries to stdout",
    )
    pool_size: int = Field(
        default=20,
        ge=1,
        description="Connection pool size",
    )
    max_overflow: int = Field(
        default=10,
        ge=0,
        description="Maximum pool overflow",
    )
    pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Pool timeout in seconds",
    )
    pool_recycle: int = Field(
        default=3600,
        ge=0,
        description="Connection recycle time in seconds",
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str = Field(
        default="changeme-in-production-use-strong-secret",
        description="HS256 secret key for JWT signing",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiry in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        description="Refresh token expiry in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold settings."""

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")

    high: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold percentage",
    )
    mid: int = Field(
        default=70,
        ge=0,
        le=100,
        description="One-click review threshold percentage",
    )
    low: int = Field(
        default=40,
        ge=0,
        le=100,
        description="Exception threshold percentage",
    )


class ToleranceSettings(BaseSettings):
    """Matching tolerance settings."""

    model_config = SettingsConfigDict(env_prefix="TOLERANCE_")

    price: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Price match tolerance percentage",
    )
    qty: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Quantity match tolerance percentage",
    )


class PGBouncerSettings(BaseSettings):
    """PGBouncer connection settings."""

    model_config = SettingsConfigDict(env_prefix="PGBOUNCER_")

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
        description="Debug mode",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 prefix",
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins",
    )

    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database configuration",
    )
    jwt: JWTSettings = Field(
        default_factory=JWTSettings,
        description="JWT configuration",
    )
    threshold: ThresholdSettings = Field(
        default_factory=ThresholdSettings,
        description="Matching threshold configuration",
    )
    tolerance: ToleranceSettings = Field(
        default_factory=ToleranceSettings,
        description="Matching tolerance configuration",
    )
    pgbouncer: PGBouncerSettings = Field(
        default_factory=PGBouncerSettings,
        description="PGBouncer configuration",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper


class Settings(BaseSettings):
    """Aggregated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app: AppSettings = Field(
        default_factory=AppSettings,
        description="Application configuration",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
