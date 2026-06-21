# core/config.py
"""Application configuration using pydantic-settings."""

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
    app_env: str = "development"
    app_name: str = "FinaRo AP Automation"

    # Database
    database_url: str = "postgresql+asyncpg://finaro:secret@localhost:5432/finaro_ap"
    database_echo: bool = False

    # JWT Authentication
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: List[str] = ["*"]

    # Matching Engine Thresholds (0-100)
    threshold_high: float = 90.0
    threshold_mid: float = 70.0
    threshold_low: float = 50.0

    # Matching Tolerances
    tolerance_price: float = 5.0  # Percentage
    tolerance_qty: float = 10.0  # Percentage

    # Learning Loop
    learning_enabled: bool = True
    learning_batch_size: int = 100
    confirmation_required: bool = True

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env.lower() in ("development", "dev")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
