"""
Celery Worker Entry Point

Initializes and runs Celery worker for ETL tasks.

Usage:
    celery -A worker worker --loglevel=info --queue=transcoding
    celery -A worker worker --loglevel=info --queue=thumbnails
    celery -A worker worker --loglevel=info --queue=indexing
"""

import os
import logging
from celery import Celery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Celery app
app = Celery('etl_tasks')

# Load configuration from celeryconfig
app.config_from_object('celeryconfig')

# Auto-discover tasks
app.autodiscover_tasks(['tasks'])

logger.info("Celery worker initialized")
logger.info(f"Broker: {app.conf.broker_url}")
logger.info(f"Backend: {app.conf.result_backend}")


if __name__ == '__main__':
    app.start()
