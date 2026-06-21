"""Application settings loaded from environment variables.

All configuration is sourced from environment variables (or a `.env` file in
development). Hardcoded secrets are never accepted; missing required values
raise at startup so the operator gets immediate feedback.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_name: str = "AP Automation Core Engine"
    log_level: str = "INFO"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Database (async driver) ---
    database_url: str = Field(
        default="postgresql+asyncpg://ap_user:ap_password@localhost:5432/ap_automation",
        description="Async SQLAlchemy DSN. asyncpg driver is required.",
    )
    database_url_sync: str = Field(
        default="postgresql://ap_user:ap_password@localhost:5432/ap_automation",
        description="Sync DSN used by Alembic migrations.",
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # --- PGBouncer (optional sidecar) ---
    pgbouncer_host: str = "localhost"
    pgbouncer_port: int = 6432

    # --- Auth ---
    jwt_secret_key: SecretStr = Field(..., min_length=16)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12

    # --- Matching thresholds ---
    threshold_high: float = Field(95.0, ge=0.0, le=100.0)
    threshold_mid: float = Field(80.0, ge=0.0, le=100.0)
    threshold_low: float = Field(60.0, ge=0.0, le=100.0)

    # --- Tolerances ---
    tolerance_price: float = Field(0.02, ge=0.0, le=1.0)
    tolerance_qty: float = Field(0.01, ge=0.0, le=1.0)

    # --- Learning loop ---
    cross_ref_min_confirmations: int = Field(3, ge=1)
    cross_ref_promotion_threshold: float = Field(0.85, ge=0.0, le=1.0)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        if isinstance(value, str) and value:
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator("threshold_low", "threshold_mid", "threshold_high")
    @classmethod
    def _thresholds_ordered(cls, value: float, info) -> float:
        data = info.data
        low = data.get("threshold_low")
        mid = data.get("threshold_mid")
        high = data.get("threshold_high")
        if low is not None and mid is not None and high is not None:
            if not (low <= mid <= high):
                raise ValueError(
                    f"Thresholds must satisfy low <= mid <= high; "
                    f"got low={low}, mid={mid}, high={high}"
                )
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a memoized Settings instance.

    Using lru_cache prevents re-parsing the environment for every dependency
    injection while still allowing tests to call ``Settings.model_validate`` with
    explicit overrides.
    """
    return Settings()  # type: ignore[call-arg]
