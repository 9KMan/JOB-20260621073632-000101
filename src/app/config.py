// src/app/config.py
"""Application configuration from environment variables."""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinaRo AP Automation Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/finaro_ap"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_ECHO: bool = False

    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Matching Configuration
    MATCHING_WEIGHTS: dict = {
        "line_level": 0.70,
        "amount": 0.20,
        "date": 0.10
    }
    MATCHING_THRESHOLD_AUTO_APPROVE: float = float(os.getenv("MATCHING_THRESHOLD_AUTO_APPROVE", "0.95"))
    MATCHING_THRESHOLD_PENDING: float = float(os.getenv("MATCHING_THRESHOLD_PENDING", "0.70"))

    # Balance Configuration
    BALANCE_TOLERANCE_AMOUNT: float = float(os.getenv("BALANCE_TOLERANCE_AMOUNT", "0.01"))
    BALANCE_TOLERANCE_PERCENT: float = float(os.getenv("BALANCE_TOLERANCE_PERCENT", "2.0"))

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
