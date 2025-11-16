"""
Application configuration using Pydantic Settings.

Configuration is loaded from environment variables with optional .env file support.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    All settings can be overridden via environment variables.
    Example: SERVICE_NAME=my-service python main.py
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Configuration
    SERVICE_NAME: str = Field(default="cinema-service", description="Service name")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    WORKERS: int = Field(default=1, description="Number of worker processes")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    JSON_LOGS: bool = Field(default=True, description="Enable JSON logging")

    # Database Configuration
    POSTGRES_USER: str = Field(default="cinema", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="cinema123", description="PostgreSQL password")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="cinema", description="PostgreSQL database name")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", description="Kafka bootstrap servers")
    KAFKA_TOPIC_PREFIX: str = Field(default="cinema", description="Kafka topic prefix")
    KAFKA_CONSUMER_GROUP: str = Field(default="cinema-consumer", description="Kafka consumer group")

    # Observability
    JAEGER_HOST: str = Field(default="localhost", description="Jaeger agent host")
    JAEGER_PORT: int = Field(default=6831, description="Jaeger agent port")
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    ENABLE_TRACING: bool = Field(default=True, description="Enable distributed tracing")

    # Security
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        description="JWT secret key",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiration (minutes)")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration (days)")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )

    # Rate Limiting
    ENABLE_RATE_LIMITING: bool = Field(default=False, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Requests per minute per IP")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Requests per hour per IP")

    # Feature Flags
    ENABLE_API_DOCS: bool = Field(default=True, description="Enable /docs endpoint")

    @property
    def database_url(self) -> str:
        """
        Construct PostgreSQL DSN.

        Returns:
            Database connection URL
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        """
        Construct synchronous PostgreSQL DSN (for Alembic).

        Returns:
            Synchronous database connection URL
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """
        Construct Redis URL.

        Returns:
            Redis connection URL
        """
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings instance

    Example:
        ```python
        from app.core.config import get_settings

        settings = get_settings()
        print(settings.SERVICE_NAME)
        ```
    """
    return Settings()


# Convenience instance
settings = get_settings()
