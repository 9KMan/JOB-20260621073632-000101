// src/config.py
"""Application configuration using Pydantic settings."""
import os
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinaRo AP Automation"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finaro_ap"
    )
    DATABASE_POOL_SIZE: int = Field(default=5)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
