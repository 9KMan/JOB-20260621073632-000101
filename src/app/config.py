// src/app/config.py
"""Application configuration from environment variables."""

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

    # Database
    database_url: str = "postgresql+asyncpg://finaro:password@localhost:5432/finaro_ap"
    database_url_sync: str = "postgresql://finaro:password@localhost:5432/finaro_ap"

    # JWT Authentication
    secret_key: str = "change-me-in-production-use-strong-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application
    app_name: str = "FinaRo AP Automation"
    app_version: str = "0.1.0"
    debug: bool = False
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Matching Weights (Layer 2 - Cascade Matching)
    match_weight_line_level: float = 0.70
    match_weight_amount: float = 0.20
    match_weight_date: float = 0.10

    # Decision Thresholds
    threshold_auto_approve: float = 0.95
    threshold_human_review: float = 0.70

    @property
    def matching_weights(self) -> dict:
        """Get normalized matching weights."""
        total = (
            self.match_weight_line_level
            + self.match_weight_amount
            + self.match_weight_date
        )
        return {
            "line_level": self.match_weight_line_level / total,
            "amount": self.match_weight_amount / total,
            "date": self.match_weight_date / total,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
