"""
Airflow DAG: Fetch External Metadata

Fetches movie metadata from external APIs (TMDb, IMDB)
and updates the catalog database.

Schedule: Daily at 2 AM
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.http.hooks.http import HttpHook
import logging
import requests

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['data@cinema.example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

# DAG definition
dag = DAG(
    'fetch_external_metadata',
    default_args=default_args,
    description='Fetch movie metadata from TMDb and IMDB',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    tags=['etl', 'metadata', 'tmdb', 'imdb'],
)


def get_movies_needing_metadata(**context):
    """
    Get list of movies that need metadata updates

    Returns:
        List of movie IDs that need metadata
    """
    logger.info("Getting movies needing metadata...")

    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')

    # Get movies without complete metadata or old metadata
    query = """
    SELECT id, title, tmdb_id, imdb_id
    FROM movies
    WHERE
        (tmdb_id IS NULL OR imdb_id IS NULL)
        OR metadata_updated_at IS NULL
        OR metadata_updated_at < NOW() - INTERVAL '30 days'
    LIMIT 100
    """

    records = pg_hook.get_records(query)

    movies = [
        {
            'id': str(record[0]),
            'title': record[1],
            'tmdb_id': record[2],
            'imdb_id': record[3]
        }
        for record in records
    ]

    logger.info(f"Found {len(movies)} movies needing metadata")

    # Push to XCom
    context['task_instance'].xcom_push(key='movies', value=movies)

    return len(movies)


def fetch_tmdb_metadata(**context):
    """
    Fetch metadata from The Movie Database (TMDb) API

    TMDb API: https://developers.themoviedb.org/3
    """
    logger.info("Fetching metadata from TMDb...")

    # Get movies from XCom
    movies = context['task_instance'].xcom_pull(
        task_ids='get_movies_needing_metadata',
        key='movies'
    )

    if not movies:
        logger.info("No movies to fetch metadata for")
        return 0

    # TMDb API configuration
    # In production, use Airflow Variable or Connection
    tmdb_api_key = "YOUR_TMDB_API_KEY"  # Replace with actual key
    base_url = "https://api.themoviedb.org/3"

    updated_count = 0
    metadata_list = []

    for movie in movies:
        try:
            # Search for movie by title
            search_url = f"{base_url}/search/movie"
            params = {
                'api_key': tmdb_api_key,
                'query': movie['title'],
                'language': 'ru-RU'
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            results = response.json().get('results', [])

            if results:
                # Get detailed info for first result
                tmdb_id = results[0]['id']
                detail_url = f"{base_url}/movie/{tmdb_id}"
                detail_params = {
                    'api_key': tmdb_api_key,
                    'language': 'ru-RU',
                    'append_to_response': 'credits,videos'
                }

                detail_response = requests.get(detail_url, params=detail_params, timeout=10)
                detail_response.raise_for_status()

                detail = detail_response.json()

                # Extract metadata
                metadata = {
                    'movie_id': movie['id'],
                    'tmdb_id': tmdb_id,
                    'imdb_id': detail.get('imdb_id'),
                    'original_title': detail.get('original_title'),
                    'description': detail.get('overview'),
                    'release_date': detail.get('release_date'),
                    'runtime': detail.get('runtime'),
                    'rating': detail.get('vote_average'),
                    'genres': [g['name'] for g in detail.get('genres', [])],
                    'poster_path': detail.get('poster_path'),
                    'backdrop_path': detail.get('backdrop_path'),
                    'actors': [
                        c['name'] for c in detail.get('credits', {}).get('cast', [])[:10]
                    ],
                    'directors': [
                        c['name'] for c in detail.get('credits', {}).get('crew', [])
                        if c['job'] == 'Director'
                    ]
                }

                metadata_list.append(metadata)
                updated_count += 1

                logger.info(f"✅ Fetched metadata for: {movie['title']}")

        except Exception as e:
            logger.error(f"❌ Error fetching metadata for {movie['title']}: {e}")
            continue

    logger.info(f"Fetched metadata for {updated_count} movies")

    # Push to XCom
    context['task_instance'].xcom_push(key='metadata', value=metadata_list)

    return updated_count


def update_database_with_metadata(**context):
    """
    Update PostgreSQL database with fetched metadata
    """
    logger.info("Updating database with metadata...")

    # Get metadata from XCom
    metadata_list = context['task_instance'].xcom_pull(
        task_ids='fetch_tmdb_metadata',
        key='metadata'
    )

    if not metadata_list:
        logger.info("No metadata to update")
        return 0

    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')

    updated_count = 0

    for metadata in metadata_list:
        try:
            # Update movie record
            update_query = """
            UPDATE movies
            SET
                tmdb_id = %(tmdb_id)s,
                imdb_id = %(imdb_id)s,
                original_title = %(original_title)s,
                description = COALESCE(%(description)s, description),
                release_date = COALESCE(%(release_date)s, release_date),
                duration = COALESCE(%(runtime)s, duration),
                rating = COALESCE(%(rating)s, rating),
                poster_url = CASE
                    WHEN %(poster_path)s IS NOT NULL
                    THEN 'https://image.tmdb.org/t/p/w500' || %(poster_path)s
                    ELSE poster_url
                END,
                metadata_updated_at = NOW()
            WHERE id = %(movie_id)s
            """

            pg_hook.run(update_query, parameters=metadata)

            # TODO: Update genres, actors, directors in separate tables

            updated_count += 1

        except Exception as e:
            logger.error(f"Error updating movie {metadata['movie_id']}: {e}")
            continue

    logger.info(f"✅ Updated {updated_count} movies in database")

    return updated_count


# Define tasks
get_movies_task = PythonOperator(
    task_id='get_movies_needing_metadata',
    python_callable=get_movies_needing_metadata,
    dag=dag,
)

fetch_metadata_task = PythonOperator(
    task_id='fetch_tmdb_metadata',
    python_callable=fetch_tmdb_metadata,
    dag=dag,
)

update_db_task = PythonOperator(
    task_id='update_database_with_metadata',
    python_callable=update_database_with_metadata,
    dag=dag,
)

# Define task dependencies
get_movies_task >> fetch_metadata_task >> update_db_task
