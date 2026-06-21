// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, computed_field
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
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Database
    database_url: Annotated[PostgresDsn, Field(validation_alias="DATABASE_URL")] = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ap_automation"
    )
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Matching Thresholds
    threshold_high: int = Field(
        default=95,
        validation_alias="THRESHOLD_HIGH",
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: int = Field(
        default=75,
        validation_alias="THRESHOLD_MID",
        description="1-click review threshold (percentage)",
    )
    threshold_low: int = Field(
        default=50,
        validation_alias="THRESHOLD_LOW",
        description="Exception threshold (percentage)",
    )

    # Matching Tolerances
    tolerance_price: float = Field(
        default=5.0,
        validation_alias="TOLERANCE_PRICE",
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        validation_alias="TOLERANCE_QTY",
        description="Quantity match tolerance percentage",
    )

    # PGBouncer (optional connection pooling)
    pgbouncer_host: str | None = Field(
        default=None, validation_alias="PGBOUNCER_HOST"
    )
    pgbouncer_port: int = Field(default=6432, validation_alias="PGBOUNCER_PORT")

    # CORS
    cors_origins: list[str] = Field(
        default=["*"],
        validation_alias="CORS_ORIGINS",
    )

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Return synchronous database URL for Alembic migrations."""
        return str(self.database_url).replace("+asyncpg", "")

    def get_matching_decision(
        self, score: float
    ) -> str:
        """Determine decision based on score and thresholds.
        
        Args:
            score: Match score between 0 and 100.
            
        Returns:
            Decision string: 'auto_approved', 'review', or 'exception'.
        """
        if score >= self.threshold_high:
            return "auto_approved"
        elif score >= self.threshold_mid:
            return "review"
        else:
            return "exception"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
