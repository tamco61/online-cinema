from fastapi import APIRouter, Depends, Query, HTTPException
from elasticsearch import AsyncElasticsearch
from typing import Optional
from app.core.elasticsearch_client import get_es_client
from app.core.cache import get_cache, RedisCache
from app.services.search_service import SearchService
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SuggestRequest,
    SuggestResponse
)
from app.core.config import settings

router = APIRouter(prefix="/search", tags=["Search"])


async def get_search_service(
    es_client: AsyncElasticsearch = Depends(get_es_client),
    cache: RedisCache = Depends(get_cache)
) -> SearchService:
    """Dependency to get search service"""
    return SearchService(es_client, cache)


@router.get("", response_model=SearchResponse)
async def search_movies(
    query: Optional[str] = Query(None, description="Search query"),
    genres: Optional[str] = Query(None, description="Comma-separated genre slugs (e.g., 'action,drama')"),
    year_from: Optional[int] = Query(None, ge=1900, le=2100, description="Minimum year"),
    year_to: Optional[int] = Query(None, ge=1900, le=2100, description="Maximum year"),
    rating_from: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum rating"),
    rating_to: Optional[float] = Query(None, ge=0.0, le=10.0, description="Maximum rating"),
    age_rating: Optional[str] = Query(None, description="Comma-separated age ratings (e.g., 'PG,PG-13')"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    published_only: bool = Query(True, description="Show only published movies"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search for movies with full-text search and filters

    **Search fields:**
    - Title (boosted 3x)
    - Original title (boosted 2x)
    - Description
    - Actors (boosted 2x)
    - Directors (boosted 2x)

    **Filters:**
    - Genres (by slug)
    - Year range
    - Rating range
    - Age rating

    **Example:**
    ```
    GET /api/v1/search?query=inception&genres=sci-fi,action&year_from=2010&rating_from=8.0
    ```
    """
    # Parse comma-separated values
    genre_list = [g.strip() for g in genres.split(",")] if genres else None
    age_rating_list = [a.strip() for a in age_rating.split(",")] if age_rating else None

    # Build request
    search_request = SearchRequest(
        query=query,
        genres=genre_list,
        year_from=year_from,
        year_to=year_to,
        rating_from=rating_from,
        rating_to=rating_to,
        age_rating=age_rating_list,
        page=page,
        size=size,
        published_only=published_only
    )

    try:
        return await search_service.search_movies(search_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/suggest", response_model=SuggestResponse)
async def autocomplete_movies(
    query: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Autocomplete suggestions for movie titles

    **Returns:**
    - Top matching movie titles
    - Sorted by relevance and rating

    **Example:**
    ```
    GET /api/v1/search/suggest?query=incep&limit=5
    ```
    """
    suggest_request = SuggestRequest(query=query, limit=limit)

    try:
        return await search_service.autocomplete(suggest_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")


@router.get("/health")
async def health_check(
    es_client: AsyncElasticsearch = Depends(get_es_client)
):
    """
    Health check endpoint

    Verifies Elasticsearch connection
    """
    try:
        is_alive = await es_client.ping()

        return {
            "status": "healthy" if is_alive else "unhealthy",
            "elasticsearch": "connected" if is_alive else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "elasticsearch": "error",
            "error": str(e)
        }
