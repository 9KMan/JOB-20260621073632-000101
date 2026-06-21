// core/config.py
"""Application configuration management.

This module uses pydantic-settings for environment-based configuration.
All settings are loaded from environment variables or .env file.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    name: str = Field(default="apautomation", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")
    pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")
    pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, ge=0, description="Pool recycle time in seconds")

    @property
    def async_url(self) -> str:
        """Generate async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @property
    def sync_url(self) -> str:
        """Generate sync PostgreSQL connection URL for migrations."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="HS256 signing secret key",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, ge=1, le=1440, description="Access token expiry in minutes"
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold settings."""

    model_config = SettingsConfigDict(env_prefix="THRESHOLD_")

    high: int = Field(
        default=95, ge=0, le=100,
        description="Auto-approve threshold (percentage)"
    )
    mid: int = Field(
        default=75, ge=0, le=100,
        description="One-click review threshold (percentage)"
    )
    low: int = Field(
        default=50, ge=0, le=100,
        description="Exception threshold (percentage)"
    )

    @field_validator("high", "mid", "low")
    @classmethod
    def validate_thresholds(cls, v: int) -> int:
        """Validate threshold is within valid range."""
        if not 0 <= v <= 100:
            raise ValueError("Threshold must be between 0 and 100")
        return v


class ToleranceSettings(BaseSettings):
    """Matching tolerance settings."""

    model_config = SettingsConfigDict(env_prefix="TOLERANCE_")

    price: float = Field(
        default=5.0, ge=0, le=100,
        description="Price match tolerance percentage"
    )
    qty: float = Field(
        default=10.0, ge=0, le=100,
        description="Quantity match tolerance percentage"
    )


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = Field(
        default="AP Automation Core Engine",
        description="Application name"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        validation_alias="LOG_LEVEL"
    )
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    docs_url: str = Field(default="/docs", description="OpenAPI documentation URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc documentation URL")

    # CORS settings
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )
    cors_allow_methods: list[str] = Field(
        default=["*"],
        description="Allowed HTTP methods"
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed HTTP headers"
    )


class Settings(BaseSettings):
    """Combined application settings."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    thresholds: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)
    app: AppSettings = Field(default_factory=AppSettings)

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls(
            database=DatabaseSettings(),
            jwt=JWTSettings(),
            thresholds=ThresholdSettings(),
            tolerance=ToleranceSettings(),
            app=AppSettings(),
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Combined application settings instance.
    """
    return Settings.from_env()


# Global settings instance
settings = get_settings()
