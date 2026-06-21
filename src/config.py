// src/config.py
"""Application configuration."""
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    username: str = Field(default="postgres", env="POSTGRES_USER")
    password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    name: str = Field(default="finaro_ap", env="POSTGRES_DB")
    
    @property
    def url(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def sync_url(self) -> str:
        """Get synchronous database URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class JWTSettings(BaseSettings):
    """JWT configuration."""
    
    secret_key: str = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")


class AppSettings(BaseSettings):
    """Application settings."""
    
    name: str = "FinaRo AP Automation"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    api_v1_prefix: str = "/api/v1"
    
    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins."""
        return ["*"]


class Settings(BaseSettings):
    """Combined settings."""
    
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
