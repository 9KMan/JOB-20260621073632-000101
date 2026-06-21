// src/app/core/config.py
"""
Configuration management using environment variables.
"""
import os
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinaRo AP Automation"
    DEBUG: bool = Field(default=False)
    VERSION: str = "1.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finaro"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # JWT Authentication
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Matching Engine Weights (configurable)
    MATCH_WEIGHT_LINE_LEVEL: float = 0.70
    MATCH_WEIGHT_AMOUNT: float = 0.20
    MATCH_WEIGHT_DATE: float = 0.10

    # Matching Thresholds
    MATCH_CONFIRM_THRESHOLD: float = 0.95
    MATCH_PENDING_THRESHOLD: float = 0.75

    # External Integrations (placeholders)
    ERP_API_URL: str = ""
    ERP_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
