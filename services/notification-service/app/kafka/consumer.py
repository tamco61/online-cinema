"""
Kafka Consumer

Consumes events from Kafka topics and routes to appropriate handlers
"""

from aiokafka import AIOKafkaConsumer
import json
import logging
import asyncio
from typing import Dict, Callable

from app.core.config import settings
from app.kafka.handlers.subscription_handler import SubscriptionEventHandler
from app.kafka.handlers.catalog_handler import CatalogEventHandler
from app.kafka.handlers.recommendation_handler import RecommendationEventHandler
from app.providers.email import get_email_provider
from app.providers.push import get_push_provider

logger = logging.getLogger(__name__)


class NotificationEventConsumer:
    """
    Kafka consumer for notification events

    Consumes events from multiple topics and routes to handlers:
    - user.events -> SubscriptionEventHandler
    - catalog.events -> CatalogEventHandler
    - recommendation.events -> RecommendationEventHandler
    """

    def __init__(self):
        self.consumer: AIOKafkaConsumer | None = None
        self.running = False
        self.email_provider = get_email_provider()
        self.push_provider = get_push_provider()

        # Initialize handlers
        self.subscription_handler = SubscriptionEventHandler(
            self.email_provider,
            self.push_provider
        )
        self.catalog_handler = CatalogEventHandler(
            self.email_provider,
            self.push_provider
        )
        self.recommendation_handler = RecommendationEventHandler(
            self.email_provider,
            self.push_provider
        )

        # Event router: topic -> handler
        self.event_router: Dict[str, Callable] = {
            settings.KAFKA_TOPIC_USER_EVENTS: self._route_user_event,
            settings.KAFKA_TOPIC_CATALOG_EVENTS: self._route_catalog_event,
            settings.KAFKA_TOPIC_RECOMMENDATION_EVENTS: self._route_recommendation_event,
        }

    async def start(self):
        """Start Kafka consumer"""
        if not settings.ENABLE_KAFKA:
            logger.warning("⚠️  Kafka is disabled. Consumer will not start.")
            return

        try:
            # Subscribe to topics
            topics = list(self.event_router.keys())

            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            await self.consumer.start()
            logger.info(f"✅ Kafka consumer started. Subscribed to: {', '.join(topics)}")

            self.running = True

            # Start consuming messages
            await self._consume_messages()

        except Exception as e:
            logger.error(f"❌ Kafka consumer error: {e}")
            raise

    async def stop(self):
        """Stop Kafka consumer"""
        self.running = False

        if self.consumer:
            await self.consumer.stop()
            logger.info("🔌 Kafka consumer stopped")

    async def _consume_messages(self):
        """Main consumer loop"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                await self._process_message(message)

        except Exception as e:
            logger.error(f"❌ Message consumption error: {e}")

    async def _process_message(self, message):
        """Process individual Kafka message"""
        try:
            topic = message.topic
            event = message.value

            logger.info(f"📨 Received event from {topic}: {event.get('event_type', 'unknown')}")

            # Route to appropriate handler
            router_func = self.event_router.get(topic)
            if router_func:
                await router_func(event)
            else:
                logger.warning(f"No router found for topic: {topic}")

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

    async def _route_user_event(self, event: dict):
        """Route user events to subscription handler"""
        event_type = event.get("event_type")

        if event_type in ["subscription.created", "subscription.activated"]:
            await self.subscription_handler.handle_subscription_created(event)

        elif event_type in ["subscription.expired", "subscription.cancelled"]:
            await self.subscription_handler.handle_subscription_expired(event)

        elif event_type == "subscription.renewed":
            await self.subscription_handler.handle_subscription_renewed(event)

        else:
            logger.debug(f"Unhandled user event type: {event_type}")

    async def _route_catalog_event(self, event: dict):
        """Route catalog events to catalog handler"""
        event_type = event.get("event_type")

        if event_type == "movie.published":
            await self.catalog_handler.handle_movie_published(event)

        elif event_type == "movie.updated":
            await self.catalog_handler.handle_movie_updated(event)

        else:
            logger.debug(f"Unhandled catalog event type: {event_type}")

    async def _route_recommendation_event(self, event: dict):
        """Route recommendation events to recommendation handler"""
        event_type = event.get("event_type")

        if event_type == "daily_digest":
            await self.recommendation_handler.handle_daily_digest(event)

        elif event_type == "personalized_recommendation":
            await self.recommendation_handler.handle_personalized_recommendation(event)

        else:
            logger.debug(f"Unhandled recommendation event type: {event_type}")
