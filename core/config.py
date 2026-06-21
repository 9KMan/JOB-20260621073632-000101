// core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

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
    app_name: str = "AP Automation Engine"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        validation_alias="DATABASE_URL",
    )
    pgbouncer_host: Optional[str] = Field(default=None, validation_alias="PGBOUNCER_HOST")
    pgbouncer_port: int = Field(default=5432, validation_alias="PGBOUNCER_PORT")
    database_pool_size: int = Field(default=20, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, validation_alias="DATABASE_MAX_OVERFLOW")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="supersecretkey-change-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # Matching Thresholds
    threshold_high: int = Field(
        default=95,
        validation_alias="THRESHOLD_HIGH",
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: int = Field(
        default=70,
        validation_alias="THRESHOLD_MID",
        description="1-click review threshold (percentage)",
    )
    threshold_low: int = Field(
        default=40,
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

    # Learning Loop
    learning_confidence_boost: float = Field(
        default=5.0,
        description="Confidence boost for confirmed matches in learning loop",
    )
    learning_min_confirmations: int = Field(
        default=3,
        description="Minimum confirmations before promoting to high-confidence match",
    )

    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL, considering PGBouncer."""
        if self.pgbouncer_host:
            return self.database_url.replace(
                "localhost",
                f"{self.pgbouncer_host}:{self.pgbouncer_port}",
            )
        return self.database_url

    def get_threshold_for_decision(self, score: float) -> str:
        """Determine decision based on score and thresholds."""
        if score >= self.threshold_high:
            return "auto_approve"
        elif score >= self.threshold_mid:
            return "review"
        elif score >= self.threshold_low:
            return "exception"
        else:
            return "reject"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
