# src/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinaRo AP Automation"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://finaro:finaro123@localhost:5432/finaro_db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Security
    SECRET_KEY: str = "changeme12345678901234567890123456789012345678901234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Matching Engine Weights
    MATCHING_WEIGHT_LINE_LEVEL: float = 0.70
    MATCHING_WEIGHT_AMOUNT: float = 0.20
    MATCHING_WEIGHT_DATE: float = 0.10

    # Threshold for auto-approval
    AUTO_APPROVE_THRESHOLD: float = 0.95
    HUMAN_REVIEW_THRESHOLD: float = 0.70

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
