"""
OpenTrace API Configuration
Loads settings from environment variables with sensible defaults.
Supports SQLite (zero-conf local dev) and PostgreSQL.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "OpenTrace"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database: Supports SQLite (aiosqlite) or PostgreSQL (asyncpg)
    DATABASE_URL: str = "sqlite+aiosqlite:///./opentrace.db"
    
    # Security
    SECRET_KEY: str = "opentrace_super_secret_jwt_key_change_in_production_994812"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Redis / Celery (Optional for local dev, used in production worker)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]
    
    # Engine Settings
    DEFAULT_CONCURRENCY: int = 12
    DEFAULT_TIMEOUT_SECONDS: float = 8.0
    MAX_SEARCH_DEPTH: int = 2


settings = Settings()
