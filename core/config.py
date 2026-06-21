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

    # Application
    app_name: str = Field(default="AP Automation Core", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment name")

    # API
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="CORS allowed origins",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="Async PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=20, description="Connection pool size")
    database_max_overflow: int = Field(default=10, description="Max pool overflow")
    database_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    database_pool_recycle: int = Field(default=3600, description="Pool recycle in seconds")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # PGBouncer (optional fallback)
    pgbouncer_host: str | None = Field(default=None, description="PGBouncer host")
    pgbouncer_port: int = Field(default=5432, description="PGBouncer port")

    # Security
    jwt_secret_key: str = Field(
        default="changeme-in-production",
        description="JWT secret key for HS256 signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Access token expiry in minutes"
    )

    # Matching Thresholds (percentages 0-100)
    threshold_high: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold",
    )
    threshold_mid: int = Field(
        default=70,
        ge=0,
        le=100,
        description="1-click review threshold",
    )
    threshold_low: int = Field(
        default=40,
        ge=0,
        le=100,
        description="Exception threshold",
    )

    # Tolerance Settings (percentages)
    tolerance_price: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Price tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Quantity tolerance percentage",
    )

    # Learning Loop
    learning_auto_promote_threshold: int = Field(
        default=5,
        ge=1,
        description="Number of confirmed matches before auto-promotion",
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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def effective_database_url(self) -> str:
        """Return the effective database URL, using PGBouncer if configured."""
        if self.pgbouncer_host:
            # Parse the original URL to construct PGBouncer URL
            url = self.database_url
            # Replace host/port with PGBouncer settings
            return url.replace(
                "postgresql+asyncpg://",
                f"postgresql+asyncpg://",
            ).rsplit("@", 1)[0] + f"@{self.pgbouncer_host}:{self.pgbouncer_port}/apautomation"
        return self.database_url

    def get_matching_decision_thresholds(self) -> dict[str, int]:
        """Return the matching decision thresholds as a dictionary."""
        return {
            "auto_approve": self.threshold_high,
            "review": self.threshold_mid,
            "exception": self.threshold_low,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
SettingsDep = Annotated[Settings, None]
