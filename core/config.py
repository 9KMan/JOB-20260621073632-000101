// core/config.py
"""Application configuration management using pydantic-settings.

All configuration is loaded from environment variables with sensible defaults
for development. Production deployments must override these via environment.

Environment variables are validated at startup to catch configuration errors
early rather than at runtime.
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    database_url: str = Field(
        default="postgresql+asyncpg://apuser:appassword@localhost:5432/apautomation",
        description="PostgreSQL connection URL with asyncpg driver",
    )
    pgbouncer_host: Optional[str] = Field(
        default=None,
        description="PGBouncer host for connection pooling",
    )
    pgbouncer_port: int = Field(
        default=5432,
        description="PGBouncer port",
    )
    database_pool_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of connections in the pool",
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum overflow connections allowed",
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Connection pool timeout in seconds",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries (useful for debugging)",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql+asyncpg://", "postgresql://")):
            raise ValueError("Database URL must use postgresql protocol")
        return v


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT token signing (HS256)",
        min_length=32,
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiration time in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiration time in days",
    )


class ThresholdSettings(BaseSettings):
    """Matching threshold configuration."""

    threshold_high: int = Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold (percentage)",
    )
    threshold_mid: int = Field(
        default=75,
        ge=0,
        le=100,
        description="1-click review threshold (percentage)",
    )
    threshold_low: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Exception threshold (percentage)",
    )
    tolerance_price: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Price match tolerance percentage",
    )
    tolerance_qty: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description="Quantity match tolerance percentage",
    )

    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: int, info: Any) -> int:
        """Validate threshold ordering."""
        field_name = info.field_name
        thresholds = {
            "threshold_high": 95,
            "threshold_mid": 75,
            "threshold_low": 50,
        }
        # Check that thresholds are in descending order
        if field_name == "threshold_high" and v < thresholds.get("threshold_mid", 0):
            raise ValueError("HIGH threshold must be >= MID threshold")
        return v


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(
        default="AP Automation Core Engine",
        description="Application name",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version",
    )
    app_description: str = Field(
        default="AP Automation Core Engine for FinaRo - Invoice Matching & Validation",
        description="Application description",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    environment: str = Field(
        default="development",
        description="Deployment environment",
    )

    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port",
    )
    workers: int = Field(
        default=4,
        ge=1,
        description="Number of worker processes",
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development",
    )

    # CORS settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS",
    )
    cors_allow_methods: List[str] = Field(
        default=["*"],
        description="Allowed HTTP methods",
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed HTTP headers",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)",
    )

    # API settings
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 prefix",
    )
    openapi_url: Optional[str] = Field(
        default="/openapi.json",
        description="OpenAPI spec URL",
    )
    docs_url: str = Field(
        default="/docs",
        description="Swagger UI documentation URL",
    )
    redoc_url: str = Field(
        default="/redoc",
        description="ReDoc documentation URL",
    )

    # Nested settings
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database settings",
    )
    jwt: JWTSettings = Field(
        default_factory=JWTSettings,
        description="JWT settings",
    )
    thresholds: ThresholdSettings = Field(
        default_factory=ThresholdSettings,
        description="Matching threshold settings",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev")

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding secrets)."""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "debug": self.debug,
            "api_v1_prefix": self.api_v1_prefix,
            "database": {
                "pool_size": self.database.database_pool_size,
                "max_overflow": self.database.database_max_overflow,
                "echo": self.database.database_echo,
            },
            "thresholds": {
                "high": self.thresholds.threshold_high,
                "mid": self.thresholds.threshold_mid,
                "low": self.thresholds.threshold_low,
                "tolerance_price": self.thresholds.tolerance_price,
                "tolerance_qty": self.thresholds.tolerance_qty,
            },
        }


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings.
    
    Uses lru_cache to ensure settings are only loaded once
    and reused across the application lifecycle.
    
    Returns:
        AppSettings: The application settings instance.
    """
    return AppSettings()


# Convenience function for dependency injection
def get_app_settings() -> AppSettings:
    """Get application settings for FastAPI dependency injection."""
    return get_settings()


# Import for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import Field
