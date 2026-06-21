// src/app/config.py
"""Application configuration settings."""
from functools import lru_cache
from typing import Optional

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
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finaro:finaro123@localhost:5432/finaro"
    DATABASE_ECHO: bool = False
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 10
    
    # Authentication
    SECRET_KEY: str = "supersecretkey123456789012345678901234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Matching Engine
    MATCHING_LINE_WEIGHT: float = 0.70
    MATCHING_AMOUNT_WEIGHT: float = 0.20
    MATCHING_DATE_WEIGHT: float = 0.10
    
    # Tolerance thresholds (percentage)
    AMOUNT_TOLERANCE_PERCENT: float = 5.0
    DATE_TOLERANCE_DAYS: int = 7
    
    # Decision thresholds (score)
    AUTO_APPROVE_THRESHOLD: float = 0.95
    HUMAN_REVIEW_THRESHOLD: float = 0.70

    def get_database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL property."""
        return self.get_database_url_sync()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
