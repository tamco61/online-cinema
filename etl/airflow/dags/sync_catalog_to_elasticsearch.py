"""
Airflow DAG: Sync Catalog to Elasticsearch

Periodically syncs movie catalog from PostgreSQL to Elasticsearch
for fast full-text search and filtering.

Schedule: Every hour
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.elasticsearch.hooks.elasticsearch import ElasticsearchHook
import logging

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['data@cinema.example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'sync_catalog_to_elasticsearch',
    default_args=default_args,
    description='Sync catalog from PostgreSQL to Elasticsearch',
    schedule_interval='0 * * * *',  # Every hour
    catchup=False,
    tags=['etl', 'elasticsearch', 'catalog'],
)


def extract_movies_from_postgres(**context):
    """
    Extract movies from PostgreSQL catalog database

    Returns:
        List of movie dictionaries
    """
    logger.info("Extracting movies from PostgreSQL...")

    # Get PostgreSQL connection
    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')

    # Query to fetch movies with all related data
    query = """
    SELECT
        m.id,
        m.title,
        m.original_title,
        m.description,
        m.release_date,
        m.duration,
        m.rating,
        m.imdb_id,
        m.tmdb_id,
        ARRAY_AGG(DISTINCT g.name) as genres,
        ARRAY_AGG(DISTINCT a.name) as actors,
        ARRAY_AGG(DISTINCT d.name) as directors,
        m.poster_url,
        m.trailer_url,
        m.video_url,
        m.created_at,
        m.updated_at
    FROM movies m
    LEFT JOIN movie_genres mg ON m.id = mg.movie_id
    LEFT JOIN genres g ON mg.genre_id = g.id
    LEFT JOIN movie_actors ma ON m.id = ma.movie_id
    LEFT JOIN actors a ON ma.actor_id = a.id
    LEFT JOIN movie_directors md ON m.id = md.movie_id
    LEFT JOIN directors d ON md.director_id = d.id
    WHERE m.status = 'published'
    GROUP BY m.id
    ORDER BY m.updated_at DESC
    """

    # Execute query
    records = pg_hook.get_records(query)

    # Transform to dictionaries
    movies = []
    for record in records:
        movie = {
            'id': str(record[0]),
            'title': record[1],
            'original_title': record[2],
            'description': record[3],
            'release_date': record[4].isoformat() if record[4] else None,
            'duration': record[5],
            'rating': float(record[6]) if record[6] else None,
            'imdb_id': record[7],
            'tmdb_id': record[8],
            'genres': [g for g in record[9] if g] if record[9] else [],
            'actors': [a for a in record[10] if a] if record[10] else [],
            'directors': [d for d in record[11] if d] if record[11] else [],
            'poster_url': record[12],
            'trailer_url': record[13],
            'video_url': record[14],
            'created_at': record[15].isoformat() if record[15] else None,
            'updated_at': record[16].isoformat() if record[16] else None,
        }
        movies.append(movie)

    logger.info(f"Extracted {len(movies)} movies from PostgreSQL")

    # Push to XCom for next task
    context['task_instance'].xcom_push(key='movies', value=movies)

    return len(movies)


def load_movies_to_elasticsearch(**context):
    """
    Load movies to Elasticsearch index

    Creates or updates Elasticsearch index with movie data
    """
    logger.info("Loading movies to Elasticsearch...")

    # Get movies from XCom
    movies = context['task_instance'].xcom_pull(
        task_ids='extract_movies',
        key='movies'
    )

    if not movies:
        logger.warning("No movies to index")
        return 0

    # Get Elasticsearch connection
    es_hook = ElasticsearchHook(elasticsearch_conn_id='elasticsearch_default')
    es_client = es_hook.get_conn

    index_name = 'movies'

    # Create index if not exists
    if not es_client.indices.exists(index=index_name):
        logger.info(f"Creating Elasticsearch index: {index_name}")

        # Index mapping
        mapping = {
            'mappings': {
                'properties': {
                    'title': {'type': 'text', 'analyzer': 'standard'},
                    'original_title': {'type': 'text', 'analyzer': 'standard'},
                    'description': {'type': 'text', 'analyzer': 'standard'},
                    'release_date': {'type': 'date'},
                    'duration': {'type': 'integer'},
                    'rating': {'type': 'float'},
                    'imdb_id': {'type': 'keyword'},
                    'tmdb_id': {'type': 'keyword'},
                    'genres': {'type': 'keyword'},
                    'actors': {'type': 'keyword'},
                    'directors': {'type': 'keyword'},
                    'poster_url': {'type': 'keyword'},
                    'trailer_url': {'type': 'keyword'},
                    'video_url': {'type': 'keyword'},
                    'created_at': {'type': 'date'},
                    'updated_at': {'type': 'date'},
                }
            }
        }

        es_client.indices.create(index=index_name, body=mapping)

    # Bulk index movies
    from elasticsearch.helpers import bulk

    actions = []
    for movie in movies:
        action = {
            '_index': index_name,
            '_id': movie['id'],
            '_source': movie
        }
        actions.append(action)

    # Bulk insert
    success, failed = bulk(es_client, actions, raise_on_error=False)

    logger.info(f"Indexed {success} movies to Elasticsearch")
    if failed:
        logger.warning(f"Failed to index {len(failed)} movies")

    return success


def verify_sync(**context):
    """
    Verify that sync was successful

    Compares counts between PostgreSQL and Elasticsearch
    """
    logger.info("Verifying sync...")

    # Get counts from both sources
    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')
    pg_count = pg_hook.get_first("SELECT COUNT(*) FROM movies WHERE status = 'published'")[0]

    es_hook = ElasticsearchHook(elasticsearch_conn_id='elasticsearch_default')
    es_client = es_hook.get_conn
    es_count = es_client.count(index='movies')['count']

    logger.info(f"PostgreSQL count: {pg_count}")
    logger.info(f"Elasticsearch count: {es_count}")

    if pg_count == es_count:
        logger.info("✅ Sync verified successfully")
    else:
        logger.warning(f"⚠️ Count mismatch: PG={pg_count}, ES={es_count}")

    return {'pg_count': pg_count, 'es_count': es_count}


# Define tasks
extract_task = PythonOperator(
    task_id='extract_movies',
    python_callable=extract_movies_from_postgres,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_elasticsearch',
    python_callable=load_movies_to_elasticsearch,
    dag=dag,
)

verify_task = PythonOperator(
    task_id='verify_sync',
    python_callable=verify_sync,
    dag=dag,
)

# Define task dependencies
extract_task >> load_task >> verify_task
