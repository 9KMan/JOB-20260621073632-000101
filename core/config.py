// core/config.py
"""Configuration management using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    EnvSettingsSource,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Application name for documentation.
        debug: Enable debug mode (verbose logging, stack traces).
        api_v1_prefix: API version 1 URL prefix.
        cors_origins: List of allowed CORS origins.

        # Database configuration
        database_url: PostgreSQL async connection string.
        database_pool_size: Number of connections in the pool.
        database_max_overflow: Max overflow connections.
        database_pool_timeout: Pool checkout timeout in seconds.
        database_echo: Echo SQL queries (debug only).

        # JWT/Authentication
        jwt_secret_key: HS256 signing secret key.
        jwt_algorithm: JWT signing algorithm.
        jwt_access_token_expire_minutes: Access token expiry.

        # Matching engine thresholds
        threshold_high: Auto-approve threshold (0.0-1.0).
        threshold_mid: 1-click review threshold (0.0-1.0).
        threshold_low: Exception threshold (0.0-1.0).

        # Tolerance settings for matching
        tolerance_price: Price match tolerance percentage.
        tolerance_qty: Quantity match tolerance percentage.

        # Logging
        log_level: Application log level.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(
        default="AP Automation Engine",
        description="Application name for documentation",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode for verbose logging",
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API version 1 URL prefix",
    )
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins",
    )

    # Database configuration
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appass@localhost:5432/apautomation",
        description="PostgreSQL async connection string",
    )
    database_pool_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of connections in the pool",
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Max overflow connections",
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Pool checkout timeout in seconds",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries (debug only)",
    )

    # JWT/Authentication
    jwt_secret_key: str = Field(
        default="changeme-in-production-use-strong-secret",
        description="HS256 signing secret key",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiry in minutes",
    )

    # Matching engine thresholds
    threshold_high: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Auto-approve threshold (0.0-1.0)",
    )
    threshold_mid: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="1-click review threshold (0.0-1.0)",
    )
    threshold_low: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Exception threshold (0.0-1.0)",
    )

    # Tolerance settings
    tolerance_price: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Quantity match tolerance percentage",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Application log level",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper_v

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(
        cls, v: float, info: field_validator
    ) -> float:
        """Validate threshold values are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"{info.field_name} must be between 0.0 and 1.0, got {v}"
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def get_database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql+psycopg2"
        )


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached settings instance.

    """
    return settings
