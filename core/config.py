# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
See .env.example for available variables.
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

    # Application settings
    app_name: str = Field(default="AP Automation Engine", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Runtime environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    api_port: int = Field(default=8000, description="API server port")

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="PostgreSQL connection string",
    )
    database_pool_size: int = Field(default=20, description="Database pool size")
    database_max_overflow: int = Field(default=10, description="Database max overflow")
    database_pool_timeout: int = Field(default=30, description="Database pool timeout (seconds)")
    database_pool_recycle: int = Field(default=3600, description="Database pool recycle (seconds)")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # JWT Authentication settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT signing secret key",
    )
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = Field(
        default="HS256", description="JWT algorithm"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Access token expiry (minutes)"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiry (days)"
    )

    # Password hashing
    bcrypt_rounds: int = Field(default=12, description="bcrypt rounds for password hashing")

    # Matching thresholds
    threshold_high: float = Field(
        default=90.0,
        ge=0.0,
        le=100.0,
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="1-click review threshold (percentage)",
    )
    threshold_low: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Exception threshold (percentage)",
    )

    # Tolerance settings for matching
    tolerance_price: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Price match tolerance (percentage)",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Quantity match tolerance (percentage)",
    )

    # Learning loop settings
    learning_confidence_threshold: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Confidence threshold for learning promotion",
    )
    learning_promotion_count: int = Field(
        default=3,
        ge=1,
        description="Number of successful matches to promote a rule",
    )

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")
    cors_allow_methods: list[str] = Field(
        default=["*"], description="Allowed CORS methods"
    )
    cors_allow_headers: list[str] = Field(
        default=["*"], description="Allowed CORS headers"
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Validate JWT secret key is not the default placeholder."""
        if v == "your-secret-key-change-in-production" and cls._is_production():
            raise ValueError("JWT secret key must be changed in production")
        return v

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        """Validate threshold ordering."""
        return v

    @staticmethod
    def _is_production() -> bool:
        """Check if running in production."""
        import os

        return os.getenv("ENVIRONMENT", "").lower() == "production"

    def get_thresholds(self) -> dict[str, float]:
        """Get all matching thresholds as a dictionary."""
        return {
            "high": self.threshold_high,
            "mid": self.threshold_mid,
            "low": self.threshold_low,
        }

    def get_tolerances(self) -> dict[str, float]:
        """Get all tolerance settings as a dictionary."""
        return {
            "price": self.tolerance_price,
            "qty": self.tolerance_qty,
        }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
