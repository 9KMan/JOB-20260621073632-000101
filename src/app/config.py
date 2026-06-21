# src/app/config.py
"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import Any

from pydantic import Field
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
    DEBUG: bool = Field(default=False)
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://finaro:finaro_secret@localhost:5432/finaro_db",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_ECHO: bool = Field(default=False)
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Authentication
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT signing"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)
    
    # Matching Engine Weights
    MATCH_WEIGHT_LINE_LEVEL: float = Field(default=0.70)
    MATCH_WEIGHT_AMOUNT: float = Field(default=0.20)
    MATCH_WEIGHT_DATE: float = Field(default=0.10)
    
    # Decision Thresholds
    MATCH_THRESHOLD_AUTO_APPROVE: float = Field(default=0.95)
    MATCH_THRESHOLD_HUMAN_REVIEW: float = Field(default=0.70)
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    def get_database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL."""
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
