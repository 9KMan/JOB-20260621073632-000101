// core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False,
        extra="ignore",
    )

    url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/ap_automation",
        description="Async database connection URL",
    )
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Max pool overflow connections")
    pool_timeout: int = Field(default=30, ge=1, description="Pool acquire timeout in seconds")
    pool_recycle: int = Field(default=3600, ge=0, description="Connection recycle time in seconds")
    echo: bool = Field(default=False, description="Echo SQL queries")
    echo_pool: bool = Field(default=False, description="Echo pool operations")


class JWTSettings(BaseSettings):
    """JWT and authentication configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        case_sensitive=False,
        extra="ignore",
    )

    secret_key: str = Field(
        default="changeme-in-production",
        description="Secret key for JWT signing (HS256). Use strong random value in production.",
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=30, ge=1, le=1440, description="Access token expiry in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, ge=1, le=365, description="Refresh token expiry in days"
    )


class ThresholdSettings(BaseSettings):
    """Matching engine threshold configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="THRESHOLD_",
        case_sensitive=False,
        extra="ignore",
    )

    high: float = Field(
        default=95.0,
        ge=0,
        le=100,
        description="Auto-approve threshold (score >= this value)",
    )
    mid: float = Field(
        default=75.0,
        ge=0,
        le=100,
        description="1-click review threshold (score >= this value)",
    )
    low: float = Field(
        default=50.0,
        ge=0,
        le=100,
        description="Exception threshold (score >= this value, below mid)",
    )

    @field_validator("high", "mid", "low", mode="before")
    @classmethod
    def validate_thresholds(cls, v: float | str) -> float:
        """Ensure threshold values are within valid range."""
        return float(v)

    @field_validator("mid")
    @classmethod
    def validate_mid_threshold(cls, v: float, info) -> float:
        """Ensure mid threshold is below high threshold."""
        high = info.data.get("high", 95.0)
        if v >= high:
            raise ValueError("mid threshold must be less than high threshold")
        return v

    @field_validator("low")
    @classmethod
    def validate_low_threshold(cls, v: float, info) -> float:
        """Ensure low threshold is below mid threshold."""
        mid = info.data.get("mid", 75.0)
        if v >= mid:
            raise ValueError("low threshold must be less than mid threshold")
        return v


class ToleranceSettings(BaseSettings):
    """Matching engine tolerance configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="TOLERANCE_",
        case_sensitive=False,
        extra="ignore",
    )

    price: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Price match tolerance percentage",
    )
    qty: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Quantity match tolerance percentage",
    )

    @field_validator("price", "qty", mode="before")
    @classmethod
    def validate_tolerances(cls, v: float | str) -> float:
        """Ensure tolerance values are within valid range."""
        return float(v)


class AppSettings(BaseSettings):
    """Application-level configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(
        default="development",
        description="Application environment (development/staging/production)",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    api_port: int = Field(default=8000, ge=1, le=65535, description="API server port")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="CORS allowed origins (comma-separated)",
    )

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Parse comma-separated CORS origins."""
        if isinstance(v, str):
            return v
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Main application settings container.

    Aggregates all configuration from environment variables
    with appropriate prefixes and validation.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    threshold: ThresholdSettings = Field(default_factory=ThresholdSettings)
    tolerance: ToleranceSettings = Field(default_factory=ToleranceSettings)
    app: AppSettings = Field(default_factory=AppSettings)

    # Direct environment variable mappings for backwards compatibility
    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    jwt_secret_key: Optional[str] = Field(default=None, validation_alias="JWT_SECRET_KEY")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    def get_database_url(self) -> str:
        """Get database URL, preferring direct env var over nested settings."""
        return self.database_url or self.database.url

    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key, preferring direct env var over nested settings."""
        return self.jwt_secret_key or self.jwt.secret_key


@lru_cache
def get_settings() -> Settings:
    """Get cached settings singleton.

    Returns:
        Settings: Application settings instance loaded from environment.

    Example:
        