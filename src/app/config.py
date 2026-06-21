// src/app/config.py
"""Application configuration from environment variables."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "FinaRo AP Automation Engine"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://finaro:finaro_secret@localhost:5432/finaro"
    )
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

    # JWT Authentication
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["*"]

    # Matching Engine Weights
    matching_line_weight: float = 0.70
    matching_amount_weight: float = 0.20
    matching_date_weight: float = 0.10

    # Decision Thresholds
    auto_approve_threshold: float = 0.95
    human_review_threshold: float = 0.70

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
