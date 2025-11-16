# ETL Service Dockerfile
# Unified image for Airflow and Celery workers

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AIRFLOW_HOME=/app/airflow \
    AIRFLOW__CORE__DAGS_FOLDER=/app/airflow/dags \
    AIRFLOW__CORE__PLUGINS_FOLDER=/app/airflow/plugins \
    AIRFLOW__CORE__EXECUTOR=CeleryExecutor \
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow \
    AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0 \
    AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres:5432/airflow

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY airflow/ /app/airflow/
COPY celery-workers/ /app/celery-workers/

# Create necessary directories
RUN mkdir -p /app/airflow/logs /app/airflow/plugins /tmp/videos /tmp/thumbnails

# Set PYTHONPATH for imports
ENV PYTHONPATH=/app/celery-workers:$PYTHONPATH

# Expose ports
# 8080 - Airflow webserver
# 5555 - Flower (Celery monitoring)
EXPOSE 8080 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["airflow", "webserver"]
