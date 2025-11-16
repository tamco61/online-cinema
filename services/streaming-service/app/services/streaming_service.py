from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import WatchProgress, StreamSession
from app.core.s3_client import S3Client
from app.core.cache import RedisCache
from app.core.kafka_producer import KafkaEventProducer
from app.core.user_service_client import UserServiceClient
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class StreamingService:
    """Service for managing video streaming and watch progress"""

    def __init__(
        self,
        db: AsyncSession,
        s3_client: S3Client,
        cache: RedisCache,
        kafka_producer: KafkaEventProducer,
        user_service_client: UserServiceClient
    ):
        self.db = db
        self.s3_client = s3_client
        self.cache = cache
        self.kafka_producer = kafka_producer
        self.user_service_client = user_service_client

    async def check_access(self, user_id: str, access_token: str) -> tuple[bool, str]:
        """
        Check if user has access to streaming

        Returns:
            (has_access: bool, reason: str)
        """
        # Check active subscription
        has_subscription = await self.user_service_client.check_active_subscription(
            user_id,
            access_token
        )

        if not has_subscription:
            return False, "No active subscription"

        return True, "Access granted"

    async def start_stream(
        self,
        user_id: str,
        movie_id: str,
        manifest_type: str = "hls",
        user_agent: str = None,
        ip_address: str = None
    ) -> str:
        """
        Start streaming session and generate manifest URL

        Args:
            user_id: User UUID
            movie_id: Movie UUID
            manifest_type: "hls" or "dash"
            user_agent: Client user agent
            ip_address: Client IP address

        Returns:
            Signed manifest URL
        """
        # Generate signed URL for manifest
        manifest_url = self.s3_client.get_manifest_url(movie_id, manifest_type)

        # Create stream session
        session = StreamSession(
            user_id=uuid.UUID(user_id),
            movie_id=uuid.UUID(movie_id),
            started_at=datetime.utcnow(),
            user_agent=user_agent,
            ip_address=ip_address
        )

        self.db.add(session)
        await self.db.commit()

        logger.info(f"Started stream session: user={user_id}, movie={movie_id}")

        # Publish Kafka event
        await self.kafka_producer.publish_stream_start(user_id, movie_id)

        return manifest_url

    async def update_progress(self, user_id: str, movie_id: str, position_seconds: int):
        """
        Update watch progress

        Saves to Redis (fast) and will be synced to DB periodically
        """
        # Save to Redis
        await self.cache.set_watch_progress(user_id, movie_id, position_seconds)

        # Also save to DB immediately (can be optimized with background task)
        await self._sync_progress_to_db(user_id, movie_id, position_seconds)

        # Publish progress event
        await self.kafka_producer.publish_progress_update(user_id, movie_id, position_seconds)

        logger.debug(f"Updated progress: user={user_id}, movie={movie_id}, position={position_seconds}s")

    async def get_progress(self, user_id: str, movie_id: str) -> int:
        """
        Get watch progress

        Tries Redis first, falls back to DB
        """
        # Try Redis first
        progress_data = await self.cache.get_watch_progress(user_id, movie_id)

        if progress_data:
            return progress_data["position_seconds"]

        # Fall back to DB
        result = await self.db.execute(
            select(WatchProgress).where(
                WatchProgress.user_id == uuid.UUID(user_id),
                WatchProgress.movie_id == uuid.UUID(movie_id)
            )
        )

        progress = result.scalar_one_or_none()

        if progress:
            # Cache it
            await self.cache.set_watch_progress(user_id, movie_id, progress.position_seconds)
            return progress.position_seconds

        return 0

    async def _sync_progress_to_db(self, user_id: str, movie_id: str, position_seconds: int):
        """Sync progress from Redis to PostgreSQL"""
        try:
            # Check if record exists
            result = await self.db.execute(
                select(WatchProgress).where(
                    WatchProgress.user_id == uuid.UUID(user_id),
                    WatchProgress.movie_id == uuid.UUID(movie_id)
                )
            )

            progress = result.scalar_one_or_none()

            if progress:
                # Update existing
                progress.position_seconds = position_seconds
                progress.updated_at = datetime.utcnow()
                progress.last_watched_at = datetime.utcnow()
            else:
                # Create new
                progress = WatchProgress(
                    user_id=uuid.UUID(user_id),
                    movie_id=uuid.UUID(movie_id),
                    position_seconds=position_seconds,
                    last_watched_at=datetime.utcnow()
                )
                self.db.add(progress)

            await self.db.commit()

            logger.debug(f"Synced progress to DB: user={user_id}, movie={movie_id}")

        except Exception as e:
            logger.error(f"Error syncing progress to DB: {e}")
            await self.db.rollback()

    async def end_stream(self, user_id: str, movie_id: str, position_seconds: int):
        """
        End streaming session

        Updates final progress and publishes stop event
        """
        # Update final progress
        await self.update_progress(user_id, movie_id, position_seconds)

        # Publish stop event
        await self.kafka_producer.publish_stream_stop(user_id, movie_id, position_seconds)

        logger.info(f"Ended stream: user={user_id}, movie={movie_id}, final_position={position_seconds}s")
