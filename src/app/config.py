// src/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    DEBUG: bool = True
    APP_NAME: str = "FinaRo AP Automation"
    VERSION: str = "1.0.0"
    
    # Matching Configuration
    MATCHING_LINE_WEIGHT: float = 0.70
    MATCHING_AMOUNT_WEIGHT: float = 0.20
    MATCHING_DATE_WEIGHT: float = 0.10
    
    # Thresholds
    AUTO_APPROVE_THRESHOLD: float = 0.95
    HUMAN_REVIEW_THRESHOLD: float = 0.70
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
