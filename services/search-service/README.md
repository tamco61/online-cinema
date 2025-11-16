# Search Service

Full-text search service for online cinema using Elasticsearch.

## Features

- ✅ Full-text search across movies (title, description, actors, directors)
- ✅ Advanced filters (genres, year range, rating, age rating)
- ✅ Autocomplete suggestions by title
- ✅ Kafka consumer for real-time indexing from catalog service
- ✅ Redis caching for popular searches
- ✅ Edge N-gram analyzer for autocomplete
- ✅ Nested fields for genres, actors, directors

## Architecture

```
┌─────────────────┐
│ Catalog Service │
│  (Kafka Events) │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  Kafka Consumer     │
│  ├─ movie.created   │
│  ├─ movie.updated   │
│  └─ movie.published │
└─────────┬───────────┘
          │
          ▼
┌──────────────────────┐
│   Elasticsearch      │
│   movies index       │
└──────────────────────┘
          │
          ▼
┌──────────────────────┐
│   Search API         │
│  ├─ /search          │
│  └─ /search/suggest  │
└──────────────────────┘
```

## Elasticsearch Index

### Mapping

The `movies` index includes:
- **Text fields**: title (with autocomplete), description
- **Keyword fields**: genres, age_rating
- **Numeric fields**: year, rating, duration
- **Nested fields**: genres, actors, directors
- **Completion suggester**: for autocomplete

### Analyzers

- **autocomplete_analyzer**: Edge N-gram (2-20 chars) for prefix matching
- **search_analyzer**: Standard analyzer for search queries

## API Endpoints

### Search Movies

**GET** `/api/v1/search`

Full-text search with filters.

**Query Parameters:**
- `query` (optional): Search query
- `genres` (optional): Comma-separated genre slugs (e.g., `action,drama`)
- `year_from` (optional): Minimum year (1900-2100)
- `year_to` (optional): Maximum year (1900-2100)
- `rating_from` (optional): Minimum rating (0.0-10.0)
- `rating_to` (optional): Maximum rating (0.0-10.0)
- `age_rating` (optional): Comma-separated age ratings (e.g., `PG,PG-13`)
- `page` (default: 1): Page number
- `size` (default: 20, max: 100): Page size
- `published_only` (default: true): Show only published movies

**Example:**
```bash
curl "http://localhost:8004/api/v1/search?query=inception&genres=sci-fi,action&year_from=2010&rating_from=8.0"
```

**Response:**
```json
{
  "results": [
    {
      "movie_id": "uuid",
      "title": "Inception",
      "year": 2010,
      "rating": 8.8,
      "genres": [{"id": "uuid", "name": "Sci-Fi", "slug": "sci-fi"}],
      "actors": [...],
      "directors": [...]
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "total_pages": 1
}
```

### Autocomplete Suggestions

**GET** `/api/v1/search/suggest`

Get title suggestions for autocomplete.

**Query Parameters:**
- `query` (required): Search query (minimum 2 characters)
- `limit` (default: 10, max: 20): Maximum suggestions

**Example:**
```bash
curl "http://localhost:8004/api/v1/search/suggest?query=incep&limit=5"
```

**Response:**
```json
{
  "suggestions": [
    {
      "movie_id": "uuid",
      "title": "Inception",
      "year": 2010,
      "poster_url": "https://..."
    }
  ]
}
```

## Kafka Integration

### Consumed Topics

- `catalog.movie.created` - Index new movie
- `catalog.movie.updated` - Re-index movie
- `catalog.movie.published` - Update publish status

### Event Format

```json
{
  "movie_id": "uuid",
  "action": "created|updated|published",
  "timestamp": "2024-11-15T10:30:00",
  "payload": {
    "title": "Movie Title",
    "year": 2024,
    "rating": 8.5,
    "genres": [...],
    "actors": [...],
    "directors": [...]
  }
}
```

## Redis Caching

- **Key pattern**: `search:query:<hash>`
- **TTL**: 300 seconds (5 minutes)
- **Invalidation**: On movie create/update/publish

## Quick Start

### Using Docker Compose

```bash
cd search-service

# Start all services (Elasticsearch, Redis, Search Service)
docker-compose up

# API: http://localhost:8004
# Docs: http://localhost:8004/docs
# Elasticsearch: http://localhost:9200
```

### Local Development

```bash
# Copy environment file
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start Elasticsearch and Redis
docker-compose up -d elasticsearch redis

# Run service
python -m app.main

# Access at http://localhost:8004
```

## Configuration

Environment variables (`.env`):

```bash
# Elasticsearch
ELASTICSEARCH_HOSTS=["http://localhost:9200"]
ELASTICSEARCH_INDEX=movies

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=catalog
ENABLE_KAFKA=true

# Redis
REDIS_HOST=localhost
REDIS_CACHE_TTL=300
ENABLE_CACHE=true
```

## Example Queries

### Search by title
```bash
curl "http://localhost:8004/api/v1/search?query=matrix"
```

### Filter by genre and year
```bash
curl "http://localhost:8004/api/v1/search?genres=action&year_from=2000&year_to=2010"
```

### Search with rating filter
```bash
curl "http://localhost:8004/api/v1/search?query=nolan&rating_from=8.0"
```

### Autocomplete
```bash
curl "http://localhost:8004/api/v1/search/suggest?query=dark&limit=5"
```

## Health Check

```bash
curl http://localhost:8004/health
```

Returns:
```json
{
  "status": "healthy",
  "elasticsearch": "ok",
  "redis": "ok",
  "kafka": "enabled"
}
```

## Dependencies

- FastAPI 0.104.1
- Elasticsearch 8.11.0
- aiokafka 0.10.0
- redis 5.0.1
- pydantic 2.5.0

## Integration with Catalog Service

1. Start catalog-service (with Kafka)
2. Start search-service
3. When a movie is created/updated in catalog-service, Kafka event is published
4. Search-service consumer receives event and indexes the movie
5. Movie becomes searchable immediately

## Performance

- **Autocomplete**: Edge N-gram for fast prefix matching
- **Caching**: Popular searches cached in Redis
- **Indexing**: Real-time via Kafka consumer
- **Search**: Elasticsearch distributed search

## Notes

- Ensure Kafka is running (from catalog-service or standalone)
- Elasticsearch requires at least 512MB RAM
- For production, use Elasticsearch cluster with replicas
- Adjust cache TTL based on update frequency
