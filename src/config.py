// src/config.py
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
    debug: bool = False
    app_name: str = "FinaRo AP Automation"
    api_v1_prefix: str = "/api/v1"
    
    # Matching Configuration
    matching_config: dict = {
        "line_level_weight": 0.70,
        "amount_weight": 0.20,
        "date_weight": 0.10,
        "auto_approve_threshold": 0.95,
        "pending_review_threshold": 0.70,
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
