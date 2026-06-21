# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, field_validator
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
    app_name: str = Field(default="AP Automation Engine", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment: development|staging|production")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://appuser:apppassword@localhost:5432/apautomation",
        description="PostgreSQL async database URL",
    )
    database_pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")
    database_pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    database_pool_recycle: int = Field(default=3600, ge=0, description="Pool recycle time in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # PGBouncer (optional)
    pgbouncer_host: str | None = Field(default=None, description="PGBouncer host")
    pgbouncer_port: int = Field(default=6432, ge=1, le=65535, description="PGBouncer port")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="JWT signing secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, ge=1, le=1440, description="Access token expiry in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, ge=1, le=30, description="Refresh token expiry in days"
    )

    # Matching Thresholds (0.0 - 1.0)
    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold",
    )
    threshold_mid: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold",
    )
    threshold_low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold",
    )

    # Tolerance Settings
    tolerance_price: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as decimal (0.05 = 5%)",
    )
    tolerance_qty: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as decimal (0.10 = 10%)",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_allow_methods: list[str] = Field(
        default=["*"], description="Allowed HTTP methods for CORS"
    )
    cors_allow_headers: list[str] = Field(
        default=["*"], description="Allowed HTTP headers for CORS"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, ge=1, description="Max requests per window")
    rate_limit_window: int = Field(default=60, ge=1, description="Rate limit window in seconds")

    # Redis (optional)
    redis_url: str | None = Field(default=None, description="Redis URL for caching")

    # OpenTelemetry
    otel_enabled: bool = Field(default=False, description="Enable OpenTelemetry tracing")
    otel_service_name: str = Field(default="ap-automation-engine", description="OTEL service name")
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None, description="OTEL exporter endpoint"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper_v

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        """Validate threshold is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {v}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    def validate_thresholds_order(self) -> None:
        """Validate that thresholds are in correct order: HIGH > MID > LOW."""
        if not (self.threshold_high > self.threshold_mid > self.threshold_low):
            raise ValueError(
                f"Threshold order invalid: HIGH({self.threshold_high}) > "
                f"MID({self.threshold_mid}) > LOW({self.threshold_low})"
            )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.
    """
    settings = Settings()
    settings.validate_thresholds_order()
    return settings


# Type alias for dependency injection
SettingsDep = Annotated[Settings, None]
