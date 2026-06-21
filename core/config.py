// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache
from typing import Any

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
    APP_NAME: str = "AP Automation Engine"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        validation_alias="DATABASE_URL",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql+psycopg2://apuser:appassword@localhost:5432/apautomation",
        validation_alias="DATABASE_SYNC_URL",
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=0)

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production-use-strong-secret",
        validation_alias="JWT_SECRET_KEY",
    )
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, ge=1, le=1440, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"])

    # Matching Engine Thresholds
    THRESHOLD_HIGH: float = Field(
        default=90.0, ge=0, le=100, validation_alias="THRESHOLD_HIGH"
    )
    THRESHOLD_MID: float = Field(
        default=70.0, ge=0, le=100, validation_alias="THRESHOLD_MID"
    )
    THRESHOLD_LOW: float = Field(
        default=50.0, ge=0, le=100, validation_alias="THRESHOLD_LOW"
    )

    # Matching Tolerances
    TOLERANCE_PRICE: float = Field(
        default=5.0, ge=0, le=100, validation_alias="TOLERANCE_PRICE"
    )
    TOLERANCE_QTY: float = Field(
        default=10.0, ge=0, le=100, validation_alias="TOLERANCE_QTY"
    )
    TOLERANCE_DATE: int = Field(default=7, ge=0, le=365, validation_alias="TOLERANCE_DATE")

    # Scoring Weights
    SCORE_WEIGHT_PRICE: float = Field(default=40.0, ge=0, le=100)
    SCORE_WEIGHT_QUANTITY: float = Field(default=30.0, ge=0, le=100)
    SCORE_WEIGHT_DATE: float = Field(default=20.0, ge=0, le=100)
    SCORE_WEIGHT_SUPPLIER: float = Field(default=10.0, ge=0, le=100)

    @field_validator("SCORE_WEIGHT_PRICE", "SCORE_WEIGHT_QUANTITY", "SCORE_WEIGHT_DATE", "SCORE_WEIGHT_SUPPLIER")
    @classmethod
    def validate_weights(cls, v: float, info: Any) -> float:
        """Ensure weights are valid percentages."""
        if v < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return v

    @property
    def score_weights_sum(self) -> float:
        """Return sum of all scoring weights."""
        return (
            self.SCORE_WEIGHT_PRICE
            + self.SCORE_WEIGHT_QUANTITY
            + self.SCORE_WEIGHT_DATE
            + self.SCORE_WEIGHT_SUPPLIER
        )

    # Learning Loop Settings
    LEARNING_MIN_CONFIRMATIONS: int = Field(default=3, ge=1, le=10)
    LEARNING_AUTO_PROMOTE: bool = Field(default=True)

    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, ge=1)

    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=50, ge=1, le=1000)
    MAX_PAGE_SIZE: int = Field(default=200, ge=1, le=1000)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
