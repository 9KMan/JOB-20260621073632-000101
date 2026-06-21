# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or connection strings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
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
    APP_NAME: str = "AP Automation Core"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    DATABASE_HOST: str = Field(default="localhost")
    DATABASE_PORT: int = Field(default=5432)
    DATABASE_NAME: str = Field(default="apautomation")
    DATABASE_USER: str = Field(default="apuser")
    DATABASE_PASSWORD: str = Field(default="appass")
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_POOL_RECYCLE: int = Field(default=3600)
    DATABASE_ECHO: bool = Field(default=False)

    # PGBouncer (if used)
    PGBOUNCER_HOST: str = Field(default="localhost")
    PGBOUNCER_PORT: int = Field(default=5433)

    # Security / JWT
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)

    # Matching Thresholds
    THRESHOLD_HIGH: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= this value)",
    )
    THRESHOLD_MID: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold",
    )
    THRESHOLD_LOW: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score < this value)",
    )

    # Tolerance Settings
    TOLERANCE_PRICE: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance percentage",
    )
    TOLERANCE_QTY: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance percentage",
    )
    TOLERANCE_DATE_DAYS: int = Field(
        default=5,
        ge=0,
        description="Date match tolerance in days",
    )

    # Learning Loop Settings
    LEARNING_AUTO_PROMOTE: bool = Field(
        default=True,
        description="Auto-promote confirmed matches to cross_ref",
    )
    LEARNING_PROMOTE_THRESHOLD: int = Field(
        default=3,
        ge=1,
        description="Number of confirmed matches before auto-promoting",
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    )
    CORS_ALLOW_HEADERS: list[str] = Field(
        default=["*"]
    )

    # API
    API_V1_PREFIX: str = "/api/v1"
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # Redis (optional, for caching/sessions)
    REDIS_URL: RedisDsn | None = Field(default=None)

    def get_sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return str(self.DATABASE_URL).replace(
            "postgresql+asyncpg://", "postgresql://"
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG and self.ENVIRONMENT == "production"

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
