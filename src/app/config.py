# src/app/config.py
import os
from functools import lru_cache
from typing import List

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
    app_name: str = "FinaRo"
    app_version: str = "1.0.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "postgresql://finaro:finaro@localhost:5432/finaro"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Matching Weights
    matching_line_weight: float = 0.70
    matching_amount_weight: float = 0.20
    matching_date_weight: float = 0.10
    
    # Auto-approval threshold (0.0 to 1.0)
    auto_approve_threshold: float = 0.85
    
    # Business Rules
    date_tolerance_days: int = 5
    amount_tolerance_percent: float = 5.0


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
