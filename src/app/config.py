// src/app/config.py
"""Configuration management using environment variables."""
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

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://finaro:finaro@localhost:5432/finaro"
    )
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)

    # JWT Authentication
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["*"])

    # Matching Configuration
    MATCH_WEIGHT_LINE_LEVEL: float = Field(default=0.70)
    MATCH_WEIGHT_AMOUNT: float = Field(default=0.20)
    MATCH_WEIGHT_DATE: float = Field(default=0.10)

    # Auto-approve threshold (0.0 - 1.0)
    AUTO_APPROVE_THRESHOLD: float = Field(default=0.85)
    # Human review threshold (0.0 - 1.0)
    HUMAN_REVIEW_THRESHOLD: float = Field(default=0.60)

    # API Versioning
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
