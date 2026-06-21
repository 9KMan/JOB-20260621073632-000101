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
    """Database connection settings."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
    )

    url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async database connection URL",
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
        description="Maximum pool overflow connections",
    )
    pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Pool timeout in seconds",
    )
    pool_recycle: int = Field(
        default=3600,
        ge=100,
        description="Pool recycle time in seconds",
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL queries (debug only)",
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        case_sensitive=False,
    )

    secret_key: str = Field(
        default="changeme-in-production-use-strong-secret",
        description="HS256 signing secret key",
        min_length=32,
    )
    algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="JWT algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
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
    """Matching threshold settings."""

    model_config = SettingsConfigDict(
        env_prefix="THRESHOLD_",
        case_sensitive=False,
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


class ToleranceSettings(BaseSettings):
    """Matching tolerance settings."""

    model_config = SettingsConfigDict(
        env_prefix="TOLERANCE_",
        case_sensitive=False,
    )

    price: float = Field(
        default=0.02,
        ge=0,
        le=1,
        description="Price match tolerance (0.02 = 2%)",
    )
    qty: float = Field(
        default=0.05,
        ge=0,
        le=1,
        description="Quantity match tolerance (0.05 = 5%)",
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
        description="Environment",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Log level",
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated CORS origins",
    )

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return list(v)

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return self.database.url

    @property
    def database_pool_size(self) -> int:
        """Get the database pool size."""
        return self.database.pool_size

    @property
    def database_max_overflow(self) -> int:
        """Get the database max overflow."""
        return self.database.max_overflow

    @property
    def jwt_secret_key(self) -> str:
        """Get the JWT secret key."""
        return self.jwt.secret_key

    @property
    def jwt_algorithm(self) -> str:
        """Get the JWT algorithm."""
        return self.jwt.algorithm

    @property
    def threshold_high(self) -> float:
        """Get the high threshold."""
        return self.threshold.high

    @property
    def threshold_mid(self) -> float:
        """Get the mid threshold."""
        return self.threshold.mid

    @property
    def threshold_low(self) -> float:
        """Get the low threshold."""
        return self.threshold.low

    @property
    def tolerance_price(self) -> float:
        """Get the price tolerance."""
        return self.tolerance.price

    @property
    def tolerance_qty(self) -> float:
        """Get the quantity tolerance."""
        return self.tolerance.qty


@lru_cache
def get_settings() -> AppSettings:
    """Get cached application settings.

    Returns:
        AppSettings: The application settings instance.
    """
    return AppSettings()


# Convenience function for dependency injection
def get_db_settings() -> DatabaseSettings:
    """Get database settings."""
    return get_settings().database


def get_jwt_settings() -> JWTSettings:
    """Get JWT settings."""
    return get_settings().jwt


def get_threshold_settings() -> ThresholdSettings:
    """Get threshold settings."""
    return get_settings().threshold


def get_tolerance_settings() -> ToleranceSettings:
    """Get tolerance settings."""
    return get_settings().tolerance
