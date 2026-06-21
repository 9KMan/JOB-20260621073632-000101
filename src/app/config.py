// src/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application
    APP_NAME: str = "FinaRo AP Automation Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Matching Engine Weights (must sum to 1.0)
    MATCH_WEIGHT_LINE_LEVEL: float = 0.70
    MATCH_WEIGHT_AMOUNT: float = 0.20
    MATCH_WEIGHT_DATE: float = 0.10
    
    # Matching Thresholds
    AUTO_APPROVE_THRESHOLD: float = 0.95
    HUMAN_REVIEW_THRESHOLD: float = 0.70
    
    # Balance Resolution
    BALANCE_TOLERANCE_AMOUNT: float = 0.01
    BALANCE_TOLERANCE_PERCENT: float = 0.001
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
