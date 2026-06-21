# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "AP Automation Core Engine"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apautomation:apautomation_dev@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "apautomation"
    DATABASE_USER: str = "apautomation"
    DATABASE_PASSWORD: str = "apautomation_dev"

    # Database pool settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # JWT settings
    JWT_SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-minimum-32-chars",
        description="Secret key for JWT signing",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Matching thresholds (percentages)
    THRESHOLD_HIGH: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold percentage",
    )
    THRESHOLD_MID: int = Field(
        default=70,
        ge=0,
        le=100,
        description="1-click review threshold percentage",
    )
    THRESHOLD_LOW: int = Field(
        default=40,
        ge=0,
        le=100,
        description="Exception threshold percentage",
    )

    # Matching tolerances
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

    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # API settings
    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = "AP Automation API"
    API_DESCRIPTION: str = "Accounts Payable Automation Core Engine API"
    API_DEBUG: bool = False

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )

    @property
    def database_dsn(self) -> str:
        """Get database DSN for logging/debugging."""
        return f"postgresql://{self.DATABASE_USER}:***@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
