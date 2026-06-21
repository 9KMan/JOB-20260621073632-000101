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
    APP_NAME: str = "AP Automation Core Engine"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async database connection string",
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql+psycopg2://apuser:appassword@localhost:5432/apautomation",
        description="Sync database connection string for Alembic",
    )

    # Security
    JWT_SECRET_KEY: str = Field(
        default="dev-secret-change-in-production",
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Matching Thresholds
    THRESHOLD_HIGH: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (0.0-1.0)",
    )
    THRESHOLD_MID: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (0.0-1.0)",
    )
    THRESHOLD_LOW: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Exception threshold (0.0-1.0)",
    )

    # Tolerance Settings
    TOLERANCE_PRICE: float = Field(
        default=0.02,
        ge=0.0,
        description="Price match tolerance percentage (e.g., 0.02 = 2%)",
    )
    TOLERANCE_QTY: float = Field(
        default=0.10,
        ge=0.0,
        description="Quantity match tolerance percentage (e.g., 0.10 = 10%)",
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])

    # Learning Loop
    LEARNING_ENABLED: bool = Field(default=True)
    LEARNING_PROMOTION_THRESHOLD: int = Field(
        default=3,
        description="Number of confirmed matches to promote to cross-reference",
    )

    @property
    def threshold_order(self) -> tuple[float, float, float]:
        """Return thresholds in order (high, mid, low)."""
        return (self.THRESHOLD_HIGH, self.THRESHOLD_MID, self.THRESHOLD_LOW)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
