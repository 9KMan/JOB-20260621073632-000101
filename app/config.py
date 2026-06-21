// app/config.py
"""Application configuration."""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "FinaRo"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finaro"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Matching Weights
    matching_line_weight: float = 0.70
    matching_amount_weight: float = 0.20
    matching_date_weight: float = 0.10

    # Auto-approval threshold
    auto_approve_threshold: float = 0.95
    pending_threshold: float = 0.70


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
