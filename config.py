// config.py
"""Application configuration management."""
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
    ENVIRONMENT: str = Field(default="development")

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/finaro_ap"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Matching Engine Weights (must sum to 100)
    MATCH_WEIGHT_LINE_LEVEL: float = 70.0
    MATCH_WEIGHT_AMOUNT: float = 20.0
    MATCH_WEIGHT_DATE: float = 10.0

    # Matching Thresholds
    MATCH_THRESHOLD_CONFIRM: float = 85.0
    MATCH_THRESHOLD_PENDING: float = 60.0

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    ENVIRONMENT: str = "development"


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    ENVIRONMENT: str = "production"


class TestSettings(Settings):
    """Test environment settings."""
    DEBUG: bool = True
    ENVIRONMENT: str = "test"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap_test"


def get_settings() -> Settings:
    """Get settings based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "test": TestSettings,
    }
    
    settings_class = settings_map.get(env, DevelopmentSettings)
    return settings_class()


@lru_cache()
def get_cached_settings() -> Settings:
    """Get cached settings instance."""
    return get_settings()
