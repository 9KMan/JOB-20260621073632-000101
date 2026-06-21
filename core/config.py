# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded values are used in production.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PostgresDsn,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="ap-automation-engine", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ap_automation",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=20, ge=1, description="Connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Max pool overflow")
    database_pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # PGBouncer (optional)
    pgbouncer_host: str | None = Field(default=None, description="PGBouncer host")
    pgbouncer_port: int = Field(default=5432, ge=1, le=65535, description="PGBouncer port")

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="JWT signing secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Access token expiry in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, ge=1, description="Refresh token expiry in days"
    )

    # Matching Engine Thresholds (0-100)
    threshold_high: int = Field(default=90, ge=0, le=100, description="Auto-approve threshold")
    threshold_mid: int = Field(default=70, ge=0, le=100, description="1-click review threshold")
    threshold_low: int = Field(default=50, ge=0, le=100, description="Exception threshold")

    # Matching Tolerances (percentage)
    tolerance_price: float = Field(default=5.0, ge=0, description="Price tolerance percentage")
    tolerance_qty: float = Field(default=10.0, ge=0, description="Quantity tolerance percentage")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, description="Number of workers")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: int, info) -> int:
        """Ensure thresholds are in valid range."""
        if not 0 <= v <= 100:
            raise ValueError(f"{info.field_name} must be between 0 and 100")
        return v

    def get_pgbouncer_url(self) -> PostgresDsn | None:
        """Get PGBouncer connection URL if configured."""
        if self.pgbouncer_host:
            return PostgresDsn(
                f"postgresql+asyncpg://{self.database_url.username}:{self.database_url.password}"
                f"@{self.pgbouncer_host}:{self.pgbouncer_port}/{self.database_url.path[1:]}"
            )
        return None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()

# Type aliases for dependency injection
DatabaseUrl = Annotated[PostgresDsn, Field(default=settings.database_url)]
JwtSecret = Annotated[str, Field(default=settings.jwt_secret_key)]
