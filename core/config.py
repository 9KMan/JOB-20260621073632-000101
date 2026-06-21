// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Literal

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
    app_name: str = "AP Automation Core Engine"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_port: int = 8000

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="PostgreSQL connection string with asyncpg driver",
    )
    postgres_user: str = "apuser"
    postgres_password: str = "appassword"
    postgres_db: str = "apautomation"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # PGBouncer
    pgbouncer_host: str = "localhost"
    pgbouncer_port: int = 6432

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT signing (HS256)",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Matching Thresholds (0.0 - 1.0)
    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold",
    )
    threshold_mid: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold",
    )
    threshold_low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold",
    )

    # Tolerance Settings
    tolerance_price: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance percentage",
    )

    # CORS
    cors_origins: str = "*"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Parse CORS origins from string."""
        if v == "*":
            return "*"
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.database_url.replace("+asyncpg", "")

    def get_decision_threshold(
        self, decision: Literal["approve", "review", "exception"]
    ) -> float:
        """Get threshold value for a decision type."""
        thresholds = {
            "approve": self.threshold_high,
            "review": self.threshold_mid,
            "exception": self.threshold_low,
        }
        return thresholds[decision]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
