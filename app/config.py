// app/config.py
"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

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
    APP_NAME: str = Field(default="FinaRo AP Automation", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://finaro_user:finaro_secure_password@localhost:5432/finaro_db",
        description="PostgreSQL database URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, le=100, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50, description="Max connection overflow")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=1, description="Connection pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=0, description="Connection recycle time in seconds")
    
    # Authentication
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", description="JWT secret key")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, description="Token expiration in minutes")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Matching Engine Weights
    MATCH_WEIGHT_LINE_LEVEL: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Weight for line-level matching"
    )
    MATCH_WEIGHT_AMOUNT: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Weight for amount matching"
    )
    MATCH_WEIGHT_DATE: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Weight for date matching"
    )
    
    # Auto-Approval
    AUTO_APPROVE_THRESHOLD: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Minimum score for auto-approval"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        level = v.upper()
        if level not in valid_levels:
            return "INFO"
        return level
    
    @property
    def matching_weights(self) -> dict:
        """Get matching weights as a dictionary."""
        return {
            "line_level": self.MATCH_WEIGHT_LINE_LEVEL,
            "amount": self.MATCH_WEIGHT_AMOUNT,
            "date": self.MATCH_WEIGHT_DATE,
        }
    
    @property
    def total_weight(self) -> float:
        """Get total of all matching weights."""
        return sum(self.matching_weights.values())


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
