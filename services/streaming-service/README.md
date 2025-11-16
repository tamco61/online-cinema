# Streaming Service

Video streaming service with S3/MinIO, signed URLs, subscription checking, and watch progress tracking.

## Features

- ✅ **Signed URLs** for HLS/DASH manifests (S3/MinIO)
- ✅ **Access Control** (JWT + active subscription check)
- ✅ **Watch Progress Tracking** (Redis + PostgreSQL)
- ✅ **Kafka Events** (stream.start, stream.stop, stream.progress)
- ✅ **User Service Integration** (subscription validation via HTTP)
- ✅ **Stream Sessions** (analytics tracking)

## Architecture

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ JWT Token
       ▼
┌─────────────────────────┐
│  Streaming API          │
│  ├─ Auth Check          │
│  ├─ Subscription Check  │──────► User Service (HTTP)
│  └─ Generate Signed URL │
└─────┬───────────────────┘
      │
      ▼
┌──────────────────┐       ┌──────────┐
│   S3/MinIO       │       │  Kafka   │
│   vod bucket     │       │  Events  │
│  ├─ index.m3u8   │       └──────────┘
│  └─ chunks/*.ts  │
└──────────────────┘
      │
      ▼ Signed URL
┌──────────────┐
│   Client     │
│  Video Player│
└──────────────┘
```

## Database Schema

### watch_progress
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User reference |
| movie_id | UUID | Movie reference |
| position_seconds | INTEGER | Playback position |
| last_watched_at | TIMESTAMP | Last update time |

### stream_sessions
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User reference |
| movie_id | UUID | Movie reference |
| started_at | TIMESTAMP | Session start |
| ended_at | TIMESTAMP | Session end |
| duration_seconds | INTEGER | Total duration |
| user_agent | VARCHAR | Client info |
| ip_address | VARCHAR | Client IP |

## API Endpoints

### Start Streaming

**POST** `/api/v1/stream/{movie_id}`

Start streaming session and get manifest URL.

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Body:**
```json
{
  "manifest_type": "hls"
}
```

**Response:**
```json
{
  "manifest_url": "http://minio:9000/vod/movies/{movie_id}/index.m3u8?X-Amz-Algorithm=...",
  "expires_in": 3600,
  "manifest_type": "hls"
}
```

**Access Control:**
- ✅ Valid JWT token
- ✅ Active subscription (checked via user-service)

**Kafka Event:** `stream.start`

---

### Update Progress

**POST** `/api/v1/stream/{movie_id}/progress`

Update watch progress (call every 10 seconds).

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Body:**
```json
{
  "position_seconds": 120
}
```

**Response:**
```json
{
  "success": true,
  "position_seconds": 120,
  "message": "Progress updated successfully"
}
```

**Storage:**
- Redis (fast access, TTL: 24h)
- PostgreSQL (persistent)

**Kafka Event:** `stream.progress`

---

### Get Progress

**GET** `/api/v1/stream/{movie_id}/progress`

Get current watch progress.

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "position_seconds": 120,
  "last_watched_at": "2024-11-15T10:30:00"
}
```

---

### Stop Streaming

**POST** `/api/v1/stream/{movie_id}/stop`

Stop streaming session.

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Body:**
```json
{
  "position_seconds": 1800
}
```

**Response:**
```json
{
  "success": true,
  "message": "Stream stopped successfully"
}
```

**Kafka Event:** `stream.stop`

## S3/MinIO Structure

```
vod/
├── movies/
│   ├── {movie_id}/
│   │   ├── index.m3u8          # HLS manifest
│   │   ├── index.mpd           # DASH manifest (optional)
│   │   ├── chunk_00001.ts      # Video segment
│   │   ├── chunk_00002.ts
│   │   └── ...
│   └── ...
```

## Kafka Events

### stream.start
```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "action": "stream_start",
  "timestamp": "2024-11-15T10:30:00"
}
```

### stream.progress
```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "action": "progress_update",
  "position_seconds": 120,
  "timestamp": "2024-11-15T10:30:00"
}
```

### stream.stop
```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "action": "stream_stop",
  "position_seconds": 1800,
  "timestamp": "2024-11-15T10:30:00"
}
```

## Quick Start

### Using Docker Compose

```bash
cd streaming-service

# Start all services (PostgreSQL, Redis, MinIO, Streaming Service)
docker-compose up

# API: http://localhost:8005
# Docs: http://localhost:8005/docs
# MinIO Console: http://localhost:9001
```

### Local Development

```bash
# Copy environment file
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start infrastructure
docker-compose up -d postgres redis minio

# Run migrations
psql -U streaming_service -d streaming_db -h localhost -p 5435 -f migrations/001_create_tables.sql

# Run service
python -m app.main

# Access at http://localhost:8005
```

## Configuration

Environment variables (`.env`):

```bash
# S3/MinIO
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=vod
SIGNED_URL_EXPIRATION=3600

# User Service
USER_SERVICE_URL=http://localhost:8002
USER_SERVICE_TIMEOUT=5

# JWT (must match auth-service)
JWT_SECRET_KEY=your-secret-key-change-in-production

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ENABLE_KAFKA=true

# Redis
REDIS_HOST=localhost
REDIS_PROGRESS_TTL=86400
REDIS_SUBSCRIPTION_CACHE_TTL=300
```

## Signed URL Flow

1. Client requests manifest with JWT token
2. Service validates JWT and checks subscription
3. Service generates signed URL for S3 object
4. Client receives signed URL (expires in 1 hour)
5. Client fetches manifest and segments directly from S3
6. Client periodically updates progress via API

## Integration with Other Services

### Auth Service
- JWT tokens generated by auth-service
- Streaming service validates tokens using shared secret

### User Service
- HTTP calls to check active subscription
- Subscription status cached in Redis (5 min TTL)

### Catalog Service
- Movie metadata (not directly integrated)
- Movie IDs used to locate S3 objects

## Dependencies

- FastAPI 0.104.1
- boto3 1.34.0 (S3 client)
- SQLAlchemy 2.0.23 (async)
- asyncpg 0.29.0
- redis 5.0.1
- aiokafka 0.10.0
- httpx 0.25.2 (HTTP client)
- PyJWT 2.8.0

## MinIO Setup

Access MinIO Console at http://localhost:9001

**Credentials:**
- Username: `minioadmin`
- Password: `minioadmin`

**Upload Video Files:**
1. Navigate to `vod` bucket
2. Create directory: `movies/{movie_id}/`
3. Upload HLS files: `index.m3u8`, `chunk_*.ts`

## Health Check

```bash
curl http://localhost:8005/health
```

Returns:
```json
{
  "status": "healthy",
  "s3": "ok",
  "redis": "ok",
  "kafka": "enabled"
}
```

## Example Usage

### 1. Start Streaming

```bash
curl -X POST http://localhost:8005/api/v1/stream/{movie_id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"manifest_type": "hls"}'
```

### 2. Update Progress (every 10s)

```bash
curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/progress \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"position_seconds": 120}'
```

### 3. Get Progress

```bash
curl http://localhost:8005/api/v1/stream/{movie_id}/progress \
  -H "Authorization: Bearer <token>"
```

### 4. Stop Streaming

```bash
curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/stop \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"position_seconds": 1800}'
```

## Production Notes

1. **S3 Security**: Use IAM roles instead of access keys
2. **CDN**: Put CloudFront/CDN in front of S3 for better performance
3. **DRM**: Add DRM protection for premium content
4. **Rate Limiting**: Limit progress update frequency per user
5. **Monitoring**: Track streaming metrics (buffering, bitrate, etc.)

## Troubleshooting

### "No active subscription" error
- Check user has active subscription in user-service
- Verify subscription cache is not stale

### "Manifest not found" error
- Verify movie files exist in S3: `movies/{movie_id}/index.m3u8`
- Check S3 bucket name and credentials

### Signed URL expired
- Increase `SIGNED_URL_EXPIRATION` setting
- Client should request new URL when expired
