from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.s3_client import get_s3_client, S3Client
from app.core.cache import get_cache, RedisCache
from app.core.kafka_producer import get_kafka_producer, KafkaEventProducer
from app.core.user_service_client import get_user_service_client, UserServiceClient
from app.core.security import verify_access_token
from app.core.config import settings
from app.services.streaming_service import StreamingService
from app.schemas.streaming import (
    StreamRequest,
    StreamResponse,
    ProgressUpdateRequest,
    ProgressUpdateResponse,
    WatchProgressResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["Streaming"])


def get_access_token(authorization: str = Header(...)) -> str:
    """Extract access token from Authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    return authorization.replace("Bearer ", "")


async def get_current_user_id(access_token: str = Depends(get_access_token)) -> str:
    """Get current user ID from access token"""
    user_id = verify_access_token(access_token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return str(user_id)


async def get_streaming_service(
    db: AsyncSession = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_client),
    cache: RedisCache = Depends(get_cache),
    kafka_producer: KafkaEventProducer = Depends(get_kafka_producer),
    user_service_client: UserServiceClient = Depends(get_user_service_client)
) -> StreamingService:
    """Dependency to get streaming service"""
    return StreamingService(db, s3_client, cache, kafka_producer, user_service_client)


@router.post("/{movie_id}", response_model=StreamResponse)
async def start_streaming(
    movie_id: str,
    request_body: StreamRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    access_token: str = Depends(get_access_token),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    """
    Start streaming a movie

    **Access Control:**
    - Requires valid JWT token
    - Requires active subscription

    **Returns:**
    - Signed URL for HLS/DASH manifest
    - URL expires in 1 hour

    **Example:**
    ```bash
    curl -X POST http://localhost:8005/api/v1/stream/{movie_id} \\
      -H "Authorization: Bearer <token>" \\
      -H "Content-Type: application/json" \\
      -d '{"manifest_type": "hls"}'
    ```
    """
    # Check access (subscription)
    has_access, reason = await streaming_service.check_access(user_id, access_token)

    if not has_access:
        raise HTTPException(status_code=403, detail=f"Access denied: {reason}")

    # Get client info
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    # Start stream and get manifest URL
    try:
        manifest_url = await streaming_service.start_stream(
            user_id=user_id,
            movie_id=movie_id,
            manifest_type=request_body.manifest_type,
            user_agent=user_agent,
            ip_address=ip_address
        )

        return StreamResponse(
            manifest_url=manifest_url,
            expires_in=settings.SIGNED_URL_EXPIRATION,
            manifest_type=request_body.manifest_type
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        raise HTTPException(status_code=500, detail="Failed to start streaming")


@router.post("/{movie_id}/progress", response_model=ProgressUpdateResponse)
async def update_watch_progress(
    movie_id: str,
    progress: ProgressUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    """
    Update watch progress

    **Tracking:**
    - Saved to Redis (fast access)
    - Synced to PostgreSQL (persistent storage)
    - Kafka event published

    **Client should call this endpoint periodically (e.g., every 10 seconds)**

    **Example:**
    ```bash
    curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/progress \\
      -H "Authorization: Bearer <token>" \\
      -H "Content-Type: application/json" \\
      -d '{"position_seconds": 120}'
    ```
    """
    try:
        await streaming_service.update_progress(
            user_id=user_id,
            movie_id=movie_id,
            position_seconds=progress.position_seconds
        )

        return ProgressUpdateResponse(
            success=True,
            position_seconds=progress.position_seconds
        )

    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")


@router.get("/{movie_id}/progress", response_model=WatchProgressResponse)
async def get_watch_progress(
    movie_id: str,
    user_id: str = Depends(get_current_user_id),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    """
    Get current watch progress

    **Returns:**
    - Current playback position
    - Last watched timestamp

    **Example:**
    ```bash
    curl http://localhost:8005/api/v1/stream/{movie_id}/progress \\
      -H "Authorization: Bearer <token>"
    ```
    """
    try:
        position = await streaming_service.get_progress(user_id, movie_id)

        return WatchProgressResponse(
            user_id=user_id,
            movie_id=movie_id,
            position_seconds=position
        )

    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress")


@router.post("/{movie_id}/stop")
async def stop_streaming(
    movie_id: str,
    progress: ProgressUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    streaming_service: StreamingService = Depends(get_streaming_service)
):
    """
    Stop streaming session

    **Actions:**
    - Updates final watch progress
    - Publishes stream.stop event
    - Ends stream session

    **Example:**
    ```bash
    curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/stop \\
      -H "Authorization: Bearer <token>" \\
      -H "Content-Type: application/json" \\
      -d '{"position_seconds": 1800}'
    ```
    """
    try:
        await streaming_service.end_stream(
            user_id=user_id,
            movie_id=movie_id,
            position_seconds=progress.position_seconds
        )

        return {
            "success": True,
            "message": "Stream stopped successfully"
        }

    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop stream")
