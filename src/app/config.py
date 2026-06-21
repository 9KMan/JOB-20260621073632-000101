// src/app/config.py
"""
FinaRo AP Automation Core Engine
Configuration Settings
"""
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
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    
    # Server
    HOST: str = Field(default="0.0.0.0", validation_alias="HOST")
    PORT: int = Field(default=8000, validation_alias="PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://finaro:finaro_password@localhost:5432/finaro_db",
        validation_alias="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, validation_alias="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, validation_alias="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, validation_alias="DATABASE_POOL_TIMEOUT")
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        validation_alias="CORS_ORIGINS"
    )
    
    # 3-Way Matching Weights
    MATCHING_LINE_WEIGHT: float = Field(default=0.70, validation_alias="MATCHING_LINE_WEIGHT")
    MATCHING_AMOUNT_WEIGHT: float = Field(default=0.20, validation_alias="MATCHING_AMOUNT_WEIGHT")
    MATCHING_DATE_WEIGHT: float = Field(default=0.10, validation_alias="MATCHING_DATE_WEIGHT")
    
    # Matching Thresholds
    MATCH_SCORE_AUTO_APPROVE: float = Field(
        default=0.95, 
        validation_alias="MATCH_SCORE_AUTO_APPROVE"
    )
    MATCH_SCORE_HUMAN_REVIEW: float = Field(
        default=0.70, 
        validation_alias="MATCH_SCORE_HUMAN_REVIEW"
    )
    
    # Tolerance settings for matching
    AMOUNT_TOLERANCE_PERCENT: float = Field(
        default=5.0, 
        validation_alias="AMOUNT_TOLERANCE_PERCENT"
    )
    DATE_TOLERANCE_DAYS: int = Field(
        default=7, 
        validation_alias="DATE_TOLERANCE_DAYS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
