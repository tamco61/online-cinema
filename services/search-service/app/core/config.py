from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "search-service"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8004
    DEBUG: bool = False

    # Elasticsearch
    ELASTICSEARCH_HOSTS: list[str] = ["http://localhost:9200"]
    ELASTICSEARCH_INDEX: str = "movies"
    ELASTICSEARCH_TIMEOUT: int = 30
    ELASTICSEARCH_MAX_RETRIES: int = 3

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "catalog"
    KAFKA_CONSUMER_GROUP: str = "search-service"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    ENABLE_KAFKA: bool = True

    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    REDIS_PASSWORD: str | None = None
    REDIS_CACHE_TTL: int = 300  # 5 minutes
    ENABLE_CACHE: bool = True

    # Search Settings
    SEARCH_DEFAULT_PAGE_SIZE: int = 20
    SEARCH_MAX_PAGE_SIZE: int = 100
    AUTOCOMPLETE_MAX_SUGGESTIONS: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
