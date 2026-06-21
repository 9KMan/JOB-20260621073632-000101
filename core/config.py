# core/config.py
"""
Application configuration using pydantic-settings.
"""
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
    )

    # Application
    APP_NAME: str = "AP Automation Core"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="Async PostgreSQL connection string",
    )
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="changeme-in-production",
        description="HS256 secret key for JWT signing",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Matching Thresholds
    THRESHOLD_HIGH: int = Field(
        default=95,
        description="Auto-approve threshold (percentage)",
    )
    THRESHOLD_MID: int = Field(
        default=70,
        description="1-click review threshold (percentage)",
    )
    THRESHOLD_LOW: int = Field(
        default=40,
        description="Exception threshold (percentage)",
    )

    # Tolerance Settings
    TOLERANCE_PRICE: float = Field(
        default=5.0,
        description="Price match tolerance percentage",
    )
    TOLERANCE_QTY: float = Field(
        default=10.0,
        description="Quantity match tolerance percentage",
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )

    # API
    API_V1_PREFIX: str = "/api/v1"

    @property
    def database_sync_url(self) -> str:
        """Get synchronous database URL for migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql"
        )

    def is_auto_approve(self, score: float) -> bool:
        """Check if score qualifies for auto-approve."""
        return score >= self.THRESHOLD_HIGH

    def is_review(self, score: float) -> bool:
        """Check if score requires 1-click review."""
        return self.THRESHOLD_MID <= score < self.THRESHOLD_HIGH

    def is_exception(self, score: float) -> bool:
        """Check if score requires exception handling."""
        return self.THRESHOLD_LOW <= score < self.THRESHOLD_MID

    def is_reject(self, score: float) -> bool:
        """Check if score should be auto-rejected."""
        return score < self.THRESHOLD_LOW


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
