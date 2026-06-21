// src/config.py
"""Application configuration from environment variables."""
from functools import lru_cache
from typing import Any

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
    database_url: str = "postgresql+asyncpg://finaro:secure_password@localhost:5432/finaro_ap"
    database_url_sync: str = "postgresql://finaro:secure_password@localhost:5432/finaro_ap"

    # JWT Authentication
    secret_key: str = "dev-secret-key-change-in-production-32chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def get_database_config(self) -> dict[str, Any]:
        """Get database configuration for SQLAlchemy."""
        return {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "echo": self.debug,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
