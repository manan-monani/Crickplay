"""
Configuration management for Crickplay Backend API
Uses Pydantic Settings for environment variable management
"""

from typing import List
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # API Configuration
    PROJECT_NAME: str = "Crickplay API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://crickplay_user:crickplay_password@localhost:5432/crickplay_db",
        description="Async database URL for SQLAlchemy",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://crickplay_user:crickplay_password@localhost:5432/crickplay_db",
        description="Sync database URL for Alembic migrations",
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://:crickplay_redis_password@localhost:6379/0",
        description="Redis connection URL",
    )
    REDIS_CACHE_TTL: int = Field(
        default=300, description="Default cache TTL in seconds"
    )

    # JWT Configuration
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-min-32-characters-long",
        description="Secret key for JWT encoding (MUST be changed in production)",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = Field(
        default='["http://localhost:3000","http://localhost:8000"]',
        description="JSON array of allowed CORS origins",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from JSON string or list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_FAN: str = "100/hour"
    RATE_LIMIT_PROFESSIONAL: str = "1000/hour"
    RATE_LIMIT_ENTERPRISE: str = "10000/hour"

    # Kafka Configuration (for Phase 1 integration)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:29092"
    KAFKA_TOPIC: str = "live_match_deliveries"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Cache Configuration
    ENABLE_QUERY_CACHE: bool = True

    # Monitoring
    ENABLE_METRICS: bool = True

    def get_cors_origins(self) -> List[str]:
        """Get parsed CORS origins"""
        if isinstance(self.BACKEND_CORS_ORIGINS, list):
            return self.BACKEND_CORS_ORIGINS
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except:
            return [self.BACKEND_CORS_ORIGINS]


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance
    Using lru_cache ensures settings are loaded only once
    """
    return Settings()


# Export settings instance
settings = get_settings()
