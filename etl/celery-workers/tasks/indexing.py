"""
Celery Task: Elasticsearch Indexing

Indexes movies to Elasticsearch for fast search and filtering.
Alternative to Airflow DAG for event-driven indexing.
"""

import logging
from elasticsearch import Elasticsearch
from typing import Dict, List

logger = logging.getLogger(__name__)


def index_movie_to_elasticsearch(
    movie_id: str,
    action: str = 'index'
) -> dict:
    """
    Index single movie to Elasticsearch

    Args:
        movie_id: Movie UUID
        action: Action type (index, update, delete)

    Returns:
        Dictionary with indexing result

    Process:
        1. Fetch movie data from PostgreSQL
        2. Transform to Elasticsearch document
        3. Index/update/delete in Elasticsearch
        4. Return result
    """
    logger.info(f"Indexing movie {movie_id} to Elasticsearch (action: {action})")

    try:
        # Step 1: Fetch movie data from PostgreSQL
        movie_data = _fetch_movie_from_database(movie_id)

        if not movie_data:
            logger.error(f"Movie {movie_id} not found in database")
            return {
                'movie_id': movie_id,
                'status': 'failed',
                'error': 'Movie not found'
            }

        # Step 2: Connect to Elasticsearch
        es_client = Elasticsearch(
            hosts=['http://localhost:9200'],
            # Add authentication if needed
        )

        index_name = 'movies'

        # Step 3: Perform action
        if action == 'index' or action == 'update':
            # Transform movie data for Elasticsearch
            es_document = _transform_movie_for_elasticsearch(movie_data)

            # Index document
            response = es_client.index(
                index=index_name,
                id=movie_id,
                document=es_document
            )

            logger.info(f"✅ Indexed movie {movie_id}: {response['result']}")

            return {
                'movie_id': movie_id,
                'status': 'success',
                'action': action,
                'result': response['result']
            }

        elif action == 'delete':
            # Delete document
            response = es_client.delete(
                index=index_name,
                id=movie_id
            )

            logger.info(f"✅ Deleted movie {movie_id} from index")

            return {
                'movie_id': movie_id,
                'status': 'success',
                'action': action,
                'result': 'deleted'
            }

        else:
            logger.error(f"Unknown action: {action}")
            return {
                'movie_id': movie_id,
                'status': 'failed',
                'error': f'Unknown action: {action}'
            }

    except Exception as e:
        logger.error(f"❌ Indexing failed for movie {movie_id}: {e}")

        return {
            'movie_id': movie_id,
            'status': 'failed',
            'error': str(e)
        }


def bulk_index_movies(movie_ids: List[str]) -> dict:
    """
    Bulk index multiple movies to Elasticsearch

    Args:
        movie_ids: List of movie UUIDs

    Returns:
        Dictionary with bulk indexing results
    """
    logger.info(f"Bulk indexing {len(movie_ids)} movies to Elasticsearch")

    try:
        # Fetch all movies
        movies_data = _fetch_movies_from_database(movie_ids)

        if not movies_data:
            logger.warning("No movies found to index")
            return {
                'status': 'success',
                'indexed': 0,
                'failed': 0
            }

        # Connect to Elasticsearch
        es_client = Elasticsearch(
            hosts=['http://localhost:9200'],
        )

        index_name = 'movies'

        # Prepare bulk actions
        from elasticsearch.helpers import bulk

        actions = []
        for movie in movies_data:
            es_document = _transform_movie_for_elasticsearch(movie)

            action = {
                '_index': index_name,
                '_id': movie['id'],
                '_source': es_document
            }
            actions.append(action)

        # Bulk index
        success, failed = bulk(es_client, actions, raise_on_error=False)

        logger.info(f"✅ Bulk indexed {success} movies")

        if failed:
            logger.warning(f"Failed to index {len(failed)} movies")

        return {
            'status': 'success',
            'indexed': success,
            'failed': len(failed) if failed else 0
        }

    except Exception as e:
        logger.error(f"❌ Bulk indexing failed: {e}")

        return {
            'status': 'failed',
            'error': str(e)
        }


def reindex_all_movies() -> dict:
    """
    Reindex all published movies to Elasticsearch

    Returns:
        Dictionary with reindexing results
    """
    logger.info("Reindexing all movies to Elasticsearch")

    try:
        # Get all published movie IDs
        movie_ids = _get_all_published_movie_ids()

        logger.info(f"Found {len(movie_ids)} movies to reindex")

        # Bulk index in batches
        batch_size = 100
        total_indexed = 0
        total_failed = 0

        for i in range(0, len(movie_ids), batch_size):
            batch = movie_ids[i:i + batch_size]

            result = bulk_index_movies(batch)

            total_indexed += result.get('indexed', 0)
            total_failed += result.get('failed', 0)

            logger.info(f"Progress: {i + len(batch)}/{len(movie_ids)} movies processed")

        logger.info(f"✅ Reindexing completed: {total_indexed} indexed, {total_failed} failed")

        return {
            'status': 'success',
            'total_movies': len(movie_ids),
            'indexed': total_indexed,
            'failed': total_failed
        }

    except Exception as e:
        logger.error(f"❌ Reindexing failed: {e}")

        return {
            'status': 'failed',
            'error': str(e)
        }


def _fetch_movie_from_database(movie_id: str) -> Dict:
    """
    Fetch movie data from PostgreSQL

    In production, use actual database connection
    """
    # Pseudo-code
    # import psycopg2
    # conn = psycopg2.connect(DATABASE_URL)
    # cursor = conn.cursor()
    # cursor.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
    # movie = cursor.fetchone()
    # return transform_to_dict(movie)

    # Mock data for example
    return {
        'id': movie_id,
        'title': 'Example Movie',
        'description': 'Description',
        'genres': ['Action', 'Sci-Fi'],
        'actors': ['Actor 1', 'Actor 2'],
        'directors': ['Director 1'],
        'rating': 8.5,
        'release_date': '2024-01-01'
    }


def _fetch_movies_from_database(movie_ids: List[str]) -> List[Dict]:
    """
    Fetch multiple movies from PostgreSQL

    In production, use actual database connection
    """
    # Pseudo-code
    # import psycopg2
    # conn = psycopg2.connect(DATABASE_URL)
    # cursor = conn.cursor()
    # cursor.execute("SELECT * FROM movies WHERE id = ANY(%s)", (movie_ids,))
    # movies = cursor.fetchall()
    # return [transform_to_dict(m) for m in movies]

    return [_fetch_movie_from_database(mid) for mid in movie_ids]


def _get_all_published_movie_ids() -> List[str]:
    """
    Get all published movie IDs from PostgreSQL

    In production, use actual database connection
    """
    # Pseudo-code
    # import psycopg2
    # conn = psycopg2.connect(DATABASE_URL)
    # cursor = conn.cursor()
    # cursor.execute("SELECT id FROM movies WHERE status = 'published'")
    # return [row[0] for row in cursor.fetchall()]

    return []


def _transform_movie_for_elasticsearch(movie: Dict) -> Dict:
    """
    Transform movie data to Elasticsearch document format

    Args:
        movie: Movie dictionary from database

    Returns:
        Elasticsearch document
    """
    return {
        'title': movie.get('title'),
        'original_title': movie.get('original_title'),
        'description': movie.get('description'),
        'release_date': movie.get('release_date'),
        'duration': movie.get('duration'),
        'rating': movie.get('rating'),
        'imdb_id': movie.get('imdb_id'),
        'tmdb_id': movie.get('tmdb_id'),
        'genres': movie.get('genres', []),
        'actors': movie.get('actors', []),
        'directors': movie.get('directors', []),
        'poster_url': movie.get('poster_url'),
        'trailer_url': movie.get('trailer_url'),
        'video_url': movie.get('video_url'),
        'created_at': movie.get('created_at'),
        'updated_at': movie.get('updated_at'),
    }
