// src/config.py
"""Application configuration from environment variables."""
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinaRo AP Automation"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/finaro"
    )
    DATABASE_POOL_SIZE: int = Field(default=5)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_ECHO: bool = Field(default=False)

    # Authentication
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # Matching Engine Weights
    MATCHING_LINE_WEIGHT: float = Field(default=0.70)
    MATCHING_AMOUNT_WEIGHT: float = Field(default=0.20)
    MATCHING_DATE_WEIGHT: float = Field(default=0.10)

    # Decision Thresholds
    AUTO_APPROVE_THRESHOLD: float = Field(default=0.95)
    HUMAN_REVIEW_THRESHOLD: float = Field(default=0.70)

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["*"])

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
