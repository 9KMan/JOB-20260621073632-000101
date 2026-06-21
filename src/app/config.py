// src/app/config.py
"""
Configuration management for FinaRo AP Automation Core Engine.
All configuration is loaded from environment variables.
"""

import os
from functools import lru_cache
from typing import List

from pydantic import Field
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
    APP_NAME: str = "FinaRo AP Automation Core Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    
    # Security
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/finaro")
    DATABASE_SYNC_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/finaro")
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Matching Engine
    MATCHING_LINE_WEIGHT: float = 0.70
    MATCHING_AMOUNT_WEIGHT: float = 0.20
    MATCHING_DATE_WEIGHT: float = 0.10
    
    # Auto-approve threshold (0.0 - 1.0)
    AUTO_APPROVE_THRESHOLD: float = 0.95
    # Human review threshold (0.0 - 1.0)
    HUMAN_REVIEW_THRESHOLD: float = 0.70
    
    # Tolerance percentages for matching
    AMOUNT_TOLERANCE_PERCENT: float = 5.0
    DATE_TOLERANCE_DAYS: int = 7


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
