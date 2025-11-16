from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.clickhouse_client import get_clickhouse_client, ClickHouseClient
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    PopularContentResponse,
    UserStatsResponse,
    ViewingEventCreate
)
from app.core.config import settings
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(
    ch_client: ClickHouseClient = Depends(get_clickhouse_client)
) -> AnalyticsService:
    """Dependency to get analytics service"""
    return AnalyticsService(ch_client)


@router.get("/content/popular", response_model=PopularContentResponse)
async def get_popular_content(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get most popular movies by views

    **Query ClickHouse:**
    ```sql
    SELECT
        movie_id,
        sum(start_count) as total_views,
        sum(unique_viewers) as unique_viewers,
        round(sum(finish_count) / sum(start_count) * 100, 2) as completion_rate
    FROM popular_content_mv
    WHERE event_date >= today() - 7
    GROUP BY movie_id
    ORDER BY total_views DESC
    LIMIT 10
    ```

    **Example:**
    ```bash
    curl "http://localhost:8006/api/v1/analytics/content/popular?days=7&limit=10"
    ```

    **Response:**
    ```json
    {
      "items": [
        {
          "movie_id": "uuid",
          "total_views": 1500,
          "unique_viewers": 800,
          "completion_rate": 75.5
        }
      ],
      "period_days": 7,
      "total_items": 10
    }
    ```
    """
    try:
        return analytics_service.get_popular_content(days=days, limit=limit)

    except Exception as e:
        logger.error(f"Error getting popular content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular content")


@router.get("/user/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get user viewing statistics

    **Queries ClickHouse:**

    1. **Main stats:**
    ```sql
    SELECT
        sum(movies_started) as total_started,
        sum(movies_finished) as total_finished,
        sum(unique_movies) as unique_movies
    FROM user_stats_mv
    WHERE user_id = '{user_id}'
      AND event_date >= today() - 30
    ```

    2. **Total watch time:**
    ```sql
    SELECT sum(position_seconds) as total_seconds
    FROM viewing_events
    WHERE user_id = '{user_id}'
      AND event_type = 'finish'
      AND event_time >= now() - INTERVAL 30 DAY
    ```

    3. **Most watched movie:**
    ```sql
    SELECT movie_id, count() as watch_count
    FROM viewing_events
    WHERE user_id = '{user_id}'
      AND event_type = 'start'
      AND event_time >= now() - INTERVAL 30 DAY
    GROUP BY movie_id
    ORDER BY watch_count DESC
    LIMIT 1
    ```

    **Example:**
    ```bash
    curl "http://localhost:8006/api/v1/analytics/user/{user_id}/stats?days=30"
    ```

    **Response:**
    ```json
    {
      "user_id": "uuid",
      "movies_started": 25,
      "movies_finished": 18,
      "unique_movies_watched": 20,
      "total_watch_time_seconds": 108000,
      "completion_rate": 72.0,
      "period_days": 30,
      "most_watched_movie_id": "uuid"
    }
    ```
    """
    try:
        return analytics_service.get_user_stats(user_id=user_id, days=days)

    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")


@router.get("/trends")
async def get_viewing_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get viewing trends over time

    **Query ClickHouse:**
    ```sql
    SELECT
        toDate(event_time) as date,
        countIf(event_type = 'start') as starts,
        countIf(event_type = 'finish') as finishes,
        uniq(user_id) as unique_users,
        uniq(movie_id) as unique_movies
    FROM viewing_events
    WHERE event_time >= now() - INTERVAL 7 DAY
    GROUP BY date
    ORDER BY date
    ```

    **Example:**
    ```bash
    curl "http://localhost:8006/api/v1/analytics/trends?days=7"
    ```

    **Response:**
    ```json
    {
      "period_days": 7,
      "trends": [
        {
          "date": "2024-11-10",
          "starts": 500,
          "finishes": 350,
          "unique_users": 200,
          "unique_movies": 50
        }
      ]
    }
    ```
    """
    try:
        return analytics_service.get_viewing_trends(days=days)

    except Exception as e:
        logger.error(f"Error getting viewing trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get viewing trends")


@router.get("/peak-hours")
async def get_peak_hours(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get peak viewing hours

    **Query ClickHouse:**
    ```sql
    SELECT
        toHour(event_time) as hour,
        count() as events_count,
        uniq(user_id) as unique_users
    FROM viewing_events
    WHERE event_time >= now() - INTERVAL 7 DAY
    GROUP BY hour
    ORDER BY hour
    ```

    **Example:**
    ```bash
    curl "http://localhost:8006/api/v1/analytics/peak-hours?days=7"
    ```

    **Response:**
    ```json
    {
      "period_days": 7,
      "peak_hours": [
        {
          "hour": 20,
          "events_count": 5000,
          "unique_users": 1200
        }
      ]
    }
    ```
    """
    try:
        return analytics_service.get_peak_hours(days=days)

    except Exception as e:
        logger.error(f"Error getting peak hours: {e}")
        raise HTTPException(status_code=500, detail="Failed to get peak hours")


@router.post("/events")
async def create_viewing_event(
    event: ViewingEventCreate,
    ch_client: ClickHouseClient = Depends(get_clickhouse_client)
):
    """
    Create viewing event manually (HTTP endpoint)

    **Note:** This is optional. Events are typically consumed from Kafka.

    **Body:**
    ```json
    {
      "user_id": "uuid",
      "movie_id": "uuid",
      "event_type": "start",
      "position_seconds": 0,
      "session_id": "uuid",
      "metadata": {}
    }
    ```

    **Example:**
    ```bash
    curl -X POST http://localhost:8006/api/v1/analytics/events \\
      -H "Content-Type: application/json" \\
      -d '{
        "user_id": "uuid",
        "movie_id": "uuid",
        "event_type": "start",
        "position_seconds": 0
      }'
    ```
    """
    try:
        ch_client.insert_viewing_event(
            user_id=event.user_id,
            movie_id=event.movie_id,
            event_type=event.event_type,
            position_seconds=event.position_seconds,
            event_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            session_id=event.session_id,
            metadata=json.dumps(event.metadata)
        )

        return {
            "success": True,
            "message": "Viewing event created"
        }

    except Exception as e:
        logger.error(f"Error creating viewing event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create viewing event")
