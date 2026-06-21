# src/core/config.py
"""Application configuration using pydantic-settings."""

import os
from functools import lru_cache
from typing import List

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
    APP_NAME: str = "FinaRo AP Automation"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finaro:finaro_secret@localhost:5432/finaro"
    DATABASE_URL_SYNC: str = "postgresql://finaro:finaro_secret@localhost:5432/finaro"

    # Security
    SECRET_KEY: str = "supersecretkeychangeinproduction123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Matching Engine Weights (Layer 2)
    MATCH_WEIGHT_LINE_LEVEL: float = 0.70
    MATCH_WEIGHT_AMOUNT: float = 0.20
    MATCH_WEIGHT_DATE: float = 0.10

    # Matching Thresholds
    MATCH_THRESHOLD_AUTO_APPROVE: float = 0.95
    MATCH_THRESHOLD_PENDING_REVIEW: float = 0.70

    @property
    def database_url(self) -> str:
        """Get async database URL."""
        return self.DATABASE_URL

    @property
    def database_url_sync(self) -> str:
        """Get sync database URL."""
        return self.DATABASE_URL_SYNC


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
