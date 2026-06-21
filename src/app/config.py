// src/app/config.py
"""Application configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "FinaRo AP Automation"
    debug: bool = False
    
    # Matching Engine Weights
    match_weight_line_level: float = 0.70
    match_weight_amount: float = 0.20
    match_weight_date: float = 0.10
    
    # Auto-approve threshold (0.0 to 1.0)
    auto_approve_threshold: float = 0.85
    # Human review threshold
    human_review_threshold: float = 0.60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
