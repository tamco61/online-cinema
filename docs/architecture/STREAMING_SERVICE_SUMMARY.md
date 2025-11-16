# Streaming Service - Итоговый отчет

## ✅ Выполнено

Streaming Service с S3/MinIO, signed URLs, проверкой подписки и трекингом прогресса полностью реализован.

## 🎯 Функциональность

### ✅ Генерация Signed URLs
- **S3/MinIO интеграция** через boto3
- Signed URLs для HLS/DASH манифестов
- Поддержка: `index.m3u8` (HLS), `index.mpd` (DASH)
- Проверка существования объектов в S3
- Настраиваемое время жизни URL (default: 1 час)

**Структура бакета:**
```
vod/
└── movies/
    └── {movie_id}/
        ├── index.m3u8
        ├── chunk_00001.ts
        ├── chunk_00002.ts
        └── ...
```

### ✅ Проверка доступа
**2-уровневая проверка:**
1. **JWT токен** (валидация через shared secret)
2. **Активная подписка** (HTTP запрос к user-service)

**Кэширование:**
- Статус подписки кэшируется в Redis (TTL: 5 мин)
- Повторные проверки берутся из кэша
- Автоматическая инвалидация

### ✅ Трекинг прогресса просмотра
**Двухуровневое хранение:**
- **Redis** - быстрый доступ (TTL: 24 часа)
- **PostgreSQL** - постоянное хранение

**Endpoints:**
- `POST /stream/{movie_id}/progress` - обновление прогресса
- `GET /stream/{movie_id}/progress` - получение прогресса

**Рекомендация:** клиент отправляет прогресс каждые 10 секунд

### ✅ Kafka события
**3 типа событий:**
1. **stream.start** - начало просмотра
2. **stream.progress** - обновление прогресса
3. **stream.stop** - остановка просмотра

**Формат события:**
```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "action": "stream_start",
  "timestamp": "2024-11-15T10:30:00"
}
```

### ✅ Интеграция с User Service
**HTTP клиент (httpx):**
- `GET /api/v1/subscriptions/current` - проверка подписки
- Timeout: 5 секунд
- Автоматический retry при ошибках
- Кэширование результатов

## 📁 Структура

```
streaming-service/
├── app/
│   ├── main.py                          # FastAPI app
│   ├── core/
│   │   ├── config.py                    # Settings (S3, Kafka, Redis, DB)
│   │   ├── s3_client.py                 # S3/MinIO client + signed URLs
│   │   ├── cache.py                     # Redis (progress + subscription)
│   │   ├── security.py                  # JWT validation
│   │   ├── kafka_producer.py            # Kafka events
│   │   └── user_service_client.py       # HTTP client
│   ├── db/
│   │   ├── models.py                    # WatchProgress, StreamSession
│   │   └── session.py                   # AsyncSession
│   ├── schemas/
│   │   └── streaming.py                 # Pydantic models
│   ├── services/
│   │   └── streaming_service.py         # Business logic
│   └── api/v1/endpoints/
│       └── streaming.py                 # Endpoints
├── migrations/
│   └── 001_create_tables.sql           # DB schema
├── docker-compose.yml                   # PostgreSQL + Redis + MinIO
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 📊 База данных (2 таблицы)

### 1. watch_progress
Хранение прогресса просмотра

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User reference (indexed) |
| movie_id | UUID | Movie reference (indexed) |
| position_seconds | INTEGER | Позиция воспроизведения |
| created_at | TIMESTAMP | Время создания |
| updated_at | TIMESTAMP | Время обновления |
| last_watched_at | TIMESTAMP | Последний просмотр |

**Constraint:** UNIQUE(user_id, movie_id)

### 2. stream_sessions
Трекинг сессий стриминга (аналитика)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User reference |
| movie_id | UUID | Movie reference |
| started_at | TIMESTAMP | Начало сессии |
| ended_at | TIMESTAMP | Конец сессии |
| duration_seconds | INTEGER | Длительность |
| user_agent | VARCHAR | User agent |
| ip_address | VARCHAR | IP адрес |

## 📋 API Endpoints

### Streaming API

| Method | Endpoint | Description | Auth | Access Control |
|--------|----------|-------------|------|----------------|
| POST | `/api/v1/stream/{movie_id}` | Начать стриминг | JWT | Subscription |
| POST | `/api/v1/stream/{movie_id}/progress` | Обновить прогресс | JWT | - |
| GET | `/api/v1/stream/{movie_id}/progress` | Получить прогресс | JWT | - |
| POST | `/api/v1/stream/{movie_id}/stop` | Остановить стриминг | JWT | - |

## 🔧 Интеграции

### S3/MinIO
- Библиотека: **boto3 1.34.0**
- Signature version: **s3v4**
- Bucket: `vod`
- Signed URL expiration: **3600 секунд (1 час)**
- Методы:
  - `generate_signed_url()` - генерация signed URL
  - `get_manifest_url()` - URL манифеста (HLS/DASH)
  - `get_segment_url()` - URL сегмента
  - `check_object_exists()` - проверка существования

### Kafka
- Библиотека: **aiokafka 0.10.0**
- Топики: `stream.{start|progress|stop}`
- События при:
  - Начале просмотра (`start_stream`)
  - Обновлении прогресса (`update_progress`)
  - Остановке просмотра (`end_stream`)

### Redis
**2 типа кэша:**
1. **Progress cache:**
   - Ключ: `progress:{user_id}:{movie_id}`
   - TTL: 86400 секунд (24 часа)
   - Значение: `{user_id, movie_id, position_seconds}`

2. **Subscription cache:**
   - Ключ: `subscription:{user_id}`
   - TTL: 300 секунд (5 минут)
   - Значение: `{is_active, plan_id, expires_at}`

### PostgreSQL
- Async (asyncpg)
- 2 таблицы: watch_progress, stream_sessions
- Автоматическая синхронизация прогресса из Redis

### User Service (HTTP)
- Библиотека: **httpx 0.25.2** (async)
- Endpoint: `GET /api/v1/subscriptions/current`
- Timeout: 5 секунд
- Кэширование ответов в Redis

## 🚀 Быстрый старт

```bash
cd streaming-service

# Docker Compose (включает PostgreSQL, Redis, MinIO)
docker-compose up

# API: http://localhost:8005
# Docs: http://localhost:8005/docs
# MinIO Console: http://localhost:9001
```

### Локально

```bash
cp .env.example .env
pip install -r requirements.txt

# Запустить инфраструктуру
docker-compose up -d postgres redis minio

# Миграции
psql -U streaming_service -d streaming_db -h localhost -p 5435 -f migrations/001_create_tables.sql

# Запуск
python -m app.main
```

## 📝 Примеры использования

### 1. Начать стриминг (+ проверка подписки)

```bash
curl -X POST http://localhost:8005/api/v1/stream/{movie_id} \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"manifest_type": "hls"}'
```

**Ответ:**
```json
{
  "manifest_url": "http://minio:9000/vod/movies/{movie_id}/index.m3u8?X-Amz-Algorithm=AWS4-HMAC-SHA256&...",
  "expires_in": 3600,
  "manifest_type": "hls"
}
```

**Что происходит:**
1. Проверка JWT токена
2. HTTP запрос к user-service для проверки подписки
3. Генерация signed URL для `movies/{movie_id}/index.m3u8`
4. Создание stream_session в БД
5. Публикация Kafka события `stream.start`

### 2. Обновить прогресс (каждые 10 секунд)

```bash
curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/progress \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"position_seconds": 120}'
```

**Ответ:**
```json
{
  "success": true,
  "position_seconds": 120,
  "message": "Progress updated successfully"
}
```

**Что происходит:**
1. Сохранение в Redis (быстро)
2. Синхронизация в PostgreSQL
3. Публикация Kafka события `stream.progress`

### 3. Получить текущий прогресс

```bash
curl http://localhost:8005/api/v1/stream/{movie_id}/progress \
  -H "Authorization: Bearer <token>"
```

**Ответ:**
```json
{
  "user_id": "uuid",
  "movie_id": "uuid",
  "position_seconds": 120,
  "last_watched_at": "2024-11-15T10:30:00"
}
```

**Источник данных:**
- Сначала Redis (если есть)
- Затем PostgreSQL (если нет в Redis)

### 4. Остановить стриминг

```bash
curl -X POST http://localhost:8005/api/v1/stream/{movie_id}/stop \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"position_seconds": 1800}'
```

**Что происходит:**
1. Обновление финального прогресса
2. Публикация Kafka события `stream.stop`
3. Логирование завершения сессии

## ⚙️ Конфигурация

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

# JWT (должен совпадать с auth-service)
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=stream
ENABLE_KAFKA=true

# Redis
REDIS_HOST=localhost
REDIS_PROGRESS_TTL=86400
REDIS_SUBSCRIPTION_CACHE_TTL=300
```

## 🎓 Ключевые фичи

✅ **S3/MinIO integration** с boto3
✅ **Signed URLs** для HLS/DASH манифестов
✅ **2-level access control** (JWT + subscription)
✅ **HTTP client** для user-service (httpx)
✅ **Redis двойного назначения** (progress + subscription cache)
✅ **Dual storage** для прогресса (Redis + PostgreSQL)
✅ **Kafka события** (start, progress, stop)
✅ **Stream sessions tracking** для аналитики
✅ **Docker Compose** с MinIO setup
✅ **Автоматическое создание бакета** (minio-init)

## 📦 Зависимости

- FastAPI 0.104.1
- boto3 1.34.0 - S3 client
- SQLAlchemy 2.0.23 (async)
- asyncpg 0.29.0
- redis 5.0.1
- aiokafka 0.10.0
- httpx 0.25.2 - HTTP client
- PyJWT 2.8.0

## 🏗️ Архитектура

```
┌────────────────┐
│     Client     │
│   (JWT Token)  │
└────────┬───────┘
         │
         │ POST /stream/{movie_id}
         │
         ▼
┌─────────────────────────────┐
│    Streaming Service        │
│  ┌───────────────────────┐  │
│  │ 1. Validate JWT       │  │
│  │ 2. Check Subscription │──┼────► User Service (HTTP)
│  │ 3. Generate Signed URL│  │      ├─ Check subscription
│  │ 4. Track Session      │  │      └─ Cache in Redis
│  │ 5. Publish Kafka Event│  │
│  └───────────────────────┘  │
└─────────┬───────────────────┘
          │
          ├──► S3/MinIO (Signed URL)
          ├──► Redis (Progress, Subscription Cache)
          ├──► PostgreSQL (WatchProgress, StreamSessions)
          └──► Kafka (stream.start)
                │
                ▼
         ┌──────────────┐
         │ Analytics    │
         │ Services     │
         └──────────────┘
```

## 🔄 Event Flow

```
1. Client запрашивает манифест с JWT токеном
         ↓
2. Streaming Service проверяет JWT
         ↓
3. HTTP запрос к User Service → проверка подписки
         ↓
4. Кэширование статуса подписки в Redis (5 мин)
         ↓
5. Генерация signed URL для S3 объекта
         ↓
6. Создание StreamSession в БД
         ↓
7. Публикация Kafka события stream.start
         ↓
8. Возврат signed URL клиенту
         ↓
9. Client скачивает манифест и сегменты напрямую из S3
         ↓
10. Client периодически обновляет прогресс (каждые 10 сек)
         ↓
11. Прогресс сохраняется в Redis + синхронизируется в PostgreSQL
         ↓
12. Публикация Kafka события stream.progress
```

## 🔒 Access Control Flow

```
POST /stream/{movie_id}
  │
  ├─► Extract JWT from Authorization header
  │
  ├─► Validate JWT (verify_access_token)
  │    ├─ Check signature
  │    ├─ Check expiration
  │    └─ Extract user_id
  │
  ├─► Check subscription (UserServiceClient)
  │    ├─ Try Redis cache first
  │    │   └─ Cache HIT? → Return cached status
  │    │
  │    └─ Cache MISS?
  │        ├─ HTTP GET to user-service
  │        ├─ Parse response
  │        ├─ Cache in Redis (5 min TTL)
  │        └─ Return subscription status
  │
  ├─► is_active == True?
  │    ├─ YES → Continue
  │    └─ NO  → Return 403 Forbidden
  │
  └─► Generate signed URL and return
```

## 📈 MinIO Setup

**Console:** http://localhost:9001

**Credentials:**
- Username: `minioadmin`
- Password: `minioadmin`

**Загрузка видео:**
1. Открыть MinIO Console
2. Bucket: `vod`
3. Создать папку: `movies/{movie_id}/`
4. Загрузить файлы:
   - `index.m3u8` - HLS manifest
   - `chunk_00001.ts`, `chunk_00002.ts`, ... - сегменты

**Инициализация бакета:**
```bash
# Автоматически через docker-compose (minio-init service)
mc alias set myminio http://minio:9000 minioadmin minioadmin
mc mb myminio/vod --ignore-existing
mc anonymous set download myminio/vod
```

## 🚦 Интеграция с другими сервисами

### Auth Service
- Генерирует JWT токены
- Shared secret: `JWT_SECRET_KEY`
- Streaming service валидирует токены

### User Service
- HTTP endpoint: `GET /api/v1/subscriptions/current`
- Проверка активной подписки
- Результат кэшируется в Redis (5 мин)

### Catalog Service
- Movie metadata (indirect)
- Movie IDs используются для поиска в S3

### Analytics (потенциальная интеграция)
- Kafka consumer для событий `stream.*`
- Агрегация метрик просмотров
- Dashboard с аналитикой

## ✨ Итого

**Всего создано: 25+ файлов**

Streaming Service готов к использованию и включает:
- ✅ S3/MinIO интеграция с signed URLs
- ✅ 2-level access control (JWT + subscription)
- ✅ HTTP интеграция с user-service
- ✅ Dual storage для прогресса (Redis + PostgreSQL)
- ✅ Kafka события для аналитики
- ✅ Stream sessions tracking
- ✅ MinIO с автоматическим созданием бакета
- ✅ Docker Compose с полной инфраструктурой
- ✅ Полную документацию

Сервис готов к стримингу видео с контролем доступа и трекингом прогресса!
