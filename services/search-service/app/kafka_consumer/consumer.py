from aiokafka import AIOKafkaConsumer
import json
import logging
from app.core.config import settings
from app.services.search_service import SearchService
from datetime import datetime

logger = logging.getLogger(__name__)


class MovieEventConsumer:
    """
    Kafka consumer for catalog.movie.* events

    Events:
    - catalog.movie.created: Index new movie
    - catalog.movie.updated: Update movie document
    - catalog.movie.published: Update is_published flag
    """

    def __init__(self, search_service: SearchService):
        self.search_service = search_service
        self.consumer: AIOKafkaConsumer | None = None
        self.running = False

    async def start(self):
        """Start Kafka consumer"""
        if not settings.ENABLE_KAFKA:
            logger.warning("⚠️  Kafka is disabled. Consumer will not start.")
            return

        try:
            # Subscribe to all catalog movie topics
            topics = [
                f"{settings.KAFKA_TOPIC_PREFIX}.movie.created",
                f"{settings.KAFKA_TOPIC_PREFIX}.movie.updated",
                f"{settings.KAFKA_TOPIC_PREFIX}.movie.published"
            ]

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

            logger.info(f"📨 Received event from {topic}: {event.get('movie_id')}")

            # Extract event data
            movie_id = event.get("movie_id")
            action = event.get("action")
            payload = event.get("payload", {})

            # Route to appropriate handler
            if action == "created":
                await self._handle_movie_created(movie_id, payload)

            elif action == "updated":
                await self._handle_movie_updated(movie_id, payload)

            elif action == "published":
                await self._handle_movie_published(movie_id, payload)

            else:
                logger.warning(f"⚠️  Unknown action: {action}")

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

    async def _handle_movie_created(self, movie_id: str, payload: dict):
        """
        Handle catalog.movie.created event

        Expected payload:
        {
            "title": "Movie Title",
            "year": 2024,
            "rating": 8.5,
            "description": "...",
            "genres": [...],
            "actors": [...],
            "directors": [...]
        }
        """
        logger.info(f"🎬 Creating movie index: {movie_id}")

        # Build document for indexing
        movie_doc = self._build_movie_document(movie_id, payload)

        # Index the movie
        await self.search_service.index_movie(movie_doc)

    async def _handle_movie_updated(self, movie_id: str, payload: dict):
        """
        Handle catalog.movie.updated event

        Re-index the entire document
        """
        logger.info(f"🔄 Updating movie index: {movie_id}")

        # Build updated document
        movie_doc = self._build_movie_document(movie_id, payload)

        # Re-index the movie
        await self.search_service.index_movie(movie_doc)

    async def _handle_movie_published(self, movie_id: str, payload: dict):
        """
        Handle catalog.movie.published event

        Update is_published flag
        """
        logger.info(f"📢 Publishing movie: {movie_id}")

        is_published = payload.get("is_published", True)
        published_at = payload.get("published_at") or datetime.utcnow().isoformat()

        # Update publish status
        await self.search_service.update_movie_publish_status(
            movie_id,
            is_published,
            published_at
        )

    def _build_movie_document(self, movie_id: str, payload: dict) -> dict:
        """
        Build Elasticsearch document from Kafka event payload
        """
        return {
            "movie_id": movie_id,
            "title": payload.get("title", ""),
            "original_title": payload.get("original_title"),
            "description": payload.get("description"),
            "year": payload.get("year"),
            "duration": payload.get("duration"),
            "rating": payload.get("rating"),
            "age_rating": payload.get("age_rating"),
            "poster_url": payload.get("poster_url"),
            "trailer_url": payload.get("trailer_url"),
            "imdb_id": payload.get("imdb_id"),
            "genres": payload.get("genres", []),
            "actors": payload.get("actors", []),
            "directors": payload.get("directors", []),
            "is_published": payload.get("is_published", False),
            "published_at": payload.get("published_at"),
            "created_at": payload.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat()
        }
