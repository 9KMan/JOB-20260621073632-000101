# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
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
    APP_NAME: str = "AP Automation Core"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "ap_automation"
    DATABASE_USER: str = "ap_user"
    DATABASE_PASSWORD: str = "password"

    # For async SQLAlchemy connection
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://ap_user:password@localhost:5432/ap_automation"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v: str | None, info) -> str:
        """Build database URL from components if not explicitly set."""
        if v:
            return v
        values = info.data
        return (
            f"postgresql+asyncpg://{values.get('DATABASE_USER', 'ap_user')}:"
            f"{values.get('DATABASE_PASSWORD', 'password')}@"
            f"{values.get('DATABASE_HOST', 'localhost')}:"
            f"{values.get('DATABASE_PORT', 5432)}/"
            f"{values.get('DATABASE_NAME', 'ap_automation')}"
        )

    # PGBouncer (optional override)
    PGBOUNCER_HOST: str | None = None
    PGBOUNCER_PORT: int = 6432

    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Matching Thresholds (percentage 0-100)
    THRESHOLD_HIGH: int = 95  # Auto-approve threshold
    THRESHOLD_MID: int = 70   # 1-click review threshold
    THRESHOLD_LOW: int = 40   # Exception threshold (below this = reject)

    # Tolerance Settings (percentage)
    TOLERANCE_PRICE: float = 5.0  # Price match tolerance %
    TOLERANCE_QTY: float = 10.0   # Quantity match tolerance %

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Alembic
    ALEMBIC_DATABASE_URL: str | None = None

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        if self.ALEMBIC_DATABASE_URL:
            return self.ALEMBIC_DATABASE_URL
        return self.DATABASE_URL.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()

# Type aliases for dependency injection
DatabaseUrl = Annotated[str, Field(description="Database connection URL")]
SecretKey = Annotated[str, Field(description="JWT secret key")]
