# core/config.py
"""
Environment configuration via pydantic-settings.

All configuration is loaded from environment variables (no hardcoded secrets).
Supports development, testing, and production environments.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    PostgresDsn,
    RedisDsn,
    field_validator,
    model_validator,
    SecretStr,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database connection configuration."""

    url: PostgresDsn = Field(
        default=PostgresDsn(
            "postgresql+asyncpg://apuser:appass@localhost:5432/apautomation"
        ),
        description="Async PostgreSQL connection URL for SQLAlchemy.",
    )
    pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size.")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Max pool overflow connections.")
    pool_timeout: int = Field(default=30, ge=5, description="Pool timeout in seconds.")
    pool_recycle: int = Field(default=3600, ge=300, description="Pool recycle in seconds.")
    echo: bool = Field(default=False, description="Echo SQL queries (debug only).")

    @property
    def sync_url(self) -> str:
        """Return synchronous driver URL for Alembic migrations."""
        return str(self.url).replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")


class JWTSettings(BaseModel):
    """JWT authentication configuration."""

    secret_key: SecretStr = Field(
        default=SecretStr("insecure-dev-secret-change-in-production"),
        description="Secret key for HS256 JWT signing. MUST be overridden in production.",
    )
    algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="JWT algorithm.",
    )
    access_token_expire_minutes: int = Field(
        default=30, ge=5, le=1440, description="Access token expiry in minutes."
    )
    refresh_token_expire_days: int = Field(
        default=7, ge=1, le=30, description="Refresh token expiry in days."
    )


class MatchingThresholds(BaseModel):
    """Matching score thresholds for routing decisions."""

    high: float = Field(default=95.0, ge=0, le=100, description="Auto-approve threshold (%)")
    mid: float = Field(default=75.0, ge=0, le=100, description="One-click review threshold (%)")
    low: float = Field(default=50.0, ge=0, le=100, description="Exception threshold (%)")

    @model_validator(mode="after")
    def validate_thresholds(self) -> MatchingThresholds:
        """Ensure thresholds are in descending order."""
        if not (self.high >= self.mid >= self.low):
            raise ValueError("Threshold values must satisfy: high >= mid >= low")
        return self


class ToleranceSettings(BaseModel):
    """Matching tolerance settings for price and quantity comparisons."""

    price: float = Field(default=0.02, ge=0, le=1, description="Price tolerance as decimal (2% default).")
    qty: float = Field(default=0.05, ge=0, le=1, description="Quantity tolerance as decimal (5% default).")


class CorsSettings(BaseModel):
    """CORS configuration."""

    allowed_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins.",
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS.")
    allowed_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods.",
    )
    allowed_headers: list[str] = Field(
        default=["*"],
        description="Allowed HTTP headers.",
    )

    @property
    def is_allow_all(self) -> bool:
        """Check if CORS allows all origins."""
        return "*" in self.allowed_origins


class ServerSettings(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host.")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port.")
    workers: int = Field(default=4, ge=1, le=16, description="Number of workers.")
    reload: bool = Field(default=False, description="Enable auto-reload (dev only).")
    log_level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info", description="Log level."
    )


class Settings(BaseSettings):
    """
    Main application settings.

    All values are loaded from environment variables with sensible defaults
    for development. Production deployments MUST override sensitive values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(default="AP Automation Engine", description="Application name.")
    app_version: str = Field(default="0.1.0", description="Application version.")
    debug: bool = Field(default=False, description="Debug mode flag.")
    environment: Literal["development", "testing", "staging", "production"] = Field(
        default="development",
        description="Deployment environment.",
    )

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    thresholds: MatchingThresholds = Field(default_factory=MatchingThresholds)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)

    # Redis (optional, for Celery/broker)
    redis_url: RedisDsn | None = Field(
        default=None,
        description="Redis URL for task queue (optional).",
    )
    redis_enabled: bool = Field(
        default=False,
        description="Enable Redis-based task queue.",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        allowed = {"development", "testing", "staging", "production"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v_lower

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"

    def model_dump_env(self) -> dict[str, str]:
        """Dump settings as environment variable dict (for subprocesses)."""
        result = {}
        result["DATABASE_URL"] = str(self.database.url)
        result["DATABASE_POOL_SIZE"] = str(self.database.pool_size)
        result["DATABASE_MAX_OVERFLOW"] = str(self.database.max_overflow)
        result["JWT_SECRET_KEY"] = self.jwt.secret_key.get_secret_value()
        result["JWT_ALGORITHM"] = self.jwt.algorithm
        result["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = str(self.jwt.access_token_expire_minutes)
        result["THRESHOLD_HIGH"] = str(self.thresholds.high)
        result["THRESHOLD_MID"] = str(self.thresholds.mid)
        result["THRESHOLD_LOW"] = str(self.thresholds.low)
        result["TOLERANCE_PRICE"] = str(self.tolerance.price)
        result["TOLERANCE_QTY"] = str(self.tolerance.qty)
        result["LOG_LEVEL"] = self.server.log_level
        result["ENVIRONMENT"] = self.environment
        return result


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache for singleton pattern — settings are loaded once
    and reused across the application lifetime.
    """
    return Settings()


# Global settings instance
settings = get_settings()
