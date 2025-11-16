# Analytics Service - Quick Start Guide

## 1. Start the Service (with Docker Compose)

```bash
cd services/analytics-service
make docker-up
```

This will start:
- Analytics Service (port 8006)
- ClickHouse (ports 9000, 8123)
- Kafka (port 9092)
- Zookeeper (port 2181)

Wait ~10 seconds for all services to be ready.

## 2. Verify Service is Running

```bash
curl http://localhost:8006/health
```

Expected response:
```json
{
  "status": "healthy",
  "clickhouse": "healthy",
  "kafka": "enabled"
}
```

## 3. Generate Test Data

```bash
python test_events.py
```

Choose option `4` to generate data and test analytics.

## 4. Test API Endpoints

### Popular Content
```bash
curl "http://localhost:8006/api/v1/analytics/content/popular?days=7&limit=10"
```

### User Statistics
```bash
# Replace {user_id} with actual UUID from test data
curl "http://localhost:8006/api/v1/analytics/user/{user_id}/stats?days=30"
```

### Viewing Trends
```bash
curl "http://localhost:8006/api/v1/analytics/trends?days=7"
```

### Peak Hours
```bash
curl "http://localhost:8006/api/v1/analytics/peak-hours?days=7"
```

## 5. Explore API Documentation

Open in browser:
- **Swagger UI:** http://localhost:8006/docs
- **ReDoc:** http://localhost:8006/redoc

## 6. Manual Event Creation

```bash
curl -X POST http://localhost:8006/api/v1/analytics/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "movie_id": "00000000-0000-0000-0000-000000000002",
    "event_type": "start",
    "position_seconds": 0
  }'
```

## 7. Query ClickHouse Directly

```bash
# Connect to ClickHouse
docker exec -it clickhouse clickhouse-client

# Run queries
USE analytics;
SELECT count() FROM viewing_events;
SELECT movie_id, sum(start_count) as views FROM popular_content_mv GROUP BY movie_id ORDER BY views DESC LIMIT 5;
```

## 8. Send Kafka Events

```bash
# Install kafka-python
pip install kafka-python

# Python script to send event
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

event = {
    "user_id": "00000000-0000-0000-0000-000000000001",
    "movie_id": "00000000-0000-0000-0000-000000000002",
    "action": "stream_start",
    "timestamp": "2024-11-15T10:30:00Z",
    "position_seconds": 0
}

producer.send('stream.start', event)
producer.flush()
```

## 9. View Logs

```bash
# All services
make logs

# Analytics service only
make docker-logs
```

## 10. Stop Services

```bash
make docker-down
```

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs analytics-service

# Restart services
docker-compose restart
```

### ClickHouse connection error
```bash
# Verify ClickHouse is running
docker ps | grep clickhouse

# Check ClickHouse logs
docker-compose logs clickhouse
```

### Kafka connection error
```bash
# Disable Kafka in .env if not needed
ENABLE_KAFKA=False

# Restart service
docker-compose restart analytics-service
```

## Development Workflow

```bash
# 1. Make code changes
# 2. Rebuild and restart
docker-compose up -d --build

# 3. Test changes
python test_events.py

# 4. Run tests
pytest
```

## Useful Make Commands

```bash
make help           # Show all commands
make install        # Install dependencies
make run            # Run locally (without Docker)
make docker-build   # Build Docker image
make docker-up      # Start all services
make docker-down    # Stop all services
make test           # Run tests
make test-events    # Generate test data
make logs           # View logs
make clean          # Clean temporary files
```

## Next Steps

1. Read full documentation: `README.md`
2. Review implementation: `ANALYTICS_SERVICE_SUMMARY.md`
3. Explore ClickHouse schema: `clickhouse/schema.sql`
4. Check out the code: `app/`

Enjoy analyzing your cinema data! 🎬📊
