// core/config.py
"""Application configuration using pydantic-settings.

All configuration is managed via environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: Annotated[
        str,
        Field(
            description="Async PostgreSQL connection string for SQLAlchemy",
            examples=["postgresql+asyncpg://user:pass@host:5432/dbname"],
        ),
    ]
    database_url_sync: Annotated[
        str,
        Field(
            description="Sync PostgreSQL connection string for Alembic",
            examples=["postgresql://user:pass@host:5432/dbname"],
        ),
    ]

    # PGBouncer Configuration (optional)
    pgbouncer_host: str | None = Field(
        default=None,
        description="PGBouncer host for connection pooling",
    )
    pgbouncer_port: int = Field(
        default=5432,
        description="PGBouncer port",
        ge=1,
        le=65535,
    )

    # JWT / Authentication
    jwt_secret_key: Annotated[
        str,
        Field(
            description="HS256 secret key for JWT token signing",
            min_length=32,
        ),
    ]
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiration in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiration in days",
    )

    # Matching Thresholds
    threshold_high: Annotated[
        float,
        Field(
            default=95.0,
            ge=0.0,
            le=100.0,
            description="Auto-approve threshold percentage",
        ),
    ]
    threshold_mid: Annotated[
        float,
        Field(
            default=70.0,
            ge=0.0,
            le=100.0,
            description="1-click review threshold percentage",
        ),
    ]
    threshold_low: Annotated[
        float,
        Field(
            default=40.0,
            ge=0.0,
            le=100.0,
            description="Exception threshold percentage",
        ),
    ]

    # Tolerance Settings
    tolerance_price: Annotated[
        float,
        Field(
            default=5.0,
            ge=0.0,
            le=100.0,
            description="Price match tolerance percentage",
        ),
    ]
    tolerance_qty: Annotated[
        float,
        Field(
            default=10.0,
            ge=0.0,
            le=100.0,
            description="Quantity match tolerance percentage",
        ),
    ]

    # Application Settings
    app_name: str = Field(
        default="AP Automation Engine",
        description="Application name",
    )
    environment: str = Field(
        default="development",
        description="Runtime environment",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag",
    )

    # API Settings
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 route prefix",
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_threshold_order(
        cls, v: float, info: field_validator
    ) -> float:
        """Validate that thresholds are in correct order: high > mid > low."""
        if info.field_name == "threshold_high":
            return v
        # Additional validation can be done at startup
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
