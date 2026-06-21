// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, RedisDsn
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
    app_name: str = "AP Automation Engine"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        validation_alias="DATABASE_URL",
    )
    database_host: str = Field(default="localhost", validation_alias="DATABASE_HOST")
    database_port: int = Field(default=5432, validation_alias="DATABASE_PORT")
    database_name: str = Field(default="apautomation", validation_alias="DATABASE_NAME")
    database_user: str = Field(default="apuser", validation_alias="DATABASE_USER")
    database_password: str = Field(default="appassword", validation_alias="DATABASE_PASSWORD")

    # Sync database URL for Alembic migrations
    database_sync_url: PostgresDsn = Field(
        default="postgresql://apuser:appassword@localhost:5432/apautomation",
        validation_alias="DATABASE_SYNC_URL",
    )

    # PGBouncer
    pgbouncer_host: str = Field(default="localhost", validation_alias="PGBOUNCER_HOST")
    pgbouncer_port: int = Field(default=5432, validation_alias="PGBOUNCER_PORT")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # Matching Thresholds (scores 0-100)
    threshold_high: int = Field(
        default=90,
        validation_alias="THRESHOLD_HIGH",
        ge=0,
        le=100,
        description="Auto-approve threshold",
    )
    threshold_mid: int = Field(
        default=70,
        validation_alias="THRESHOLD_MID",
        ge=0,
        le=100,
        description="1-click review threshold",
    )
    threshold_low: int = Field(
        default=50,
        validation_alias="THRESHOLD_LOW",
        ge=0,
        le=100,
        description="Exception threshold",
    )

    # Tolerance Settings (percentages)
    tolerance_price: float = Field(
        default=5.0,
        validation_alias="TOLERANCE_PRICE",
        ge=0,
        le=100,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        validation_alias="TOLERANCE_QTY",
        ge=0,
        le=100,
        description="Quantity match tolerance percentage",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        validation_alias="CORS_ORIGINS",
    )

    # API
    api_v1_prefix: str = "/api/v1"
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    @property
    def database_async_url(self) -> str:
        """Get async database URL."""
        return str(self.database_url)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if not self.cors_origins:
            return []
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [origin.strip() for origin in self.cors_origins[0].split(",") if origin.strip()]

    def get_threshold_level(self, score: float) -> str:
        """Determine threshold level based on score.

        Args:
            score: Match score (0-100)

        Returns:
            Threshold level: 'high', 'mid', or 'low'
        """
        if score >= self.threshold_high:
            return "high"
        elif score >= self.threshold_mid:
            return "mid"
        elif score >= self.threshold_low:
            return "low"
        return "exception"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()

# Type aliases
AppSettings = Annotated[Settings, "Application settings"]
