// src/config.py
"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/finaro_ap",
        description="PostgreSQL database URL"
    )
    pool_size: int = Field(default=5, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=0)
    echo: bool = Field(default=False)

    @property
    def pool_config(self) -> dict:
        """Get connection pool configuration."""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,
        }


class JWTSettings(BaseSettings):
    """JWT authentication settings."""
    
    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT token signing"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)


class MatchingSettings(BaseSettings):
    """Matching algorithm configuration."""
    
    weight_line_level: int = Field(default=70, ge=0, le=100)
    weight_amount: int = Field(default=20, ge=0, le=100)
    weight_date: int = Field(default=10, ge=0, le=100)
    auto_approve_threshold: int = Field(default=95, ge=0, le=100)
    human_review_threshold: int = Field(default=70, ge=0, le=100)
    
    def model_post_init(self, __context) -> None:
        """Validate weights sum to 100."""
        total = self.weight_line_level + self.weight_amount + self.weight_date
        if total != 100:
            raise ValueError(
                f"Matching weights must sum to 100, got {total}"
            )


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )
    
    app_name: str = Field(default="FinaRo AP Automation")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    matching: MatchingSettings = Field(default_factory=MatchingSettings)
    
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
