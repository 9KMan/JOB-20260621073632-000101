# core/config.py
"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables.
No hardcoded secrets or configuration values.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All fields have sensible defaults for local development.
    Override via environment variables in production.
    """
    
    # Application
    app_name: str = Field(default="AP Automation Core Engine", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://finaro:changeme@localhost:5432/ap_automation",
        alias="DATABASE_URL"
    )
    pgbouncer_host: Optional[str] = Field(default=None, alias="PGBOUNCER_HOST")
    pgbouncer_port: int = Field(default=5432, alias="PGBOUNCER_PORT")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    
    # Security / JWT
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, alias="JWT_EXPIRATION_MINUTES")
    
    # Matching Thresholds
    threshold_high: float = Field(default=95.0, alias="THRESHOLD_HIGH")
    threshold_mid: float = Field(default=70.0, alias="THRESHOLD_MID")
    threshold_low: float = Field(default=40.0, alias="THRESHOLD_LOW")
    
    # Tolerance Settings
    tolerance_price: float = Field(default=5.0, alias="TOLERANCE_PRICE")
    tolerance_qty: float = Field(default=10.0, alias="TOLERANCE_QTY")
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        alias="CORS_ORIGINS"
    )
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Validate CORS origins format."""
        if not v:
            return ""
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @field_validator("threshold_high", "threshold_mid", "threshold_low")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        """Ensure threshold is within valid range."""
        if not 0 <= v <= 100:
            raise ValueError("Threshold must be between 0 and 100")
        return v
    
    @field_validator("tolerance_price", "tolerance_qty")
    @classmethod
    def validate_tolerance(cls, v: float) -> float:
        """Ensure tolerance is non-negative."""
        if v < 0:
            raise ValueError("Tolerance must be non-negative")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience accessor for dependency injection
settings = get_settings()
