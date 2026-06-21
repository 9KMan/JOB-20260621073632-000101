// src/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finaro"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Matching weights
    match_line_weight: float = 0.70
    match_amount_weight: float = 0.20
    match_date_weight: float = 0.10
    
    # Match thresholds
    match_auto_approve_threshold: float = 0.90
    match_human_review_threshold: float = 0.60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
