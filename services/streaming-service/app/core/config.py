from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "streaming-service"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    DEBUG: bool = False

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "streaming_service"
    POSTGRES_PASSWORD: str = "streaming_password"
    POSTGRES_DB: str = "streaming_db"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 3
    REDIS_PASSWORD: str | None = None
    REDIS_PROGRESS_TTL: int = 86400  # 24 hours
    REDIS_SUBSCRIPTION_CACHE_TTL: int = 300  # 5 minutes

    # S3/MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "vod"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    SIGNED_URL_EXPIRATION: int = 3600  # 1 hour

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "stream"
    ENABLE_KAFKA: bool = True

    # User Service Integration
    USER_SERVICE_URL: str = "http://localhost:8002"
    USER_SERVICE_TIMEOUT: int = 5

    # JWT (for token validation)
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Progress Sync
    PROGRESS_SYNC_INTERVAL: int = 60  # Sync to DB every 60 seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
