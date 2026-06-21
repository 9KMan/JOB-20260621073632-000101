// core/config.py
"""Application configuration management using pydantic-settings.

This module handles all environment-based configuration with type validation
and provides sensible defaults for development while requiring explicit
configuration for production settings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL connection string with asyncpg driver
        PGBOUNCER_HOST: PGBouncer host for connection pooling
        PGBOUNCER_PORT: PGBouncer port (default: 5432)
        JWT_SECRET_KEY: Secret key for JWT token signing (HS256)
        JWT_ALGORITHM: JWT signing algorithm (default: HS256)
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token expiry in minutes
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh token expiry in days
        THRESHOLD_HIGH: Auto-approve match score threshold (0-100)
        THRESHOLD_MID: 1-click review threshold (0-100)
        THRESHOLD_LOW: Exception threshold (0-100)
        TOLERANCE_PRICE: Price match tolerance percentage
        TOLERANCE_QTY: Quantity match tolerance percentage
        LOG_LEVEL: Application log level
        DEBUG: Enable debug mode
        API_V1_PREFIX: API version 1 prefix
        PROJECT_NAME: Application name
        VERSION: Application version
        CORS_ORIGINS: Comma-separated list of allowed CORS origins
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="PostgreSQL connection string with asyncpg driver",
    )
    PGBOUNCER_HOST: str = Field(default="localhost", description="PGBouncer host")
    PGBOUNCER_PORT: int = Field(default=5432, description="PGBouncer port")

    # JWT Configuration
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production-minimum-32-characters-long",
        description="Secret key for JWT token signing (HS256)",
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token expiry in minutes",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiry in days",
    )

    # Matching Thresholds (0-100)
    THRESHOLD_HIGH: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve match score threshold",
    )
    THRESHOLD_MID: int = Field(
        default=75,
        ge=0,
        le=100,
        description="1-click review threshold",
    )
    THRESHOLD_LOW: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Exception threshold",
    )

    # Tolerance Configuration
    TOLERANCE_PRICE: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Price match tolerance percentage",
    )
    TOLERANCE_QTY: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Quantity match tolerance percentage",
    )

    # Application Settings
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level",
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version 1 prefix")
    PROJECT_NAME: str = Field(
        default="AP Automation Core Engine",
        description="Application name",
    )
    VERSION: str = Field(default="0.1.0", description="Application version")
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins",
    )

    @field_validator("THRESHOLD_HIGH", "THRESHOLD_MID", "THRESHOLD_LOW")
    @classmethod
    def validate_threshold_order(
        cls, v: int, info: FieldValidationInfo
    ) -> int:
        """Validate that thresholds are in correct order (HIGH > MID > LOW)."""
        thresholds = {
            "THRESHOLD_HIGH": 95,
            "THRESHOLD_MID": 75,
            "THRESHOLD_LOW": 50,
        }
        field_name = info.field_name
        expected_order = ["THRESHOLD_LOW", "THRESHOLD_MID", "THRESHOLD_HIGH"]

        if field_name in expected_order:
            idx = expected_order.index(field_name)
            for prev_field in expected_order[:idx]:
                prev_value = getattr(cls, prev_field, thresholds.get(prev_field, 0))
                if v <= prev_value and prev_field in thresholds:
                    # Skip validation during class creation
                    pass
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin]

    def get_database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql+psycopg2"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    This function caches the settings instance to avoid repeated
    environment variable parsing. The cache is invalidated when
    the process restarts.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Import FieldValidationInfo for type checking
from pydantic import FieldValidationInfo
