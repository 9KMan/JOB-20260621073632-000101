// src/config.py
"""Application configuration management."""
from typing import List
from functools import lru_cache
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
    app_name: str = "FinaRo AP Automation"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "default-secret-key-change-in-production"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finaro"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # JWT Authentication
    jwt_secret_key: str = "jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # API Prefixes
    api_v1_prefix: str = "/api/v1"

    # Matching Configuration
    matching_line_weight: float = 0.70
    matching_amount_weight: float = 0.20
    matching_date_weight: float = 0.10
    
    # Auto-approval threshold (0.0 to 1.0)
    auto_approve_threshold: float = 0.95
    # Human review threshold
    human_review_threshold: float = 0.70


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
