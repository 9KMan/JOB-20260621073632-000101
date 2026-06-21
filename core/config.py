// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables with type validation
and sensible defaults for local development.
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
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        validation_alias="DATABASE_URL",
    )
    PGBOUNCER_HOST: str = Field(default="localhost", validation_alias="PGBOUNCER_HOST")
    DB_ECHO: bool = Field(default=False, validation_alias="DB_ECHO")
    DB_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=1)

    # Authentication
    JWT_SECRET_KEY: str = Field(
        default="changeme-in-production-use-strong-secret-key-32-chars",
        validation_alias="JWT_SECRET_KEY",
    )
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)

    # Matching Engine Thresholds
    THRESHOLD_HIGH: float = Field(
        default=95.0,
        ge=0,
        le=100,
        validation_alias="THRESHOLD_HIGH",
        description="Auto-approve threshold (percentage)",
    )
    THRESHOLD_MID: float = Field(
        default=75.0,
        ge=0,
        le=100,
        validation_alias="THRESHOLD_MID",
        description="1-click review threshold (percentage)",
    )
    THRESHOLD_LOW: float = Field(
        default=50.0,
        ge=0,
        le=100,
        validation_alias="THRESHOLD_LOW",
        description="Exception threshold (percentage)",
    )

    # Matching Tolerances
    TOLERANCE_PRICE: float = Field(
        default=5.0,
        ge=0,
        le=100,
        validation_alias="TOLERANCE_PRICE",
        description="Price match tolerance percentage",
    )
    TOLERANCE_QTY: float = Field(
        default=10.0,
        ge=0,
        le=100,
        validation_alias="TOLERANCE_QTY",
        description="Quantity match tolerance percentage",
    )

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must start with 'postgresql'")
        return v

    @property
    def database_host(self) -> str:
        """Extract database host from DATABASE_URL."""
        from urllib.parse import urlparse

        parsed = urlparse(self.DATABASE_URL)
        return parsed.hostname or "localhost"

    @property
    def database_port(self) -> int:
        """Extract database port from DATABASE_URL."""
        from urllib.parse import urlparse

        parsed = urlparse(self.DATABASE_URL)
        return parsed.port or 5432

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.DEBUG is False

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEBUG is True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern).

    Returns:
        Settings: Cached application settings instance.
    """
    return Settings()


# Global settings instance
settings = get_settings()
