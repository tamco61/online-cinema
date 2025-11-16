# Catalog Service - Итоговый отчет

## ✅ Выполнено

Catalog Service с Kafka интеграцией полностью реализован.

## 🎯 Функциональность

### ✅ CRUD для фильмов
- Создание, чтение, обновление фильмов
- Жанры и персоны (актеры, режиссеры)
- Many-to-many связи
- Статус публикации

### ✅ Kafka события
**3 типа событий:**
1. **catalog.movie.created** - фильм создан
2. **catalog.movie.updated** - фильм обновлен
3. **catalog.movie.published** - фильм опубликован

**Формат события:**
```json
{
  "movie_id": "uuid",
  "action": "created",
  "timestamp": "2024-11-15T10:30:00",
  "payload": {
    "title": "Inception",
    "year": 2010,
    "rating": 8.8
  }
}
```

### ✅ Redis кэширование
- Кэш деталей фильма (TTL: 10 мин)
- Автоматическая инвалидация при обновлении
- Кэш популярных фильмов

## 📁 Структура

```
catalog-service/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── cache.py              # Redis cache
│   ├── db/
│   │   ├── models.py             # Movie, Genre, Person, ассоциации
│   │   └── session.py
│   ├── schemas/
│   │   └── movie.py              # Pydantic схемы
│   ├── services/
│   │   ├── kafka_producer.py    # Kafka события
│   │   └── movie_service.py     # Бизнес-логика + Kafka + Cache
│   └── api/v1/endpoints/
│       └── movies.py             # Public + Admin endpoints
├── migrations/
│   └── 001_create_tables.sql
├── docker-compose.yml            # + Kafka + Zookeeper
└── requirements.txt
```

## 📊 База данных (5 таблиц)

1. **movies** - фильмы (title, year, rating, is_published, etc.)
2. **genres** - жанры (Action, Comedy, Drama, etc.)
3. **persons** - актеры/режиссеры (full_name, photo_url, etc.)
4. **movie_genres** - many-to-many
5. **movie_persons** - many-to-many с ролью (actor/director)

## 📋 API Endpoints

### Public (опубликованные фильмы)
| Method | Endpoint | Description | Cache |
|--------|----------|-------------|-------|
| GET | `/api/v1/movies` | Список фильмов + пагинация | ❌ |
| GET | `/api/v1/movies/{id}` | Детали фильма | ✅ |

### Admin
| Method | Endpoint | Description | Kafka Event |
|--------|----------|-------------|-------------|
| POST | `/api/v1/movies` | Создать фильм | `movie.created` |
| PATCH | `/api/v1/movies/{id}` | Обновить фильм | `movie.updated` |
| POST | `/api/v1/movies/{id}/publish` | Опубликовать | `movie.published` |

## 🔧 Интеграции

### Kafka
- Библиотека: **aiokafka**
- Топики: `catalog.movie.*`
- Graceful startup/shutdown
- Опциональное отключение (`ENABLE_KAFKA=false`)

### Redis
- Кэш деталей фильма
- TTL: 600 секунд (10 мин)
- Инвалидация при обновлении/публикации

### PostgreSQL
- Async (asyncpg)
- Many-to-many связи
- Миграция с sample data (5 жанров)

## 🚀 Быстрый старт

```bash
cd catalog-service

# Docker Compose (включает Kafka + Zookeeper)
docker-compose up

# API: http://localhost:8003
# Docs: http://localhost:8003/docs
```

### Локально

```bash
cp .env.example .env
pip install -r requirements.txt

# Запустить Kafka, Zookeeper, Redis, Postgres
docker-compose up -d kafka redis postgres

# Миграции
psql -U catalog_service -d catalog_db -h localhost -f migrations/001_create_tables.sql

# Запуск
python -m app.main
```

## 📝 Примеры использования

### Создать фильм (Admin + Kafka event)

```bash
curl -X POST http://localhost:8003/api/v1/movies \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Inception",
    "year": 2010,
    "rating": 8.8,
    "description": "Mind-bending thriller",
    "duration": 148,
    "genre_ids": ["<genre-uuid>"]
  }'
```

**Kafka event публикуется:** `catalog.movie.created`

### Опубликовать фильм

```bash
curl -X POST http://localhost:8003/api/v1/movies/{id}/publish
```

**Kafka event:** `catalog.movie.published`

### Получить фильм (Public + Cache)

```bash
curl http://localhost:8003/api/v1/movies/{id}
```

Первый запрос - из БД → сохраняется в Redis
Последующие - из Redis cache (10 мин)

## ⚙️ Конфигурация

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=catalog
ENABLE_KAFKA=true

# Redis
REDIS_HOST=localhost
REDIS_CACHE_TTL=600
ENABLE_CACHE=true
```

## 🎓 Ключевые фичи

✅ **Kafka producer** с aiokafka
✅ **3 типа событий** (created, updated, published)
✅ **Redis кэширование** с автоинвалидацией
✅ **Many-to-many** связи (жанры, персоны)
✅ **Public/Admin** endpoints
✅ **Пагинация** и поиск
✅ **Docker Compose** с Kafka + Zookeeper
✅ **Sample data** в миграции

## 📦 Зависимости

- FastAPI 0.104.1
- SQLAlchemy 2.0.23 (async)
- **aiokafka 0.10.0** - Kafka client
- redis 5.0.1
- asyncpg 0.29.0

## 🏗️ Архитектура

```
┌────────────┐
│   Client   │
└─────┬──────┘
      │
      ▼
┌──────────────────────────┐
│   Catalog API            │
│  ┌────────────────────┐  │
│  │  Movie Service     │  │
│  │  ├─ Kafka Events   │  │
│  │  └─ Redis Cache    │  │
│  └────────────────────┘  │
└───┬────────┬────────┬────┘
    │        │        │
    ▼        ▼        ▼
┌────────┐ ┌──────┐ ┌──────────┐
│ Kafka  │ │Redis │ │ Postgres │
└────────┘ └──────┘ └──────────┘
    │
    ▼
┌────────────────┐
│  Other Services│ (подписчики Kafka)
└────────────────┘
```

## 🔄 Event Flow

```
Admin создает фильм
       ↓
Movie Service
       ↓
Сохранение в БД
       ↓
Kafka Producer → catalog.movie.created
       ↓
[Другие сервисы получают событие]
```

## ✨ Итого

**Всего создано: 25+ файлов**

Catalog Service готов к использованию и включает:
- ✅ Полный CRUD для фильмов
- ✅ Kafka события (3 типа)
- ✅ Redis кэширование
- ✅ Many-to-many связи
- ✅ Public/Admin API
- ✅ Docker + Kafka setup
- ✅ Полную документацию

Сервис готов к интеграции с другими микросервисами через Kafka!
