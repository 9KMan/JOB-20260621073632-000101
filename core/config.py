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

    # Database
    database_url: Annotated[
        str,
        Field(
            description="PostgreSQL connection string with asyncpg driver",
            examples=["postgresql+asyncpg://user:pass@localhost:5432/dbname"],
        ),
    ]

    # JWT Authentication
    jwt_secret_key: Annotated[
        str,
        Field(
            description="HS256 secret key for JWT signing",
            min_length=32,
        ),
    ]
    jwt_algorithm: Annotated[
        str,
        Field(default="HS256", description="JWT algorithm"),
    ]
    jwt_access_token_expire_minutes: Annotated[
        int,
        Field(default=30, ge=5, le=1440, description="Access token expiry in minutes"),
    ]

    # Matching Thresholds
    threshold_high: Annotated[
        float,
        Field(default=95.0, ge=0, le=100, description="Auto-approve threshold"),
    ]
    threshold_mid: Annotated[
        float,
        Field(default=70.0, ge=0, le=100, description="1-click review threshold"),
    ]
    threshold_low: Annotated[
        float,
        Field(default=40.0, ge=0, le=100, description="Exception threshold"),
    ]

    # Tolerance Settings
    tolerance_price: Annotated[
        float,
        Field(default=0.05, ge=0, le=1, description="Price match tolerance (5%)"),
    ]
    tolerance_qty: Annotated[
        float,
        Field(default=0.10, ge=0, le=1, description="Quantity match tolerance (10%)"),
    ]

    # Application
    app_name: Annotated[str, Field(default="AP Automation Core Engine")]
    app_version: Annotated[str, Field(default="0.1.0")]
    debug: Annotated[bool, Field(default=False)]
    log_level: Annotated[str, Field(default="INFO")]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return upper_v

    @property
    def pool_size(self) -> int:
        """Get database pool size from connection string or use default."""
        return 20

    @property
    def max_overflow(self) -> int:
        """Get max overflow from connection string or use default."""
        return 10


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
