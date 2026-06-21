# app/config.py
"""Configuration management using Pydantic Settings."""
from functools import lru_cache
from typing import List
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
    APP_NAME: str = "FinaRo AP Automation Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Authentication
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Matching Engine Weights
    MATCHING_LINE_WEIGHT: float = 0.70
    MATCHING_AMOUNT_WEIGHT: float = 0.20
    MATCHING_DATE_WEIGHT: float = 0.10

    # Decision Thresholds
    MATCH_THRESHOLD_AUTO_APPROVE: float = 0.95
    MATCH_THRESHOLD_HUMAN_REVIEW: float = 0.70

    # API
    API_V1_PREFIX: str = "/api/v1"

    @property
    def database_url_async(self) -> str:
        """Return async database URL for SQLAlchemy."""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
