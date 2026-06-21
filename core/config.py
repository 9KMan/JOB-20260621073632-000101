# core/config.py
"""Application configuration using pydantic-settings.

Configuration is loaded from environment variables with validation and
type coercion applied automatically.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:apsecret@localhost:5432/apautomation",
        description="Async PostgreSQL connection URL for SQLAlchemy",
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=0)
    DATABASE_ECHO: bool = Field(default=False, description="SQL echo mode for debugging")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    JWT_SECRET_KEY: str = Field(
        default="changeme-in-production",
        description="Secret key for HS256 JWT signing",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is sufficiently long for security."""
        if len(v) < 32 and v == "changeme-in-production":
            return v  # Allow default in development
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    model_config = SettingsConfigDict(env_prefix="JWT_")


class ThresholdSettings(BaseSettings):
    """Matching engine threshold settings."""

    THRESHOLD_HIGH: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold (percentage)",
    )
    THRESHOLD_MID: int = Field(
        default=70,
        ge=0,
        le=100,
        description="One-click review threshold (percentage)",
    )
    THRESHOLD_LOW: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Exception threshold (percentage)",
    )

    @field_validator("THRESHOLD_HIGH", "THRESHOLD_MID", "THRESHOLD_LOW")
    @classmethod
    def validate_thresholds(cls, v: int) -> int:
        """Ensure thresholds are within valid range."""
        if v < 0 or v > 100:
            raise ValueError("Threshold must be between 0 and 100")
        return v

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")


class ToleranceSettings(BaseSettings):
    """Matching tolerance settings for price and quantity."""

    TOLERANCE_PRICE: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Price match tolerance percentage",
    )
    TOLERANCE_QTY: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Quantity match tolerance percentage",
    )

    model_config = SettingsConfigDict(env_prefix="TOLERANCE_")


class AppSettings(BaseSettings):
    """General application settings."""

    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    API_PORT: int = Field(default=8000, ge=1, le=65535)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    API_V1_PREFIX: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="AP Automation Engine")
    PROJECT_VERSION: str = Field(default="0.1.0")

    model_config = SettingsConfigDict(env_prefix="")


class Settings(
    DatabaseSettings,
    JWTSettings,
    ThresholdSettings,
    ToleranceSettings,
    AppSettings,
):
    """Combined application settings.

    All settings are loaded from environment variables with appropriate
    prefixes and validation applied.
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

    Note:
        Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
