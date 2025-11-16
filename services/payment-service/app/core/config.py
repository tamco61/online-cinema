from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "payment-service"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8007
    DEBUG: bool = False

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/payment_db"
    DATABASE_ECHO: bool = False

    # Redis (for idempotency)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    IDEMPOTENCY_KEY_TTL: int = 86400  # 24 hours

    # YooMoney
    YOOMONEY_SHOP_ID: str = ""
    YOOMONEY_SECRET_KEY: str = ""
    YOOMONEY_API_URL: str = "https://api.yookassa.ru/v3"
    YOOMONEY_WEBHOOK_SECRET: str = ""  # For webhook verification

    # Payment Settings
    DEFAULT_CURRENCY: str = "RUB"
    PAYMENT_TIMEOUT_MINUTES: int = 15
    SUCCESS_REDIRECT_URL: str = "https://cinema.example.com/payment/success"
    CANCEL_REDIRECT_URL: str = "https://cinema.example.com/payment/cancel"

    # User Service Integration
    USER_SERVICE_URL: str = "http://localhost:8002"
    USER_SERVICE_API_KEY: str = ""  # For service-to-service auth

    # Subscription Plans (можно хранить в БД, но для простоты здесь)
    PLANS: dict = {
        "basic": {"name": "Basic", "price": 299.00, "duration_days": 30},
        "premium": {"name": "Premium", "price": 599.00, "duration_days": 30},
        "family": {"name": "Family", "price": 899.00, "duration_days": 30},
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
