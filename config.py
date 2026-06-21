# config.py
import os
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

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "FinaRo AP Automation Engine"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    
    # Matching Engine Weights
    matching_line_weight: float = 0.70
    matching_amount_weight: float = 0.20
    matching_date_weight: float = 0.10
    
    # Auto-approval threshold (0.0 - 1.0)
    auto_approve_threshold: float = 0.95
    human_review_threshold: float = 0.70


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
