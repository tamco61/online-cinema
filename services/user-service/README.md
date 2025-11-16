# User Service

User profiles, subscriptions, watch history, and favorites management.

## Features

- ✅ User profiles (nickname, avatar, language, country)
- ✅ Subscription plans and management
- ✅ Watch history with progress tracking
- ✅ Favorites/bookmarks
- ✅ Redis caching for profiles
- ✅ JWT authentication (from auth-service)

## Database Schema

### Tables
1. **user_profiles** - User profile data
2. **plans** - Subscription plans
3. **subscriptions** - User subscriptions
4. **watch_history** - Watch progress
5. **favorites** - Favorite content

## API Endpoints

All endpoints require authentication (JWT from auth-service).

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update profile

### Subscriptions
- `GET /api/v1/users/me/subscriptions` - Get user subscriptions

### Watch History
- `GET /api/v1/users/me/history` - Get watch history
- `POST /api/v1/users/me/history` - Update watch progress

### Favorites
- `GET /api/v1/users/me/favorites` - Get favorites
- `POST /api/v1/users/me/favorites/{content_id}` - Add to favorites
- `DELETE /api/v1/users/me/favorites/{content_id}` - Remove from favorites

## Quick Start

```bash
# Using Docker Compose
docker-compose up

# Or locally
cp .env.example .env
pip install -r requirements.txt
python -m app.main
```

API: http://localhost:8002
Docs: http://localhost:8002/docs

## Configuration

Set `JWT_SECRET_KEY` to match auth-service!

## Testing

```bash
pytest app/tests/
```
