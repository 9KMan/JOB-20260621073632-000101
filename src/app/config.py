// src/app/config.py
"""Configuration management for FinaRo AP Automation Engine."""
import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    
    host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    name: str = Field(default_factory=lambda: os.getenv("DB_NAME", "finaro_ap"))
    user: str = Field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", "postgres"))
    pool_size: int = Field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10")))
    max_overflow: int = Field(default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20")))
    
    @property
    def async_url(self) -> str:
        """Get async database URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def sync_url(self) -> str:
        """Get sync database URL for SQLAlchemy."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class JWTSettings(BaseModel):
    """JWT authentication settings."""
    
    secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me-in-production"))
    algorithm: str = Field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = Field(default_factory=lambda: int(os.getenv("JWT_EXPIRE_MINUTES", "30")))
    refresh_token_expire_days: int = Field(default_factory=lambda: int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7")))


class MatchingSettings(BaseModel):
    """Matching engine configuration."""
    
    line_match_weight: float = Field(default_factory=lambda: float(os.getenv("LINE_MATCH_WEIGHT", "0.70")))
    amount_match_weight: float = Field(default_factory=lambda: float(os.getenv("AMOUNT_MATCH_WEIGHT", "0.20")))
    date_match_weight: float = Field(default_factory=lambda: float(os.getenv("DATE_MATCH_WEIGHT", "0.10")))
    
    auto_approve_threshold: float = Field(default_factory=lambda: float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.95")))
    pending_threshold: float = Field(default_factory=lambda: float(os.getenv("PENDING_THRESHOLD", "0.70")))
    
    date_tolerance_days: int = Field(default_factory=lambda: int(os.getenv("DATE_TOLERANCE_DAYS", "7")))
    amount_tolerance_percent: float = Field(default_factory=lambda: float(os.getenv("AMOUNT_TOLERANCE_PERCENT", "5.0")))


class Settings(BaseSettings):
    """Application settings."""
    
    app_name: str = "FinaRo AP Automation Engine"
    app_version: str = "1.0.0"
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    api_v1_prefix: str = "/api/v1"
    
    cors_origins: list[str] = Field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    matching: MatchingSettings = Field(default_factory=MatchingSettings)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
