# core/config.py
"""
Application configuration management.

Uses pydantic-settings for environment variable validation and loading.
All configuration is done via environment variables - no hardcoded secrets.
"""

from functools import lru_cache
from typing import List

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

    # ─────────────────────────────────────────────────────────────────────────
    # Database Configuration
    # ─────────────────────────────────────────────────────────────────────────
    database_url: str = Field(
        description="Async PostgreSQL connection string for SQLAlchemy",
        default="postgresql+asyncpg://ap_user:ap_secure_password@localhost:5433/ap_automation",
    )
    database_pool_url: str = Field(
        description="Connection pool URL (PGBouncer endpoint)",
        default="postgresql+asyncpg://ap_user:ap_secure_password@localhost:5433/ap_automation",
    )
    database_sync_url: str = Field(
        description="Synchronous PostgreSQL connection string for Alembic",
        default="postgresql://ap_user:ap_secure_password@localhost:5432/ap_automation",
    )
    database_pool_size: int = Field(default=20, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    database_pool_timeout: int = Field(default=30, ge=1)
    database_pool_recycle: int = Field(default=3600, ge=0)

    # ─────────────────────────────────────────────────────────────────────────
    # JWT / Security Configuration
    # ─────────────────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(
        description="HS256 signing secret key",
        default="change_me_in_production_use_64_random_characters_minimum",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)

    # ─────────────────────────────────────────────────────────────────────────
    # Matching Thresholds
    # ─────────────────────────────────────────────────────────────────────────
    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (score >= this value)",
    )
    threshold_mid: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (score >= this value)",
    )
    threshold_low: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Exception threshold (score >= this value)",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_threshold_order(cls, v: float) -> float:
        """Ensure thresholds are in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {v}")
        return round(v, 4)

    # ─────────────────────────────────────────────────────────────────────────
    # Matching Tolerances
    # ─────────────────────────────────────────────────────────────────────────
    tolerance_price: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance as decimal (2% = 0.02)",
    )
    tolerance_qty: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance as decimal (5% = 0.05)",
    )

    @field_validator("tolerance_price", "tolerance_qty")
    @classmethod
    def validate_tolerance(cls, v: float) -> float:
        """Ensure tolerances are non-negative."""
        if v < 0.0:
            raise ValueError(f"Tolerance must be non-negative, got {v}")
        return round(v, 4)

    # ─────────────────────────────────────────────────────────────────────────
    # Application Settings
    # ─────────────────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper_v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ─────────────────────────────────────────────────────────────────────────
    # Computed Properties
    # ─────────────────────────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def thresholds(self) -> dict:
        """Return all thresholds as a dictionary."""
        return {
            "high": self.threshold_high,
            "mid": self.threshold_mid,
            "low": self.threshold_low,
        }

    @property
    def tolerances(self) -> dict:
        """Return all tolerances as a dictionary."""
        return {
            "price": self.tolerance_price,
            "qty": self.tolerance_qty,
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
