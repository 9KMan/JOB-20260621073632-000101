// core/config.py
"""Application configuration using pydantic-settings."""

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
    app_name: str = Field(default="AP Automation Engine", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ap_automation",
        alias="DATABASE_URL",
    )
    database_host: str = Field(default="localhost", alias="DATABASE_HOST")
    database_port: int = Field(default=5432, alias="DATABASE_PORT")
    database_user: str = Field(default="postgres", alias="DATABASE_USER")
    database_password: str = Field(default="postgres", alias="DATABASE_PASSWORD")
    database_name: str = Field(default="ap_automation", alias="DATABASE_NAME")

    # PGBouncer
    pgbouncer_host: str = Field(default="localhost", alias="PGBOUNCER_HOST")
    pgbouncer_port: int = Field(default=5432, alias="PGBOUNCER_PORT")

    # JWT Security
    jwt_secret_key: str = Field(
        default="supersecretkey-change-in-production",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Matching Thresholds
    threshold_high: int = Field(default=95, alias="THRESHOLD_HIGH")
    threshold_mid: int = Field(default=75, alias="THRESHOLD_MID")
    threshold_low: int = Field(default=50, alias="THRESHOLD_LOW")

    # Tolerance Settings
    tolerance_price: float = Field(default=5.0, alias="TOLERANCE_PRICE")
    tolerance_qty: float = Field(default=10.0, alias="TOLERANCE_QTY")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        alias="CORS_ORIGINS",
    )

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")

    @property
    def database_pool_size(self) -> int:
        """Default pool size for database connections."""
        return 20

    @property
    def database_max_overflow(self) -> int:
        """Max overflow for database connections."""
        return 10

    def get_threshold_decision(self, score: float) -> str:
        """Determine decision based on matching score.
        
        Args:
            score: Matching score (0-100)
            
        Returns:
            Decision: 'auto_approve', 'review', or 'exception'
        """
        if score >= self.threshold_high:
            return "auto_approve"
        elif score >= self.threshold_mid:
            return "review"
        elif score >= self.threshold_low:
            return "exception"
        else:
            return "rejected"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
