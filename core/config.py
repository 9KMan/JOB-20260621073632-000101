# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

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
    APP_NAME: str = "AP Automation Engine"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation"
    PGBOUNCER_HOST: Optional[str] = None
    PGBOUNCER_PORT: int = 5432
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Security
    JWT_SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # Matching Thresholds
    THRESHOLD_HIGH: int = 95
    THRESHOLD_MID: int = 70
    THRESHOLD_LOW: int = 40

    # Matching Tolerances
    TOLERANCE_PRICE: float = 5.0
    TOLERANCE_QTY: float = 10.0

    # Learning Loop
    CROSS_REF_CONFIDENCE_THRESHOLD: float = 90.0
    CROSS_REF_PROMOTION_COUNT: int = 5

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # API
    API_V1_PREFIX: str = "/api/v1"
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    @property
    def database_url_sync(self) -> str:
        """Return synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def pgbouncer_url(self) -> str:
        """Return database URL pointing to PGBouncer."""
        if self.PGBOUNCER_HOST:
            return self.DATABASE_URL.replace(
                "localhost", self.PGBOUNCER_HOST
            )
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
