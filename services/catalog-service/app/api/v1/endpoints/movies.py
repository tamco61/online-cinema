"""Movie endpoints - public and admin."""

import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService, get_cache_service
from app.db.session import get_db
from app.schemas.movie import (
    MovieCreate,
    MovieDetailResponse,
    MovieListResponse,
    MovieResponse,
    MovieUpdate,
)
from app.services.kafka_producer import KafkaProducerService, get_kafka_producer
from app.services.movie_service import MovieService

router = APIRouter()


async def get_movie_service(
    db: AsyncSession = Depends(get_db),
    kafka: KafkaProducerService = Depends(get_kafka_producer),
    cache: CacheService = Depends(get_cache_service),
) -> MovieService:
    """Dependency for movie service."""
    return MovieService(db, kafka, cache)


# Public endpoints

@router.get("", response_model=MovieListResponse, tags=["Movies - Public"])
async def get_movies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    movie_service: MovieService = Depends(get_movie_service),
):
    """Get published movies list (public)."""
    movies, total = await movie_service.get_movies(
        page=page,
        page_size=page_size,
        published_only=True,
        search=search,
    )

    return MovieListResponse(
        items=[MovieResponse.model_validate(m) for m in movies],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{movie_id}", response_model=MovieDetailResponse, tags=["Movies - Public"])
async def get_movie(
    movie_id: uuid.UUID,
    movie_service: MovieService = Depends(get_movie_service),
):
    """Get movie details (public - uses cache)."""
    movie = await movie_service.get_movie_by_id(movie_id)
    if not movie or not movie.is_published:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    return MovieDetailResponse.model_validate(movie)


# Admin endpoints

@router.post("", response_model=MovieResponse, tags=["Movies - Admin"])
async def create_movie(
    movie_data: MovieCreate,
    movie_service: MovieService = Depends(get_movie_service),
):
    """Create movie (admin) - publishes Kafka event."""
    movie = await movie_service.create_movie(movie_data)
    return MovieResponse.model_validate(movie)


@router.patch("/{movie_id}", response_model=MovieResponse, tags=["Movies - Admin"])
async def update_movie(
    movie_id: uuid.UUID,
    movie_data: MovieUpdate,
    movie_service: MovieService = Depends(get_movie_service),
):
    """Update movie (admin) - publishes Kafka event, invalidates cache."""
    movie = await movie_service.update_movie(movie_id, movie_data)
    return MovieResponse.model_validate(movie)


@router.post("/{movie_id}/publish", response_model=MovieResponse, tags=["Movies - Admin"])
async def publish_movie(
    movie_id: uuid.UUID,
    movie_service: MovieService = Depends(get_movie_service),
):
    """Publish movie (admin) - publishes Kafka event, invalidates cache."""
    movie = await movie_service.publish_movie(movie_id)
    return MovieResponse.model_validate(movie)
