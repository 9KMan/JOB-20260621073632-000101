# core/config.py
# Configuration management via pydantic-settings
# AP Automation Core Engine — FinaRo

"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        APP_NAME: Application name for logging and documentation.
        APP_VERSION: Current application version.
        DATABASE_URL: Async PostgreSQL connection string.
        DEBUG: Enable debug mode (default: False).
        LOG_LEVEL: Logging level (default: INFO).
        JWT_SECRET_KEY: Secret key for JWT token signing (HS256).
        JWT_ALGORITHM: JWT signing algorithm (default: HS256).
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token expiry in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh token expiry in days.
        THRESHOLD_HIGH: Auto-approve threshold (0.0-1.0).
        THRESHOLD_MID: 1-click review threshold (0.0-1.0).
        THRESHOLD_LOW: Exception threshold (0.0-1.0).
        TOLERANCE_PRICE: Price match tolerance as decimal (0.0-1.0).
        TOLERANCE_QTY: Quantity match tolerance as decimal (0.0-1.0).
        CORS_ORIGINS: Comma-separated list of allowed CORS origins.
        DATABASE_POOL_SIZE: Database connection pool size.
        DATABASE_MAX_OVERFLOW: Maximum overflow connections.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(default="AP Automation Engine", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appass123@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    DATABASE_POOL_SIZE: int = Field(default=20, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Pool recycle in seconds")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production-min-32-chars",
        description="Secret key for JWT signing (min 32 characters)",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiry in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")

    # Matching Engine Thresholds
    THRESHOLD_HIGH: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (95%+ confidence)",
    )
    THRESHOLD_MID: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (75-95% confidence)",
    )
    THRESHOLD_LOW: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (50-75% confidence)",
    )

    # Matching Tolerances
    TOLERANCE_PRICE: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as decimal (5%)",
    )
    TOLERANCE_QTY: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as decimal (10%)",
    )

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated CORS origins",
    )

    @field_validator("THRESHOLD_HIGH", "THRESHOLD_MID", "THRESHOLD_LOW")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        """Validate that threshold is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("TOLERANCE_PRICE", "TOLERANCE_QTY")
    @classmethod
    def validate_tolerances(cls, v: float) -> float:
        """Validate that tolerance is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Tolerance must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate minimum secret key length."""
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long for security"
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached settings instance loaded from environment.
    """
    return Settings()
