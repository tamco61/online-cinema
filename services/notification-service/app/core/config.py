from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "notification-service"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8008
    DEBUG: bool = False

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "notification-service"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    ENABLE_KAFKA: bool = True

    # Kafka Topics
    KAFKA_TOPIC_USER_EVENTS: str = "user.events"
    KAFKA_TOPIC_CATALOG_EVENTS: str = "catalog.events"
    KAFKA_TOPIC_RECOMMENDATION_EVENTS: str = "recommendation.events"

    # Email Provider
    EMAIL_PROVIDER: str = "sendgrid"  # sendgrid, aws_ses, console
    EMAIL_FROM_ADDRESS: str = "noreply@cinema.example.com"
    EMAIL_FROM_NAME: str = "Online Cinema"

    # SendGrid
    SENDGRID_API_KEY: str = ""

    # AWS SES
    AWS_SES_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Push Provider
    PUSH_PROVIDER: str = "fcm"  # fcm, console

    # Firebase Cloud Messaging
    FCM_SERVER_KEY: str = ""
    FCM_PROJECT_ID: str = ""
    FCM_CREDENTIALS_PATH: str = ""  # Path to Firebase service account JSON

    # User Service Integration (for fetching user preferences)
    USER_SERVICE_URL: str = "http://localhost:8002"
    USER_SERVICE_API_KEY: str = ""

    # Notification Settings
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    ENABLE_PUSH_NOTIFICATIONS: bool = True
    MAX_RETRY_ATTEMPTS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
