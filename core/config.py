# core/config.py
"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, computed_field
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
    database_url: Annotated[str, Field(
        description="PostgreSQL connection string",
        examples=["postgresql+asyncpg://user:pass@host:5432/dbname"]
    )]
    pgbouncer_host: Annotated[str | None, Field(
        default=None,
        description="PGBouncer host for connection pooling"
    )]
    pgbouncer_port: Annotated[int, Field(
        default=5432,
        description="PGBouncer port"
    )]
    
    # JWT Authentication
    jwt_secret_key: Annotated[str, Field(
        description="HS256 signing secret key"
    )]
    jwt_algorithm: Annotated[str, Field(
        default="HS256",
        description="JWT algorithm"
    )]
    access_token_expire_minutes: Annotated[int, Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiry in minutes"
    )]
    
    # Matching Thresholds
    threshold_high: Annotated[int, Field(
        default=95,
        ge=0,
        le=100,
        description="Auto-approve threshold percentage"
    )]
    threshold_mid: Annotated[int, Field(
        default=70,
        ge=0,
        le=100,
        description="One-click review threshold percentage"
    )]
    threshold_low: Annotated[int, Field(
        default=50,
        ge=0,
        le=100,
        description="Exception threshold percentage"
    )]
    
    # Tolerance Settings
    tolerance_price: Annotated[float, Field(
        default=5.0,
        ge=0,
        le=100,
        description="Price match tolerance percentage"
    )]
    tolerance_qty: Annotated[float, Field(
        default=10.0,
        ge=0,
        le=100,
        description="Quantity match tolerance percentage"
    )]
    
    # Application
    log_level: Annotated[str, Field(
        default="INFO",
        description="Logging level"
    )]
    debug: Annotated[bool, Field(
        default=False,
        description="Debug mode"
    )]

    @computed_field
    @property
    def effective_database_url(self) -> str:
        """Return database URL, optionally via PGBouncer."""
        if self.pgbouncer_host:
            return self.database_url.replace(
                "postgresql+asyncpg://",
                f"postgresql+asyncpg://"
            ).rsplit("@", 1)[0] + f"@{self.pgbouncer_host}:{self.pgbouncer_port}/"
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance for convenience
settings = get_settings()
