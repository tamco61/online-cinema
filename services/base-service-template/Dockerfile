# Multi-stage Docker build for Cinema microservice

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library first
COPY shared/python-common /build/shared/python-common

# Install shared library
RUN pip install --no-cache-dir -e /build/shared/python-common

# Copy requirements
COPY services/base-service-template/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r cinema && useradd -r -g cinema cinema

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/cinema/.local
COPY --from=builder /build/shared/python-common /app/shared/python-common

# Copy application code
COPY services/base-service-template/app ./app

# Set Python path
ENV PATH=/home/cinema/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER cinema

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
