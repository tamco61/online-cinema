# Analytics Service

Backend service for collecting and analyzing viewing events in the online cinema platform.

## Features

### Event Collection
- **HTTP Endpoints**: Manual event ingestion via REST API
- **Kafka Consumer**: Automatic consumption of streaming events from Kafka topics:
  - `stream.start` - User starts watching
  - `stream.progress` - Viewing progress updates
  - `stream.stop` - User stops watching

### Data Storage
- **ClickHouse Database**: High-performance columnar database optimized for analytics
- **Table**: `viewing_events` with columns:
  - `id` - UUID
  - `user_id` - UUID
  - `movie_id` - UUID
  - `event_type` - LowCardinality(String): start, progress, finish
  - `position_seconds` - UInt32
  - `event_time` - DateTime
  - `session_id` - Nullable(UUID)
  - `metadata` - String (JSON)
  - `created_at` - DateTime

### Analytics Endpoints

#### 1. Popular Content
```http
GET /api/v1/analytics/content/popular?days=7&limit=10
```

Returns most popular movies by view count.

**Response:**
```json
{
  "items": [
    {
      "movie_id": "uuid",
      "total_views": 1500,
      "unique_viewers": 800,
      "completion_rate": 75.5
    }
  ],
  "period_days": 7,
  "total_items": 10
}
```

#### 2. User Statistics
```http
GET /api/v1/analytics/user/{user_id}/stats?days=30
```

Returns viewing statistics for a specific user.

**Response:**
```json
{
  "user_id": "uuid",
  "movies_started": 25,
  "movies_finished": 18,
  "unique_movies_watched": 20,
  "total_watch_time_seconds": 108000,
  "completion_rate": 72.0,
  "period_days": 30,
  "most_watched_movie_id": "uuid"
}
```

#### 3. Viewing Trends
```http
GET /api/v1/analytics/trends?days=7
```

Returns daily viewing trends.

#### 4. Peak Hours
```http
GET /api/v1/analytics/peak-hours?days=7
```

Returns hourly distribution of viewing activity.

#### 5. Manual Event Creation (Optional)
```http
POST /api/v1/analytics/events
```

Manually create viewing event via HTTP.

**Body:**
```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "event_type": "start",
  "position_seconds": 0,
  "session_id": "uuid",
  "metadata": {}
}
```

## Architecture

### Components

1. **FastAPI Application** (`app/main.py`)
   - REST API endpoints
   - Lifespan management
   - Health checks

2. **ClickHouse Client** (`app/core/clickhouse_client.py`)
   - Connection management
   - Schema creation
   - Query execution
   - Event insertion

3. **Kafka Consumer** (`app/kafka_consumer/consumer.py`)
   - Consumes events from Kafka topics
   - Processes and transforms events
   - Inserts into ClickHouse

4. **Analytics Service** (`app/services/analytics_service.py`)
   - Business logic for analytics queries
   - Aggregation and calculations

5. **Schemas** (`app/schemas/analytics.py`)
   - Pydantic models for request/response validation

### ClickHouse Optimizations

- **Partitioning**: By month (`PARTITION BY toYYYYMM(event_time)`)
- **Ordering**: By event_time, user_id, movie_id for efficient queries
- **TTL**: Automatic data deletion after 365 days
- **Materialized Views**:
  - `popular_content_mv` - Pre-aggregated movie popularity
  - `user_stats_mv` - Pre-aggregated user statistics
- **Indexes**: Bloom filter indexes on user_id and movie_id

## Setup

### Prerequisites
- Python 3.11+
- ClickHouse server
- Kafka (optional, for event streaming)

### Installation

1. Clone repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize ClickHouse schema:
```bash
clickhouse-client --multiquery < clickhouse/schema.sql
```

### Running Locally

```bash
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload

# Or run directly
python -m app.main
```

### Running with Docker

```bash
# Build image
docker build -t analytics-service .

# Run container
docker run -p 8006:8006 --env-file .env analytics-service
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `CLICKHOUSE_HOST` | ClickHouse server host | localhost |
| `CLICKHOUSE_PORT` | ClickHouse native protocol port | 9000 |
| `CLICKHOUSE_DATABASE` | Database name | analytics |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | localhost:9092 |
| `KAFKA_CONSUMER_GROUP` | Consumer group ID | analytics-service |
| `ENABLE_KAFKA` | Enable Kafka consumer | True |

## ClickHouse Queries

### Example: Popular Movies Last 7 Days
```sql
SELECT
    movie_id,
    sum(start_count) as total_views,
    sum(unique_viewers) as unique_viewers,
    round(sum(finish_count) / sum(start_count) * 100, 2) as completion_rate
FROM popular_content_mv
WHERE event_date >= today() - 7
GROUP BY movie_id
ORDER BY total_views DESC
LIMIT 10;
```

### Example: User Watch Time
```sql
SELECT
    sum(position_seconds) as total_seconds
FROM viewing_events
WHERE user_id = '{user_id}'
  AND event_type = 'finish'
  AND event_time >= now() - INTERVAL 30 DAY;
```

### Example: Peak Hours
```sql
SELECT
    toHour(event_time) as hour,
    count() as events_count,
    uniq(user_id) as unique_users
FROM viewing_events
WHERE event_time >= now() - INTERVAL 7 DAY
GROUP BY hour
ORDER BY events_count DESC;
```

## API Documentation

Once the service is running, visit:
- Swagger UI: http://localhost:8006/docs
- ReDoc: http://localhost:8006/redoc

## Health Check

```bash
curl http://localhost:8006/health
```

## Kafka Event Format

Expected event format from Kafka topics:

```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "action": "stream_start",
  "timestamp": "2024-11-15T10:30:00Z",
  "position_seconds": 0,
  "session_id": "uuid"
}
```

Event mapping:
- `stream.start` / `stream_start` → `start`
- `stream.progress` / `progress_update` → `progress`
- `stream.stop` / `stream_stop` → `finish`

## Development

### Running Tests
```bash
pytest
```

### Code Structure
```
analytics-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── analytics.py      # API endpoints
│   ├── core/
│   │   ├── config.py                 # Configuration
│   │   └── clickhouse_client.py      # ClickHouse client
│   ├── kafka_consumer/
│   │   └── consumer.py               # Kafka consumer
│   ├── schemas/
│   │   └── analytics.py              # Pydantic schemas
│   ├── services/
│   │   └── analytics_service.py      # Business logic
│   └── main.py                       # Application entry point
├── clickhouse/
│   └── schema.sql                    # ClickHouse DDL
├── Dockerfile
├── requirements.txt
└── README.md
```

## Performance Considerations

1. **Materialized Views**: Pre-aggregate data for common queries
2. **Partitioning**: Monthly partitions for efficient data management
3. **TTL**: Automatic cleanup of old data
4. **Indexes**: Bloom filters for fast user/movie lookups
5. **Batch Inserts**: Consider batching for high-volume writes

## Future Enhancements

- [ ] Real-time dashboards
- [ ] Advanced ML-based recommendations
- [ ] Anomaly detection
- [ ] A/B testing analytics
- [ ] CDN performance metrics
- [ ] User engagement scoring

## License

Internal use only.
