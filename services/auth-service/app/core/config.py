"""
Application configuration using Pydantic Settings.

Configuration is loaded from environment variables with optional .env file support.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Auth Service settings.

    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Configuration
    SERVICE_NAME: str = Field(default="auth-service", description="Service name")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8001, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    WORKERS: int = Field(default=1, description="Number of worker processes")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    JSON_LOGS: bool = Field(default=True, description="Enable JSON logging")

    # Database Configuration
    POSTGRES_USER: str = Field(default="auth_user", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="auth_password", description="PostgreSQL password")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="auth_db", description="PostgreSQL database name")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")

    # Security & JWT
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-min-32-chars-please",
        description="JWT secret key (min 32 chars)",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiration (minutes)")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration (days)")

    # Password Policy
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")

    # OAuth2 Configuration (Google)
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, description="Google OAuth2 client ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Google OAuth2 client secret")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8001/api/v1/auth/oauth/google/callback",
        description="Google OAuth2 redirect URI",
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )

    # Rate Limiting (for login endpoint)
    LOGIN_RATE_LIMIT_PER_MINUTE: int = Field(default=5, description="Login attempts per minute per IP")
    LOGIN_RATE_LIMIT_PER_HOUR: int = Field(default=20, description="Login attempts per hour per IP")

    # Feature Flags
    ENABLE_API_DOCS: bool = Field(default=True, description="Enable /docs endpoint")
    ENABLE_OAUTH: bool = Field(default=False, description="Enable OAuth2 authentication")

    # Observability
    JAEGER_HOST: str = Field(default="localhost", description="Jaeger agent host")
    JAEGER_PORT: int = Field(default=6831, description="Jaeger agent port")
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    ENABLE_TRACING: bool = Field(default=True, description="Enable distributed tracing")

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
    """
    return Settings()


# Convenience instance
settings = get_settings()
