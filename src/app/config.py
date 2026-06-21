// src/app/config.py
"""Application configuration management."""
import os
from functools import lru_cache
from typing import Literal

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
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finaro",
        description="Async database connection string",
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/finaro",
        description="Sync database connection string for Alembic",
    )
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # Security
    secret_key: str = Field(
        default="change-me-in-production-use-strong-secret-key",
        description="Secret key for JWT signing",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "json"

    # Matching Engine Configuration
    matching_config: dict = Field(
        default_factory=lambda: {
            "line_level_weight": 0.70,
            "amount_weight": 0.20,
            "date_weight": 0.10,
            "auto_approve_threshold": 0.95,
            "auto_reject_threshold": 0.30,
            "pending_review_range": [0.30, 0.95],
        }
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
