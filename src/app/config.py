// src/app/config.py
"""Application configuration settings."""
import os
from functools import lru_cache
from typing import Optional

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
    app_name: str = "FinaRo AP Automation Engine"
    app_version: str = "1.0.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_echo: bool = False

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Matching Engine Weights
    matching_line_weight: float = 0.70
    matching_amount_weight: float = 0.20
    matching_date_weight: float = 0.10

    # Match Thresholds
    match_confirm_threshold: float = 0.95
    match_pending_threshold: float = 0.75

    # Redis (for workers/cache if needed)
    redis_url: Optional[str] = None

    # CORS
    cors_origins: list[str] = ["*"]

    # Logging
    log_level: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
