// src/app/config.py
"""Application configuration using environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinaRo AP Automation Engine"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finaro:finaro@localhost:5432/finaro"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password hashing
    BCRYPT_ROUNDS: int = 12

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Matching Engine Weights
    MATCH_WEIGHT_LINE_LEVEL: float = 0.70
    MATCH_WEIGHT_AMOUNT: float = 0.20
    MATCH_WEIGHT_DATE: float = 0.10

    # Decision Thresholds
    MATCH_THRESHOLD_AUTO_APPROVE: float = 0.95
    MATCH_THRESHOLD_PENDING_REVIEW: float = 0.70

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
