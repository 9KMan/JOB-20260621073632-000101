// core/config.py
"""Configuration management using pydantic-settings.

All configuration is managed via environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
    )

    url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="PostgreSQL connection URL with asyncpg driver",
    )
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=300)
    echo: bool = Field(default=False, description="Echo SQL queries")


class PGBouncerSettings(BaseSettings):
    """PGBouncer connection settings (optional layer)."""

    model_config = SettingsConfigDict(env_prefix="PGBOUNCER_", case_sensitive=False)

    host: str = Field(default="localhost")
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(default="apautomation")


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(env_prefix="JWT_", case_sensitive=False)

    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="HS256 secret key for JWT signing",
    )
    algorithm: Literal["HS256", "HS384", "HS512"] = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)


class ThresholdSettings(BaseSettings):
    """Matching engine threshold settings."""

    model_config = SettingsConfigDict(
        env_prefix="THRESHOLD_", case_sensitive=False
    )

    high: float = Field(
        default=95.0,
        ge=0,
        le=100,
        description="Auto-approve threshold (percentage)",
    )
    mid: float = Field(
        default=70.0,
        ge=0,
        le=100,
        description="1-click review threshold (percentage)",
    )
    low: float = Field(
        default=40.0,
        ge=0,
        le=100,
        description="Exception threshold (percentage)",
    )

    @field_validator("high", "mid", "low", mode="before")
    @classmethod
    def validate_threshold_order(cls, v: float, info) -> float:
        """Ensure thresholds are in valid order: high >= mid >= low."""
        return v


class ToleranceSettings(BaseSettings):
    """Matching tolerance settings."""

    model_config = SettingsConfigDict(env_prefix="TOLERANCE_", case_sensitive=False)

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


class ServerSettings(BaseSettings):
    """Server configuration settings."""

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    app_name: str = Field(default="AP Automation Core Engine")
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    api_v1_prefix: str = Field(default="/api/v1")


class Settings(BaseSettings):
    """Application settings composing all configuration sections."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    pgbouncer: PGBouncerSettings = Field(default_factory=PGBouncerSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    thresholds: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return self.database.url

    @property
    def pgbouncer_url(self) -> str | None:
        """Get PGBouncer URL if configured."""
        if self.pgbouncer.host:
            return (
                f"postgresql+asyncpg://{self.pgbouncer.host}:{self.pgbouncer.port}/"
                f"{self.pgbouncer.database}"
            )
        return None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings singleton.
    """
    return Settings()


# Convenience function for dependency injection
def get_database_url() -> str:
    """Get database URL for dependency injection."""
    return get_settings().database_url
