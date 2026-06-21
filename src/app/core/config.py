// src/app/core/config.py
"""
Application Configuration
All settings loaded from environment variables.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    APP_NAME: str = "FinaRo AP Automation Engine"
    
    # Security
    SECRET_KEY: str = Field(default="change-me-in-production", env="SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finaro",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Matching Engine Weights
    MATCH_WEIGHT_LINE_LEVEL: float = 0.70
    MATCH_WEIGHT_AMOUNT: float = 0.20
    MATCH_WEIGHT_DATE: float = 0.10
    
    # Matching Thresholds
    MATCH_THRESHOLD_AUTO_APPROVE: float = 0.95
    MATCH_THRESHOLD_PENDING_REVIEW: float = 0.70
    MATCH_THRESHOLD_REJECTED: float = 0.0
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
