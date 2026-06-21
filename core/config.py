# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Optional

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
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql+psycopg2://apuser:appass@localhost:5432/apautomation",
        description="Sync PostgreSQL connection string for Alembic",
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_ECHO: bool = Field(default=False)

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="changeme-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # Matching Thresholds
    THRESHOLD_HIGH: float = Field(
        default=95.0,
        ge=0.0,
        le=100.0,
        description="Auto-approve threshold percentage",
    )
    THRESHOLD_MID: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="1-click review threshold percentage",
    )
    THRESHOLD_LOW: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Exception threshold percentage",
    )

    # Matching Tolerances
    TOLERANCE_PRICE: float = Field(
        default=5.0,
        ge=0.0,
        description="Price match tolerance percentage",
    )
    TOLERANCE_QTY: float = Field(
        default=10.0,
        ge=0.0,
        description="Quantity match tolerance percentage",
    )

    # PGBouncer (optional)
    PGBOUNCER_HOST: Optional[str] = Field(default=None)
    PGBOUNCER_PORT: int = Field(default=5432)

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            return "INFO"
        return upper_v

    @property
    def database_pool_config(self) -> dict:
        """Get database pool configuration."""
        return {
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.DATABASE_POOL_TIMEOUT,
            "pool_pre_ping": True,
            "echo": self.DATABASE_ECHO,
        }

    @property
    def cors_config(self) -> dict:
        """Get CORS configuration."""
        return {
            "allow_origins": self.CORS_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
