// src/config.py
"""Application configuration from environment variables."""
import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finaro_ap"
    ))
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"


class JWTConfig(BaseModel):
    """JWT configuration."""
    secret_key: str = Field(default_factory=lambda: os.getenv(
        "JWT_SECRET_KEY",
        "your-super-secret-key-change-in-production"
    ))
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"
    ))


class AppConfig(BaseModel):
    """Application configuration."""
    name: str = "FinaRo AP Automation"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    api_v1_prefix: str = "/api/v1"
    
    # Matching weights
    match_weight_line_level: float = 0.70
    match_weight_amount: float = 0.20
    match_weight_date: float = 0.10
    
    # Auto-approval threshold (0.0 to 1.0)
    auto_approve_threshold: float = 0.95
    
    # Database settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # JWT settings
    jwt: JWTConfig = Field(default_factory=JWTConfig)


@lru_cache()
def get_config() -> AppConfig:
    """Get cached application configuration."""
    return AppConfig()


config = get_config()
