// app/config.py
"""Application configuration management."""
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
        extra="ignore",
    )

    # Application
    app_name: str = "FinaRo"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finaro"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/finaro"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # JWT Authentication
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Matching Configuration
    matching_line_weight: float = 0.7
    matching_amount_weight: float = 0.2
    matching_date_weight: float = 0.1
    auto_approve_threshold: float = 0.95
    human_review_threshold: float = 0.70
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
