# src/core/config.py
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    PROJECT_NAME: str = "FinaRo AP Automation"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Matching Engine Weights (must sum to 1.0)
    MATCHING_LINE_WEIGHT: float = 0.70
    MATCHING_AMOUNT_WEIGHT: float = 0.20
    MATCHING_DATE_WEIGHT: float = 0.10

    # Matching Thresholds
    MATCHING_CONFIRMED_THRESHOLD: float = 0.90
    MATCHING_PENDING_THRESHOLD: float = 0.60

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous database URL for migrations and scripts."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    @property
    def database_url_async(self) -> str:
        """Async database URL."""
        return self.DATABASE_URL

    def get_database_config(self) -> dict:
        """Get database connection pool configuration."""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
