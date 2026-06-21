// src/config.py
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
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "FinaRo AP Automation"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finaro_ap"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    
    # JWT Authentication
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Matching Weights
    MATCHING_LINE_WEIGHT: float = 0.70
    MATCHING_AMOUNT_WEIGHT: float = 0.20
    MATCHING_DATE_WEIGHT: float = 0.10
    
    # Decision Thresholds
    AUTO_APPROVE_THRESHOLD: float = 95.0
    HUMAN_REVIEW_THRESHOLD: float = 70.0
    
    # Date tolerances (in days)
    DATE_TOLERANCE_DAYS: int = 7
    
    # Amount tolerance (percentage)
    AMOUNT_TOLERANCE_PERCENT: float = 5.0


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
