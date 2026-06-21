# core/config.py
"""Configuration management using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Literal

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

    # Application
    APP_NAME: str = "AP Automation Engine"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apdb",
        description="PostgreSQL connection string for async SQLAlchemy",
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=0)

    # PGBouncer (optional)
    PGBOUNCER_HOST: str | None = None
    PGBOUNCER_PORT: int = 6432

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for HS256 JWT signing",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)

    # Matching Thresholds (0-100 scale)
    THRESHOLD_HIGH: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold (inclusive)",
    )
    THRESHOLD_MID: int = Field(
        default=70,
        ge=0,
        le=100,
        description="1-click review threshold (inclusive)",
    )
    THRESHOLD_LOW: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Exception threshold (inclusive)",
    )

    # Tolerance Settings
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

    # Learning Loop
    LEARNING_CONFIRMATION_COUNT: int = Field(
        default=3,
        ge=1,
        description="Number of confirmations to promote to cross_ref",
    )
    LEARNING_BOOST_FACTOR: float = Field(
        default=10.0,
        ge=0,
        description="Score boost for learned matches",
    )

    # API
    API_V1_PREFIX: str = "/api/v1"
    OPENAPI_URL: str | None = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["*"])

    @field_validator("THRESHOLD_HIGH", "THRESHOLD_MID", "THRESHOLD_LOW")
    @classmethod
    def validate_thresholds(cls, v: int, info) -> int:
        """Ensure thresholds are in valid order."""
        thresholds = info.data
        if (
            "THRESHOLD_HIGH" in info.field_name
            and "THRESHOLD_MID" in thresholds
            and v < thresholds["THRESHOLD_MID"]
        ):
            raise ValueError(
                f"THRESHOLD_HIGH ({v}) must be >= THRESHOLD_MID ({thresholds['THRESHOLD_MID']})"
            )
        if (
            "THRESHOLD_MID" in info.field_name
            and "THRESHOLD_LOW" in thresholds
            and v < thresholds["THRESHOLD_LOW"]
        ):
            raise ValueError(
                f"THRESHOLD_MID ({v}) must be >= THRESHOLD_LOW ({thresholds['THRESHOLD_LOW']})"
            )
        return v

    @property
    def database_pool_url(self) -> str:
        """Return the database URL with PGBouncer if configured."""
        if self.PGBOUNCER_HOST:
            # Replace host in DATABASE_URL with PGBouncer host
            import re

            pattern = r"postgresql\+asyncpg://([^@]+@[^:]+):(\d+)/(\w+)"
            match = re.match(pattern, self.DATABASE_URL)
            if match:
                user_pass, _, dbname = match.groups()
                return f"postgresql+asyncpg://{user_pass}@{self.PGBOUNCER_HOST}:{self.PGBOUNCER_PORT}/{dbname}"
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
