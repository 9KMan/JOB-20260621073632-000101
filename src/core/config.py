# src/core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apautomation:apautomation_secret@localhost:5432/apautomation",
        description="PostgreSQL database connection URL (async)",
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=50)
    database_pool_timeout: int = Field(default=30, ge=1)
    database_pool_recycle: int = Field(default=3600, ge=0)

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="dev_secret_key_change_in_production",
        description="Secret key for HS256 JWT signing",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)

    model_config = SettingsConfigDict(env_prefix="JWT_")


class MatchingSettings(BaseSettings):
    """Matching engine threshold and tolerance settings."""

    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= threshold_high)",
    )
    threshold_mid: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (score >= threshold_mid)",
    )
    threshold_low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= threshold_low)",
    )
    tolerance_price: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as decimal (2% = 0.02)",
    )
    tolerance_qty: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as decimal (5% = 0.05)",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {v}")
        return v

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")


class AppSettings(BaseSettings):
    """Application-level settings."""

    app_name: str = Field(default="AP Automation Core Engine")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(env_prefix="")


class Settings(BaseSettings):
    """Combined application settings."""

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    matching: MatchingSettings = Field(default_factory=MatchingSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url_sync(self) -> str:
        """Return synchronous database URL for Alembic."""
        return self.database.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()

# Type aliases for convenience
DbSettings = Annotated[DatabaseSettings, Field(title="Database Settings")]
JwtSettings = Annotated[JWTSettings, Field(title="JWT Settings")]
MatchSettings = Annotated[MatchingSettings, Field(title="Matching Settings")]
AppConfig = Annotated[AppSettings, Field(title="Application Settings")]
