// src/app/config.py
"""Application configuration management."""
import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "FinaRo AP Automation"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finaro_ap"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    pgbouncer_host: str = "localhost"
    pgbouncer_port: int = 5432
    pgbouncer_pool_size: int = 20
    
    # JWT Authentication
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Matching Engine Configuration
    match_weight_line_level: float = 0.70
    match_weight_amount: float = 0.20
    match_weight_date: float = 0.10
    auto_approve_threshold: float = 0.95
    human_review_threshold: float = 0.70
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    @property
    def database_url_async(self) -> str:
        """Return async database URL."""
        return self.database_url
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as list."""
        return [origin.strip() for origin in self.cors_origins]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
