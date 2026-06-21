// core/config.py
"""Application settings loaded from environment variables via pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration — all values sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_name: str = Field(default="AP Automation Core", description="Application display name")
    environment: str = Field(default="development", description="deployment environment")
    log_level: str = Field(default="INFO", description="Logging verbosity level")
    debug: bool = Field(default=False, description="Enable debug mode")

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:changeme@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    pgbouncer_host: str = Field(default="localhost", description="PGBouncer host")
    pgbouncer_port: int = Field(default=5432, description="PGBouncer port")
    db_pool_size: int = Field(default=10, description="Connection pool size")
    db_max_overflow: int = Field(default=20, description="Connection pool max overflow")
    db_pool_timeout: int = Field(default=30, description="Connection pool timeout (seconds)")
    db_echo: bool = Field(default=False, description="Echo SQL queries (debug only)")

    # ── JWT / Authentication ────────────────────────────────────────────────────
    jwt_secret_key: str = Field(
        default="change-me-in-production-use-strong-secret-key-256-bits",
        description="HS256 signing secret (min 256 bits)",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Access token expiry (minutes)"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiry (days)"
    )
    bcrypt_rounds: int = Field(default=12, description="bcrypt cost factor")

    # ── Matching Thresholds ─────────────────────────────────────────────────────
    threshold_high: float = Field(
        default=95.0,
        ge=0.0,
        le=100.0,
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="1-click review threshold (percentage)",
    )
    threshold_low: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Exception threshold (percentage)",
    )

    # ── Tolerance Settings ──────────────────────────────────────────────────────
    tolerance_price: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Allowed price variance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Allowed quantity variance percentage",
    )

    # ── Learning Loop ──────────────────────────────────────────────────────────
    learning_confirmed_weight: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Weight for confirmed matches in learning"
    )
    learning_rejected_weight: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Weight for rejected matches in learning"
    )
    learning_promotion_min_confirmations: int = Field(
        default=3, ge=1, description="Min confirmations to promote a cross-reference"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got: {v}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got: {v}")
        return upper

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Convenience type alias for dependency injection
SettingsDep = Annotated[Settings, Field(default_factory=get_settings)]
