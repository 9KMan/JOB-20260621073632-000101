// app/core/config.py
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
    APP_NAME: str = "AP Automation Core Engine"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation"
    PGBOUNCER_HOST: str = "localhost"
    PGBOUNCER_PORT: int = 6432
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Security
    JWT_SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Matching Thresholds
    THRESHOLD_HIGH: float = 0.95  # Auto-approve
    THRESHOLD_MID: float = 0.75  # 1-click review
    THRESHOLD_LOW: float = 0.50  # Exception flagging

    # Tolerance Settings
    TOLERANCE_PRICE: float = 0.02  # 2% price tolerance
    TOLERANCE_QTY: float = 0.10  # 10% quantity tolerance

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Learning System
    LEARNING_ENABLED: bool = True
    MIN_CONFIRMATIONS_FOR_PROMOTION: int = 3
    PROMOTION_CONFIDENCE_BOOST: float = 0.1

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
