// src/app/config.py
"""Application configuration management."""
import os
from functools import lru_cache
from typing import Optional

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
    app_name: str = "FinaRo AP Automation"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # API
    api_v1_prefix: str = "/api/v1"
    api_key_header: str = "X-API-Key"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finaro",
        validation_alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=20, validation_alias="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=10, validation_alias="DB_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, validation_alias="DB_POOL_TIMEOUT")

    # Authentication
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(
        default=30, validation_alias="JWT_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, validation_alias="JWT_REFRESH_DAYS"
    )

    # Password
    bcrypt_rounds: int = Field(default=12, validation_alias="BCRYPT_ROUNDS")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        validation_alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Matching Engine Weights
    matching_line_weight: float = 0.70
    matching_amount_weight: float = 0.20
    matching_date_weight: float = 0.10

    # Auto-approval threshold
    auto_approve_threshold: float = 0.95
    pending_review_threshold: float = 0.70

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
