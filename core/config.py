// core/config.py
"""Application configuration management."""
import os
from functools import lru_cache
from typing import List

from pydantic import Field
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
    app_name: str = Field(default="FinaRo", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/finaro",
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW")
    
    # Redis / Celery
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND")
    
    # JWT
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, alias="JWT_EXPIRATION_MINUTES")
    
    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000", alias="CORS_ORIGINS")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # Matching weights
    matching_weight_line_level: float = 0.70
    matching_weight_amount: float = 0.20
    matching_weight_date: float = 0.10
    
    # Approval thresholds
    auto_approve_threshold: float = 0.95
    human_review_threshold: float = 0.70


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
