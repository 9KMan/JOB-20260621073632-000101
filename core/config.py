# core/config.py
"""Configuration management using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ap_automation",
        description="PostgreSQL database connection URL for async SQLAlchemy",
    )
    PGBOUNCER_HOST: str = Field(default="localhost", description="PGBouncer host address")
    PGBOUNCER_PORT: int = Field(default=5432, ge=1, le=65535, description="PGBouncer port")
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, description="Max pool overflow connections")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=0, description="Pool recycle time in seconds")
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries (debug only)")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql+asyncpg://", "postgresql://")):
            raise ValueError("DATABASE_URL must start with postgresql+asyncpg:// or postgresql://")
        return v


class JWTSettings(BaseSettings):
    """JWT authentication configuration."""

    JWT_SECRET_KEY: str = Field(
        default="changeme-in-production",
        description="Secret key for HS256 JWT signing",
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="JWT algorithm",
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiry in minutes",
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiry in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching engine threshold configuration."""

    THRESHOLD_HIGH: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= THRESHOLD_HIGH)",
    )
    THRESHOLD_MID: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (score >= THRESHOLD_MID)",
    )
    THRESHOLD_LOW: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= THRESHOLD_LOW)",
    )

    @field_validator("THRESHOLD_HIGH", "THRESHOLD_MID", "THRESHOLD_LOW", mode="after")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        """Ensure thresholds are valid values."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v


class ToleranceSettings(BaseSettings):
    """Tolerance settings for matching comparisons."""

    TOLERANCE_PRICE: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as decimal (2% = 0.02)",
    )
    TOLERANCE_QTY: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as decimal (10% = 0.10)",
    )

    @field_validator("TOLERANCE_PRICE", "TOLERANCE_QTY", mode="after")
    @classmethod
    def validate_tolerance(cls, v: float) -> float:
        """Ensure tolerance values are valid percentages."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Tolerance must be between 0.0 and 1.0")
        return v


class AppSettings(BaseSettings):
    """Application-level settings."""

    APP_NAME: str = Field(default="AP Automation", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 route prefix")
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="CORS allowed origins",
    )
    DEBUG: bool = Field(default=False, description="Debug mode flag")


class Settings(
    DatabaseSettings,
    JWTSettings,
    ThresholdSettings,
    ToleranceSettings,
    AppSettings,
):
    """Combined settings class for the entire application.

    Loads all configuration from environment variables.
    All secrets and configuration must be provided via env vars.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()
