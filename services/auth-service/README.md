# Auth Service

Authentication and authorization service for the Online Cinema platform.

## Features

- ✅ User registration with email/password
- ✅ User login with JWT token generation
- ✅ Access token (JWT) and refresh token (stored in Redis)
- ✅ Token refresh endpoint
- ✅ Logout (single session and all sessions)
- ✅ Password hashing with bcrypt
- ✅ Rate limiting on login endpoint (in-memory)
- 🚧 OAuth2 integration (Google) - skeleton implementation

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (async via asyncpg)
- **Cache/Sessions**: Redis
- **Authentication**: JWT (HS256)
- **Password Hashing**: bcrypt
- **ORM**: SQLAlchemy 2.0 (async)

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (rate limited: 5 req/min)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (invalidate refresh token)
- `POST /api/v1/auth/logout-all` - Logout from all devices
- `GET /api/v1/auth/me` - Get current user info (requires auth)

### OAuth (Skeleton)

- `GET /api/v1/auth/oauth/google` - Initiate Google OAuth
- `GET /api/v1/auth/oauth/google/callback` - Google OAuth callback

### Health & Info

- `GET /health` - Health check
- `GET /` - Service info
- `GET /docs` - API documentation (Swagger UI)

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Installation

1. Clone the repository and navigate to auth-service:

```bash
cd online-cinema/services/auth-service
```

2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env and configure your settings
```

5. Start PostgreSQL and Redis (or use Docker Compose):

```bash
docker-compose up -d postgres redis
```

6. Run database migrations:

```bash
psql -U auth_user -d auth_db -h localhost -f migrations/001_create_users_table.sql
```

7. Start the service:

```bash
python -m app.main
# or with uvicorn
uvicorn app.main:app --reload --port 8001
```

8. Access the API:

- API: http://localhost:8001
- Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health

## Docker Compose

Start all services (app, PostgreSQL, Redis):

```bash
docker-compose up
```

## Configuration

All configuration is done via environment variables. See `.env.example` for available options.

### Important Settings

- `JWT_SECRET_KEY` - **CHANGE THIS IN PRODUCTION!** Generate with: `openssl rand -hex 32`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token TTL (default: 15 minutes)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token TTL (default: 7 days)
- `LOGIN_RATE_LIMIT_PER_MINUTE` - Login rate limit (default: 5)

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
ruff check app/
```

### Type Checking

```bash
mypy app/
```

## Project Structure

```
auth-service/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py      # Auth endpoints
│   │   │   │   └── oauth.py     # OAuth endpoints
│   │   │   └── router.py        # V1 router
│   │   └── deps.py              # API dependencies
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   └── security.py          # Security utilities
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── session.py           # Database session
│   ├── schemas/
│   │   └── auth.py              # Pydantic schemas
│   ├── services/
│   │   ├── auth_service.py      # Auth business logic
│   │   ├── jwt_service.py       # JWT operations
│   │   └── redis_service.py     # Redis operations
│   └── main.py                  # FastAPI app
├── migrations/
│   └── 001_create_users_table.sql
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

## Security Features

- ✅ Password hashing with bcrypt (12 rounds)
- ✅ JWT tokens with expiration
- ✅ Refresh token rotation
- ✅ Token storage in Redis with TTL
- ✅ Rate limiting on sensitive endpoints
- ✅ CORS protection
- ✅ Password complexity validation

## Token Flow

### Registration / Login

1. User sends email/password
2. Service validates credentials
3. Service generates:
   - Access token (JWT, 15 min TTL)
   - Refresh token (JWT, 7 day TTL)
4. Refresh token stored in Redis with key: `auth:refresh:{user_id}:{token_id}`
5. Both tokens returned to client

### Token Refresh

1. Client sends refresh token
2. Service validates token and checks Redis
3. Service generates new access token
4. New access token returned to client

### Logout

1. Client sends refresh token
2. Service deletes token from Redis
3. Token is now invalid

## Troubleshooting

### Cannot connect to PostgreSQL

- Check PostgreSQL is running: `docker ps`
- Verify connection settings in `.env`
- Test connection: `psql -U auth_user -d auth_db -h localhost`

### Cannot connect to Redis

- Check Redis is running: `docker ps`
- Test connection: `redis-cli ping`

### Rate limit issues

- Rate limiting is in-memory and resets on app restart
- For production, implement Redis-based rate limiting

## Production Deployment

1. Change `JWT_SECRET_KEY` to a strong random value
2. Set `ENVIRONMENT=production`
3. Disable auto-reload: `RELOAD=false`
4. Use proper database migrations (Alembic)
5. Set up SSL/TLS for PostgreSQL and Redis
6. Implement Redis-based rate limiting
7. Set up monitoring and logging
8. Use a reverse proxy (nginx) with rate limiting

## License

MIT
