from elasticsearch import AsyncElasticsearch
from app.core.config import settings
from app.core.cache import RedisCache
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    MovieSearchResult,
    SuggestRequest,
    SuggestResponse,
    SuggestionItem
)
import logging
import math

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, es_client: AsyncElasticsearch, cache: RedisCache):
        self.es = es_client
        self.cache = cache

    async def search_movies(self, search_request: SearchRequest) -> SearchResponse:
        """
        Full-text search for movies with filters
        """
        # Generate cache key
        filters = {
            "genres": search_request.genres,
            "year_from": search_request.year_from,
            "year_to": search_request.year_to,
            "rating_from": search_request.rating_from,
            "rating_to": search_request.rating_to,
            "age_rating": search_request.age_rating,
            "published_only": search_request.published_only,
            "page": search_request.page,
            "size": search_request.size
        }
        query_hash = self.cache.generate_query_hash(
            search_request.query or "",
            filters
        )

        # Check cache
        cached_result = await self.cache.get_search_results(query_hash)
        if cached_result:
            return SearchResponse(**cached_result)

        # Build Elasticsearch query
        es_query = self._build_search_query(search_request)

        # Calculate pagination
        from_index = (search_request.page - 1) * search_request.size

        try:
            # Execute search
            response = await self.es.search(
                index=settings.ELASTICSEARCH_INDEX,
                body=es_query,
                from_=from_index,
                size=search_request.size
            )

            # Parse results
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]

            results = [
                self._parse_movie_hit(hit)
                for hit in hits
            ]

            total_pages = math.ceil(total / search_request.size)

            search_response = SearchResponse(
                results=results,
                total=total,
                page=search_request.page,
                size=search_request.size,
                total_pages=total_pages
            )

            # Cache the result
            await self.cache.set_search_results(
                query_hash,
                search_response.model_dump()
            )

            return search_response

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def _build_search_query(self, req: SearchRequest) -> dict:
        """Build Elasticsearch query with filters"""
        must_clauses = []
        filter_clauses = []

        # Published filter
        if req.published_only:
            filter_clauses.append({"term": {"is_published": True}})

        # Full-text search
        if req.query:
            must_clauses.append({
                "multi_match": {
                    "query": req.query,
                    "fields": [
                        "title^3",  # Boost title
                        "original_title^2",
                        "description",
                        "actors.full_name^2",
                        "directors.full_name^2"
                    ],
                    "type": "best_fields",
                    "operator": "or",
                    "fuzziness": "AUTO"
                }
            })

        # Genre filter
        if req.genres:
            filter_clauses.append({
                "nested": {
                    "path": "genres",
                    "query": {
                        "terms": {"genres.slug": req.genres}
                    }
                }
            })

        # Year range filter
        if req.year_from or req.year_to:
            year_range = {}
            if req.year_from:
                year_range["gte"] = req.year_from
            if req.year_to:
                year_range["lte"] = req.year_to
            filter_clauses.append({"range": {"year": year_range}})

        # Rating range filter
        if req.rating_from or req.rating_to:
            rating_range = {}
            if req.rating_from:
                rating_range["gte"] = req.rating_from
            if req.rating_to:
                rating_range["lte"] = req.rating_to
            filter_clauses.append({"range": {"rating": rating_range}})

        # Age rating filter
        if req.age_rating:
            filter_clauses.append({"terms": {"age_rating": req.age_rating}})

        # Build final query
        if not must_clauses:
            # No search query - match all
            query = {
                "query": {
                    "bool": {
                        "filter": filter_clauses
                    }
                },
                "sort": [
                    {"rating": {"order": "desc"}},
                    {"year": {"order": "desc"}}
                ]
            }
        else:
            # With search query
            query = {
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "filter": filter_clauses
                    }
                }
            }

        return query

    async def autocomplete(self, suggest_request: SuggestRequest) -> SuggestResponse:
        """
        Autocomplete suggestions by movie title
        """
        try:
            # Use match query with edge_ngram analyzer
            response = await self.es.search(
                index=settings.ELASTICSEARCH_INDEX,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "title": {
                                            "query": suggest_request.query,
                                            "operator": "and"
                                        }
                                    }
                                }
                            ],
                            "filter": [
                                {"term": {"is_published": True}}
                            ]
                        }
                    },
                    "sort": [
                        "_score",
                        {"rating": {"order": "desc"}}
                    ],
                    "_source": ["movie_id", "title", "year", "poster_url"]
                },
                size=suggest_request.limit
            )

            hits = response["hits"]["hits"]

            suggestions = [
                SuggestionItem(
                    movie_id=hit["_source"]["movie_id"],
                    title=hit["_source"]["title"],
                    year=hit["_source"]["year"],
                    poster_url=hit["_source"].get("poster_url")
                )
                for hit in hits
            ]

            return SuggestResponse(suggestions=suggestions)

        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            raise

    def _parse_movie_hit(self, hit: dict) -> MovieSearchResult:
        """Parse Elasticsearch hit to MovieSearchResult"""
        source = hit["_source"]

        return MovieSearchResult(
            movie_id=source["movie_id"],
            title=source["title"],
            original_title=source.get("original_title"),
            description=source.get("description"),
            year=source["year"],
            duration=source.get("duration"),
            rating=source.get("rating"),
            age_rating=source.get("age_rating"),
            poster_url=source.get("poster_url"),
            trailer_url=source.get("trailer_url"),
            genres=source.get("genres", []),
            actors=source.get("actors", []),
            directors=source.get("directors", []),
            is_published=source.get("is_published", False),
            published_at=source.get("published_at")
        )

    async def index_movie(self, movie_data: dict):
        """
        Index or update a movie document
        """
        try:
            movie_id = movie_data["movie_id"]

            await self.es.index(
                index=settings.ELASTICSEARCH_INDEX,
                id=movie_id,
                document=movie_data
            )

            logger.info(f"✅ Indexed movie: {movie_id}")

            # Invalidate search cache
            await self.cache.invalidate_movie(movie_id)

        except Exception as e:
            logger.error(f"❌ Indexing error for movie {movie_data.get('movie_id')}: {e}")
            raise

    async def update_movie_publish_status(self, movie_id: str, is_published: bool, published_at: str = None):
        """
        Update movie publish status
        """
        try:
            update_body = {
                "doc": {
                    "is_published": is_published,
                    "published_at": published_at
                }
            }

            await self.es.update(
                index=settings.ELASTICSEARCH_INDEX,
                id=movie_id,
                body=update_body
            )

            logger.info(f"✅ Updated publish status for movie: {movie_id}")

            # Invalidate search cache
            await self.cache.invalidate_movie(movie_id)

        except Exception as e:
            logger.error(f"❌ Update error for movie {movie_id}: {e}")
            raise

    async def delete_movie(self, movie_id: str):
        """
        Delete a movie from index
        """
        try:
            await self.es.delete(
                index=settings.ELASTICSEARCH_INDEX,
                id=movie_id
            )

            logger.info(f"🗑️  Deleted movie: {movie_id}")

            # Invalidate search cache
            await self.cache.invalidate_movie(movie_id)

        except Exception as e:
            logger.error(f"❌ Delete error for movie {movie_id}: {e}")
