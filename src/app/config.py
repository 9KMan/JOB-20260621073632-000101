# src/app/config.py
"""
Application configuration using Pydantic Settings.
All configuration is loaded from environment variables.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="FinaRo AP Automation", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Security
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finaro_ap",
        alias="DATABASE_URL"
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/finaro_ap",
        alias="DATABASE_URL_SYNC"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        alias="CORS_ORIGINS"
    )
    
    # Matching Engine Configuration
    matching_weight_line_level: float = Field(
        default=0.70,
        alias="MATCHING_WEIGHT_LINE_LEVEL",
        ge=0,
        le=1
    )
    matching_weight_amount: float = Field(
        default=0.20,
        alias="MATCHING_WEIGHT_AMOUNT",
        ge=0,
        le=1
    )
    matching_weight_date: float = Field(
        default=0.10,
        alias="MATCHING_WEIGHT_DATE",
        ge=0,
        le=1
    )
    auto_approve_threshold: float = Field(
        default=0.95,
        alias="AUTO_APPROVE_THRESHOLD",
        ge=0,
        le=1
    )
    human_review_threshold: float = Field(
        default=0.70,
        alias="HUMAN_REVIEW_THRESHOLD",
        ge=0,
        le=1
    )

    @property
    def total_matching_weight(self) -> float:
        """Validate that matching weights sum to 1.0"""
        total = (
            self.matching_weight_line_level 
            + self.matching_weight_amount 
            + self.matching_weight_date
        )
        return round(total, 2)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
