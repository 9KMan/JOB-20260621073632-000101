# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, field_validator
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
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: Annotated[str, Field(validation_alias="DATABASE_URL")] = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/apautomation"
    )

    # JWT Authentication
    jwt_secret_key: Annotated[str, Field(validation_alias="JWT_SECRET_KEY")] = (
        "change-me-in-production"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Matching Thresholds
    threshold_high: Annotated[float, Field(ge=0, le=100)] = 95.0
    threshold_mid: Annotated[float, Field(ge=0, le=100)] = 75.0
    threshold_low: Annotated[float, Field(ge=0, le=100)] = 50.0

    # Tolerance Settings
    tolerance_price: Annotated[float, Field(ge=0, le=100)] = 5.0
    tolerance_qty: Annotated[float, Field(ge=0, le=100)] = 10.0

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate and potentially transform the database URL."""
        if not v:
            raise ValueError("DATABASE_URL must be set")
        if "postgresql" not in v and "postgres" not in v:
            raise ValueError("DATABASE_URL must use PostgreSQL driver")
        return v

    @field_validator("threshold_high")
    @classmethod
    def validate_threshold_high(cls, v: float, info) -> float:
        """Ensure threshold_high is greater than threshold_mid."""
        return v

    def get_decision_threshold(self, score: float) -> str:
        """Route score to decision based on thresholds.

        Args:
            score: Match score between 0 and 100

        Returns:
            Decision: 'APPROVED', 'REVIEW', or 'EXCEPTION'
        """
        if score >= self.threshold_high:
            return "APPROVED"
        elif score >= self.threshold_mid:
            return "REVIEW"
        else:
            return "EXCEPTION"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings singleton
    """
    return Settings()
