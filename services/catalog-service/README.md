# Catalog Service

Movie catalog service with Kafka events and Redis caching.

## Features

- ✅ Movie CRUD operations
- ✅ Kafka events (created, updated, published)
- ✅ Redis caching for movie details
- ✅ Public API (published movies only)
- ✅ Admin API (full CRUD)
- ✅ Genres and Persons (actors, directors)
- ✅ Many-to-many relationships

## Database Schema

- **movies** - Main movie table
- **genres** - Genre references
- **persons** - Actors, directors, etc.
- **movie_genres** - Many-to-many
- **movie_persons** - Many-to-many with role

## Kafka Events

### Topics
- `catalog.movie.created` - New movie created
- `catalog.movie.updated` - Movie updated
- `catalog.movie.published` - Movie published

### Event Format
```json
{
  "movie_id": "uuid",
  "action": "created|updated|published",
  "timestamp": "ISO-8601",
  "payload": {
    "title": "Movie Title",
    "year": 2024,
    "rating": 8.5
  }
}
```

## API Endpoints

### Public
- `GET /api/v1/movies` - List published movies
- `GET /api/v1/movies/{id}` - Movie details (cached)

### Admin
- `POST /api/v1/movies` - Create movie + Kafka event
- `PATCH /api/v1/movies/{id}` - Update movie + Kafka event
- `POST /api/v1/movies/{id}/publish` - Publish movie + Kafka event

## Quick Start

```bash
docker-compose up

# API: http://localhost:8003
# Docs: http://localhost:8003/docs
```

## Configuration

- `ENABLE_KAFKA=true` - Enable/disable Kafka
- `ENABLE_CACHE=true` - Enable/disable Redis cache
- `REDIS_CACHE_TTL=600` - Cache TTL (10 min)
