# core/config.py
"""Application configuration loaded from environment variables via pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: Annotated[
        PostgresDsn,
        Field(
            description="Async database connection string (asyncpg driver)",
            default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        ),
    ]

    url_sync: Annotated[
        PostgresDsn,
        Field(
            description="Sync database connection string (used by Alembic migrations)",
            default="postgresql://apuser:appassword@localhost:5432/apautomation",
        ),
    ]

    echo: Annotated[
        bool,
        Field(
            description="Echo SQL queries to stdout (useful for debugging)",
            default=False,
        ),
    ]

    pool_size: Annotated[int, Field(description="Connection pool size", default=20)]
    max_overflow: Annotated[int, Field(description="Max overflow connections", default=10)]
    pool_timeout: Annotated[int, Field(description="Pool timeout in seconds", default=30)]
    pool_recycle: Annotated[int, Field(description="Connection recycle time in seconds", default=3600)]
    pool_pre_ping: Annotated[bool, Field(description="Check connection health before use", default=True)]


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: Annotated[
        str,
        Field(
            description="Secret key for HS256 JWT signing",
            default="dev-secret-key-change-in-production",
        ),
    ]

    algorithm: Annotated[str, Field(description="JWT signing algorithm", default="HS256")]

    access_token_expire_minutes: Annotated[
        int,
        Field(description="Access token expiry in minutes", default=30),
    ]

    refresh_token_expire_days: Annotated[
        int,
        Field(description="Refresh token expiry in days", default=7),
    ]


class MatchingSettings(BaseSettings):
    """AP matching engine threshold and tolerance settings."""

    model_config = SettingsConfigDict(env_prefix="")

    # Score thresholds (0.0 – 1.0)
    threshold_high: Annotated[
        float,
        Field(
            description="Auto-approve threshold: matches above this score auto-approve",
            ge=0.0,
            le=1.0,
            default=0.95,
        ),
    ]

    threshold_mid: Annotated[
        float,
        Field(
            description="One-click review threshold: matches between mid and high go to review",
            ge=0.0,
            le=1.0,
            default=0.70,
        ),
    ]

    threshold_low: Annotated[
        float,
        Field(
            description="Exception threshold: matches below this score become exceptions",
            ge=0.0,
            le=1.0,
            default=0.40,
        ),
    ]

    # Tolerance margins
    tolerance_price: Annotated[
        float,
        Field(
            description="Price match tolerance as decimal (0.02 = 2%)",
            ge=0.0,
            le=1.0,
            default=0.02,
        ),
    ]

    tolerance_qty: Annotated[
        float,
        Field(
            description="Quantity match tolerance as decimal (0.05 = 5%)",
            ge=0.0,
            le=1.0,
            default=0.05,
        ),
    ]


class AppSettings(BaseSettings):
    """Application-level settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    environment: Annotated[
        str,
        Field(description="Runtime environment", default="development"),
    ]

    log_level: Annotated[
        str,
        Field(description="Logging level", default="INFO"),
    ]

    api_v1_prefix: Annotated[str, Field(description="API v1 route prefix", default="/api/v1")]

    app_name: Annotated[str, Field(description="Application name", default="AP Automation Engine")]

    debug: Annotated[bool, Field(description="Debug mode", default=False)]

    cors_origins: Annotated[
        list[str],
        Field(
            description="Allowed CORS origins",
            default=["http://localhost:3000", "http://localhost:8080"],
        ),
    ]


class Settings(BaseSettings):
    """Aggregated application settings."""

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    matching: MatchingSettings = Field(default_factory=MatchingSettings)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


settings = get_settings()
