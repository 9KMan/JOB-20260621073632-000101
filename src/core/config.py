// src/core/config.py
"""
Application configuration using Pydantic Settings
All configuration is loaded from environment variables
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "FinaRo AP Automation Core Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://finaro:finaro123@localhost:5432/finaro_db",
        env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    # Security
    SECRET_KEY: str = Field(
        default=secrets.token_urlsafe(32),
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Matching Engine Weights
    MATCHING_LINE_WEIGHT: float = Field(default=0.70, env="MATCHING_LINE_WEIGHT")
    MATCHING_AMOUNT_WEIGHT: float = Field(default=0.20, env="MATCHING_AMOUNT_WEIGHT")
    MATCHING_DATE_WEIGHT: float = Field(default=0.10, env="MATCHING_DATE_WEIGHT")
    
    # Matching Thresholds
    MATCHING_CONFIRM_THRESHOLD: float = Field(
        default=0.90,
        env="MATCHING_CONFIRM_THRESHOLD"
    )
    MATCHING_PENDING_THRESHOLD: float = Field(
        default=0.70,
        env="MATCHING_PENDING_THRESHOLD"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
