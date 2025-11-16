"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Catalog Service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service
    SERVICE_NAME: str = Field(default="catalog-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8003)
    RELOAD: bool = Field(default=False)

    # Database
    POSTGRES_USER: str = Field(default="catalog_service")
    POSTGRES_PASSWORD: str = Field(default="catalog_password")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="catalog_db")

    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: str | None = Field(default=None)
    REDIS_DB: int = Field(default=0)
    REDIS_CACHE_TTL: int = Field(default=600, description="Cache TTL in seconds (10 min)")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    KAFKA_TOPIC_PREFIX: str = Field(default="catalog")
    ENABLE_KAFKA: bool = Field(default=True, description="Enable Kafka events")

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # Feature Flags
    ENABLE_API_DOCS: bool = Field(default=True)
    ENABLE_CACHE: bool = Field(default=True)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL DSN."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
