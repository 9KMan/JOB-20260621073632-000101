# core/config.py
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
    APP_NAME: str = "AP Automation Engine"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="PostgreSQL async connection string",
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=0)

    # PGBouncer (optional)
    PGBOUNCER_HOST: str | None = Field(default=None)
    PGBOUNCER_PORT: int = Field(default=5432)
    PGBOUNCER_DATABASE: str = Field(default="apautomation")

    # Security - JWT
    JWT_SECRET_KEY: str = Field(
        default="changeme-in-production-use-strong-secret",
        description="Secret key for JWT token signing (HS256)",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)

    # Security - Password
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=31)

    # Matching Thresholds
    THRESHOLD_HIGH: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (above this = automatic approval)",
    )
    THRESHOLD_MID: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (between mid and high = review)",
    )
    THRESHOLD_LOW: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Exception threshold (below this = exception flag)",
    )

    # Tolerance Settings
    TOLERANCE_PRICE: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Price match tolerance percentage (2%)",
    )
    TOLERANCE_QTY: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Quantity match tolerance percentage (5%)",
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    # Redis (optional, for caching)
    REDIS_URL: RedisDsn | None = Field(default=None)

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG

    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL, considering PGBouncer."""
        if self.PGBOUNCER_HOST:
            return (
                f"postgresql+asyncpg://{self.DATABASE_URL.username}:"
                f"{self.DATABASE_URL.password}@{self.PGBOUNCER_HOST}:"
                f"{self.PGBOUNCER_PORT}/{self.PGBOUNCER_DATABASE}"
            )
        return str(self.DATABASE_URL)

    def validate_thresholds(self) -> None:
        """Validate threshold ordering."""
        if not 0 <= self.THRESHOLD_LOW <= self.THRESHOLD_MID <= self.THRESHOLD_HIGH <= 1:
            raise ValueError(
                "Thresholds must be ordered: 0 <= THRESHOLD_LOW <= "
                "THRESHOLD_MID <= THRESHOLD_HIGH <= 1"
            )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate_thresholds()
    return settings


# Global settings instance
settings = get_settings()

# Type alias for dependency injection
SettingsDep = Annotated[Settings, Field(default_factory=get_settings)]
