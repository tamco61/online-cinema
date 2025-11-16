# Cinema Service Template

Base template for Cinema microservices. Use this template to create new services.

## Features

- ✅ FastAPI with async support
- ✅ SQLAlchemy 2.0 with async PostgreSQL
- ✅ Pydantic v2 for validation and settings
- ✅ Cinema-common library integration (logging, metrics, tracing)
- ✅ Health check endpoints (/health, /ready)
- ✅ Repository pattern for database access
- ✅ Service layer for business logic
- ✅ JWT authentication ready
- ✅ Docker and Docker Compose support
- ✅ Pytest with async support
- ✅ Code quality tools (black, ruff, mypy)

## Project Structure

```
base-service-template/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── health.py      # Health check endpoints
│   │   │   │   └── __init__.py
│   │   │   ├── router.py          # Main v1 router
│   │   │   └── __init__.py
│   │   └── deps.py                # FastAPI dependencies
│   ├── core/
│   │   ├── config.py              # Pydantic Settings
│   │   ├── security.py            # JWT and password utilities
│   │   ├── middleware.py          # Middleware setup
│   │   └── __init__.py
│   ├── db/
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── repositories.py        # Repository pattern
│   │   ├── session.py             # Database session
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── common.py              # Pydantic schemas
│   │   └── __init__.py
│   ├── services/
│   │   ├── base_service.py        # Business logic layer
│   │   └── __init__.py
│   ├── utils/
│   │   └── __init__.py
│   └── main.py                    # FastAPI application
├── tests/
│   ├── conftest.py                # Pytest fixtures
│   ├── test_health.py             # Health endpoint tests
│   └── __init__.py
├── .dockerignore
├── .env.example                   # Environment variables template
├── .gitignore
├── Dockerfile                     # Production Docker image
├── pyproject.toml                 # Project config
├── README.md                      # This file
└── requirements.txt               # Python dependencies
```

## Quick Start

### 1. Copy Template

```bash
# Copy template to create a new service
cp -r services/base-service-template services/my-service
cd services/my-service

# Update service name in files:
# - app/core/config.py (SERVICE_NAME)
# - pyproject.toml (name)
# - README.md
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
vim .env
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install cinema-common library (if not already installed)
pip install -e ../../shared/python-common
```

### 4. Run Locally

```bash
# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Or use Python directly
python -m app.main
```

### 5. Access API

- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Readiness: http://localhost:8000/api/v1/ready
- Metrics: http://localhost:8000/metrics (if cinema-common is installed)

## Development

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py -v
```

### Code Quality

```bash
# Format code
black .
ruff check --fix .

# Type checking
mypy app
```

### Database Migrations

```bash
# Initialize Alembic (first time)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Docker

### Build Image

```bash
# From repository root
docker build -f services/base-service-template/Dockerfile -t cinema-service:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e POSTGRES_HOST=postgres \
  -e REDIS_HOST=redis \
  cinema-service:latest
```

### Docker Compose

```yaml
# Add to docker-compose.yml
services:
  my-service:
    build:
      context: .
      dockerfile: services/my-service/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SERVICE_NAME=my-service
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
```

## Adding New Endpoints

### 1. Create Pydantic Schemas

```python
# app/schemas/movies.py
from app.schemas.common import BaseSchema, IDMixin, TimestampMixin

class MovieBase(BaseSchema):
    title: str
    year: int

class MovieCreate(MovieBase):
    pass

class MovieResponse(MovieBase, IDMixin, TimestampMixin):
    pass
```

### 2. Create Database Model

```python
# app/db/models.py
from app.db.session import Base

class Movie(BaseModel):
    __tablename__ = "movies"

    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[int] = mapped_column(Integer)
```

### 3. Create Service

```python
# app/services/movie_service.py
from app.services.base_service import BaseService

class MovieService(BaseService[Movie, MovieCreate, MovieUpdate]):
    pass
```

### 4. Create Endpoint

```python
# app/api/v1/endpoints/movies.py
from fastapi import APIRouter, Depends
from app.api.deps import DatabaseSession

router = APIRouter()

@router.get("/movies")
async def list_movies(db: AsyncSession = DatabaseSession):
    service = MovieService(db, Movie)
    movies = await service.get_all()
    return movies
```

### 5. Register Router

```python
# app/api/v1/router.py
from .endpoints import movies

router.include_router(
    movies.router,
    prefix="/movies",
    tags=["Movies"],
)
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key settings:

- `SERVICE_NAME` - Service identifier
- `ENVIRONMENT` - development/staging/production
- `LOG_LEVEL` - DEBUG/INFO/WARNING/ERROR
- `POSTGRES_*` - Database connection
- `REDIS_*` - Redis connection
- `JAEGER_*` - Distributed tracing
- `JWT_SECRET_KEY` - Authentication secret

### Cinema-Common Integration

The template automatically integrates with `cinema-common` library:

- **Logging**: Structured JSON logging with correlation IDs
- **Metrics**: Prometheus metrics at `/metrics`
- **Tracing**: OpenTelemetry + Jaeger integration
- **Error Handling**: Unified error responses
- **Middleware**: CORS, correlation ID, rate limiting

Disable in `.env`:
```
ENABLE_METRICS=false
ENABLE_TRACING=false
```

## Production Deployment

### Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: my-service
        image: cinema-service:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
```

### Best Practices

1. **Always use migrations** - Don't rely on `init_db()` in production
2. **Set strong JWT secret** - Generate with `openssl rand -hex 32`
3. **Enable JSON logs** - Set `JSON_LOGS=true` for production
4. **Configure CORS properly** - Don't use `["*"]` in production
5. **Use connection pooling** - Configure in `db/session.py`
6. **Set up monitoring** - Use Prometheus, Grafana, Jaeger
7. **Run as non-root** - Dockerfile already configured

## Troubleshooting

### Database connection fails

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U cinema -d cinema
```

### Import errors

```bash
# Reinstall cinema-common
pip install -e ../../shared/python-common --force-reinstall
```

### Tests fail

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run with verbose output
pytest -vv
```

## License

MIT

## Support

- Documentation: `/docs` endpoint
- Issues: GitHub Issues
- Email: devops@cinema.example.com
