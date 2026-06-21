# core/config.py
"""Application configuration via pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: Annotated[
        PostgresDsn,
        Field(
            default="postgresql+asyncpg://apuser:apsecret@localhost:5432/apautomation",
            description="Async PostgreSQL connection string",
        ),
    ]
    database_pool_size: Annotated[int, Field(default=20, ge=1, le=100)]
    database_max_overflow: Annotated[int, Field(default=10, ge=0, le=50)]
    database_pool_timeout: Annotated[int, Field(default=30, ge=5)]
    database_echo: Annotated[bool, Field(default=False)]

    # ── JWT / Auth ────────────────────────────────────────────────────────────
    jwt_secret_key: Annotated[str, Field(min_length=32)]
    jwt_algorithm: Annotated[str, Field(default="HS256")]
    jwt_expire_minutes: Annotated[int, Field(default=30, ge=1)]

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: Annotated[str, Field(default="*")]

    # ── Matching Thresholds ─────────────────────────────────────────────────────
    threshold_high: Annotated[int, Field(default=95, ge=0, le=100, description="Auto-approve score threshold")]
    threshold_mid: Annotated[int, Field(default=75, ge=0, le=100, description="1-click review threshold")]
    threshold_low: Annotated[int, Field(default=50, ge=0, le=100, description="Exception threshold")]

    # ── Match Tolerance ─────────────────────────────────────────────────────────
    tolerance_price: Annotated[float, Field(default=2.0, ge=0, description="Price match tolerance %")]
    tolerance_qty: Annotated[float, Field(default=5.0, ge=0, description="Quantity match tolerance %")]

    # ── Logging ────────────────────────────────────────────────────────────────
    log_level: Annotated[str, Field(default="INFO")]

    # ── Derived helpers ────────────────────────────────────────────────────────
    @property
    def database_url_sync(self) -> str:
        """Synchronous DB URL for Alembic migrations."""
        return self.database_url.replace("postgresql+asyncpg", "postgresql")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _validate_thresholds(self) -> "Settings":
        """Ensure thresholds are ordered: high >= mid >= low."""
        if not (self.threshold_low <= self.threshold_mid <= self.threshold_high):
            raise ValueError("threshold_low must be <= threshold_mid <= threshold_high")
        return self

    @model_validator(mode="after")
    def _validate_jwt_secret(self) -> "Settings":
        """Warn if JWT secret looks like a default/placeholder in non-test envs."""
        weak_secrets = {"change-me", "changeme", "secret", "your-secret", "change-me-in-production"}
        if self.jwt_secret_key.lower() in weak_secrets:
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY appears weak. Set a strong random value in production.",
                UserWarning,
                stacklevel=1,
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a singleton cached Settings instance."""
    return Settings()


# Global singleton
settings = get_settings()
