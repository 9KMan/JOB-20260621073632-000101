// src/app/config.py
"""Application configuration using environment variables."""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinaRo AP Automation"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/finaro"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Matching Weights (Layer 2)
    MATCHING_WEIGHT_LINE_LEVEL: float = 0.70
    MATCHING_WEIGHT_AMOUNT: float = 0.20
    MATCHING_WEIGHT_DATE: float = 0.10

    # Matching Thresholds
    MATCHING_AUTO_APPROVE_THRESHOLD: float = 0.95
    MATCHING_HUMAN_REVIEW_THRESHOLD: float = 0.70
    MATCHING_TOLERANCE_AMOUNT: float = 0.01
    MATCHING_TOLERANCE_PERCENT: float = 0.05

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
