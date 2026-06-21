// core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async PostgreSQL connection URL for SQLAlchemy",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql+psycopg2://apuser:appass@localhost:5432/apautomation",
        description="Sync PostgreSQL connection URL for Alembic migrations",
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        description="Number of connections to maintain in the pool",
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum overflow connections allowed",
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        description="Seconds to wait for a connection from the pool",
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL statements to stdout",
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256",
        description="Algorithm for JWT token signing",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration in minutes",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration settings."""

    THRESHOLD_HIGH: float = Field(
        default=95.0,
        ge=0.0,
        le=100.0,
        description="Auto-approve threshold percentage",
    )
    THRESHOLD_MID: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="One-click review threshold percentage",
    )
    THRESHOLD_LOW: float = Field(
        default=60.0,
        ge=0.0,
        le=100.0,
        description="Exception threshold percentage",
    )


class ToleranceSettings(BaseSettings):
    """Match tolerance configuration settings."""

    TOLERANCE_PRICE: float = Field(
        default=2.0,
        ge=0.0,
        description="Price match tolerance percentage",
    )
    TOLERANCE_QTY: float = Field(
        default=5.0,
        ge=0.0,
        description="Quantity match tolerance percentage",
    )


class AppSettings(BaseSettings):
    """Application-level settings."""

    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version 1 prefix",
    )
    PROJECT_NAME: str = Field(
        default="AP Automation Core Engine",
        description="Project name for OpenAPI docs",
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level",
    )
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS_ORIGINS from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class Settings(
    DatabaseSettings,
    JWTSettings,
    ThresholdSettings,
    ToleranceSettings,
    AppSettings,
):
    """Combined application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
