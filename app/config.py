// app/config.py
"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "FinaRo AP Automation"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finaro"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # File uploads
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    
    # Matching thresholds
    match_confidence_threshold: float = 0.85
    match_auto_approve_threshold: float = 0.95
    match_pending_review_threshold: float = 0.70
    
    # Weighting for scoring
    line_level_weight: float = 0.70
    amount_weight: float = 0.20
    date_weight: float = 0.10
    
    # Date tolerance (in days)
    date_tolerance_days: int = 3
    
    # Amount tolerance (as percentage)
    amount_tolerance_percent: float = 2.0


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
