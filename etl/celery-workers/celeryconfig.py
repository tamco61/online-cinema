"""
Celery Configuration

Configures Celery app for ETL video processing tasks.
"""

import os
from kombu import Queue

# Celery App Configuration
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Task serialization
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/Moscow'
enable_utc = True

# Task routing
task_routes = {
    'tasks.transcoding.*': {'queue': 'transcoding'},
    'tasks.thumbnails.*': {'queue': 'thumbnails'},
    'tasks.indexing.*': {'queue': 'indexing'},
}

# Define queues
task_queues = (
    Queue('transcoding', routing_key='transcoding'),
    Queue('thumbnails', routing_key='thumbnails'),
    Queue('indexing', routing_key='indexing'),
    Queue('default', routing_key='default'),
)

# Task execution
task_acks_late = True
worker_prefetch_multiplier = 1  # One task at a time (important for heavy video processing)
task_time_limit = 3600  # 1 hour
task_soft_time_limit = 3300  # 55 minutes

# Result backend settings
result_expires = 86400  # 24 hours

# Worker settings
worker_max_tasks_per_child = 10  # Restart worker after 10 tasks (prevent memory leaks)
worker_disable_rate_limits = True

# Logging
worker_hijack_root_logger = False
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Task discovery
imports = (
    'tasks.transcoding',
    'tasks.thumbnails',
    'tasks.indexing',
)

# Beat schedule (if using Celery Beat instead of Airflow)
#beat_schedule = {
#     'reindex-all-movies': {
#         'task': 'tasks.indexing.reindex_all_movies',
#         'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
#     },
# }
