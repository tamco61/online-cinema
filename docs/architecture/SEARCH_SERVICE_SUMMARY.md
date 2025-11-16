# Search Service - Итоговый отчет

## ✅ Выполнено

Search Service с Elasticsearch и Kafka интеграцией полностью реализован.

## 🎯 Функциональность

### ✅ Полнотекстовый поиск
- Поиск по полям: **title**, **description**, **actors**, **directors**, **genres**
- Многополевой поиск с весами (title x3, actors/directors x2)
- Фильтры (facets):
  - По жанрам (genre slugs)
  - По годам (year_from, year_to)
  - По рейтингу (rating_from, rating_to)
  - По возрастному рейтингу (age_rating)
- Пагинация (page, size)
- Только опубликованные фильмы (published_only)

### ✅ Автодополнение (Autocomplete)
- Поиск по началу названия (edge N-gram)
- Топ suggestions с сортировкой по релевантности и рейтингу
- Минимум 2 символа для запроса

### ✅ Elasticsearch индекс
**Mapping:**
- Text fields с анализаторами (title, description)
- Keyword fields для фильтров (genres, age_rating)
- Nested fields для genres, actors, directors
- Edge N-gram tokenizer для autocomplete (2-20 символов)
- Completion suggester для title

**Индекс:** `movies`

### ✅ Kafka Consumer
**3 типа событий от catalog-service:**
1. **catalog.movie.created** → индексация нового фильма
2. **catalog.movie.updated** → переиндексация фильма
3. **catalog.movie.published** → обновление флага is_published

**Формат события:**
```json
{
  "movie_id": "uuid",
  "action": "created|updated|published",
  "timestamp": "2024-11-15T10:30:00",
  "payload": {
    "title": "Inception",
    "year": 2010,
    "rating": 8.8,
    "genres": [...],
    "actors": [...],
    "directors": [...]
  }
}
```

### ✅ Redis кэширование
- Кэш результатов поиска (TTL: 5 мин)
- Ключи: `search:query:<hash>` (MD5 от query + filters)
- Автоматическая инвалидация при индексации/обновлении

## 📁 Структура

```
search-service/
├── app/
│   ├── main.py                      # FastAPI app + lifespan
│   ├── core/
│   │   ├── config.py                # Settings (ES, Kafka, Redis)
│   │   ├── elasticsearch_client.py  # ES client + mapping
│   │   └── cache.py                 # Redis cache
│   ├── schemas/
│   │   └── search.py                # Pydantic models (SearchRequest, SearchResponse)
│   ├── services/
│   │   └── search_service.py        # SearchService (search, autocomplete, index)
│   ├── kafka_consumer/
│   │   └── consumer.py              # MovieEventConsumer
│   └── api/v1/endpoints/
│       └── search.py                # /search, /search/suggest
├── docker-compose.yml               # ES + Redis + Search Service
├── Dockerfile                       # Multi-stage build
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 📊 Elasticsearch Mapping

**Index:** `movies`

### Settings
- **number_of_shards**: 1
- **number_of_replicas**: 1
- **Analyzers:**
  - `autocomplete_analyzer` - edge_ngram tokenizer (2-20 chars)
  - `search_analyzer` - standard tokenizer

### Mappings
| Field | Type | Description |
|-------|------|-------------|
| movie_id | keyword | Уникальный ID |
| title | text | Название (с autocomplete) |
| original_title | text | Оригинальное название |
| description | text | Описание |
| year | integer | Год выпуска |
| duration | integer | Длительность (мин) |
| rating | float | Рейтинг (0-10) |
| age_rating | keyword | Возрастной рейтинг |
| is_published | boolean | Опубликовано |
| genres | nested | Жанры (id, name, slug) |
| actors | nested | Актеры (id, full_name, character_name) |
| directors | nested | Режиссеры (id, full_name) |

## 📋 API Endpoints

### Public API

| Method | Endpoint | Description | Cache |
|--------|----------|-------------|-------|
| GET | `/api/v1/search` | Полнотекстовый поиск + фильтры | ✅ |
| GET | `/api/v1/search/suggest` | Автодополнение по названию | ❌ |
| GET | `/health` | Health check (ES + Redis) | ❌ |

## 🔧 Интеграции

### Elasticsearch
- Библиотека: **elasticsearch 8.11.0** (async)
- Индекс: `movies`
- Edge N-gram для autocomplete
- Multi-match query с весами полей
- Nested queries для genres/actors/directors

### Kafka
- Библиотека: **aiokafka 0.10.0**
- Consumer group: `search-service`
- Топики: `catalog.movie.*`
- Auto offset reset: `earliest`
- Graceful startup/shutdown

### Redis
- Кэш поисковых запросов
- TTL: 300 секунд (5 мин)
- Инвалидация при индексации/обновлении

## 🚀 Быстрый старт

```bash
cd search-service

# Docker Compose (включает ES + Redis)
docker-compose up

# API: http://localhost:8004
# Docs: http://localhost:8004/docs
# Elasticsearch: http://localhost:9200
```

### Локально

```bash
cp .env.example .env
pip install -r requirements.txt

# Запустить ES и Redis
docker-compose up -d elasticsearch redis

# Запуск
python -m app.main
```

## 📝 Примеры использования

### Полнотекстовый поиск

```bash
curl "http://localhost:8004/api/v1/search?query=inception&genres=sci-fi,action&year_from=2010&rating_from=8.0&page=1&size=20"
```

**Ответ:**
```json
{
  "results": [
    {
      "movie_id": "uuid",
      "title": "Inception",
      "year": 2010,
      "rating": 8.8,
      "genres": [{"id": "uuid", "name": "Sci-Fi", "slug": "sci-fi"}],
      "actors": [{"id": "uuid", "full_name": "Leonardo DiCaprio", "character_name": "Cobb"}],
      "directors": [{"id": "uuid", "full_name": "Christopher Nolan"}]
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "total_pages": 1
}
```

### Автодополнение

```bash
curl "http://localhost:8004/api/v1/search/suggest?query=incep&limit=5"
```

**Ответ:**
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

### Health Check

```bash
curl http://localhost:8004/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "elasticsearch": "ok",
  "redis": "ok",
  "kafka": "enabled"
}
```

## ⚙️ Конфигурация

```bash
# Elasticsearch
ELASTICSEARCH_HOSTS=["http://localhost:9200"]
ELASTICSEARCH_INDEX=movies
ELASTICSEARCH_TIMEOUT=30

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=catalog
KAFKA_CONSUMER_GROUP=search-service
ENABLE_KAFKA=true

# Redis
REDIS_HOST=localhost
REDIS_CACHE_TTL=300
ENABLE_CACHE=true

# Search
SEARCH_DEFAULT_PAGE_SIZE=20
SEARCH_MAX_PAGE_SIZE=100
AUTOCOMPLETE_MAX_SUGGESTIONS=10
```

## 🎓 Ключевые фичи

✅ **Elasticsearch** с async client
✅ **Edge N-gram** для autocomplete (2-20 символов)
✅ **Multi-match query** с весами полей (title x3)
✅ **Nested queries** для genres/actors/directors
✅ **Kafka consumer** для real-time индексации
✅ **Redis кэширование** с автоинвалидацией
✅ **Фильтры** (genres, year, rating, age_rating)
✅ **Пагинация** с total_pages
✅ **Docker Compose** с Elasticsearch + Redis
✅ **Health check** endpoint

## 📦 Зависимости

- FastAPI 0.104.1
- Elasticsearch 8.11.0 (async)
- aiokafka 0.10.0 - Kafka consumer
- redis 5.0.1
- pydantic 2.5.0

## 🏗️ Архитектура

```
┌─────────────────┐
│ Catalog Service │
│  (Kafka Events) │
└────────┬────────┘
         │
         │ catalog.movie.created
         │ catalog.movie.updated
         │ catalog.movie.published
         │
         ▼
┌─────────────────────┐
│  Kafka Consumer     │
│  MovieEventConsumer │
└─────────┬───────────┘
          │
          ▼
┌──────────────────────┐       ┌──────────┐
│   Elasticsearch      │◄──────│  Redis   │
│   movies index       │       │  Cache   │
└──────────┬───────────┘       └──────────┘
           │
           ▼
┌──────────────────────┐
│   Search API         │
│  ┌────────────────┐  │
│  │ GET /search    │  │
│  │ GET /suggest   │  │
│  └────────────────┘  │
└──────────────────────┘
           │
           ▼
      ┌─────────┐
      │ Clients │
      └─────────┘
```

## 🔄 Event Flow

```
1. Admin создает фильм в Catalog Service
         ↓
2. Catalog Service публикует Kafka event: catalog.movie.created
         ↓
3. Search Service Consumer получает событие
         ↓
4. MovieEventConsumer индексирует фильм в Elasticsearch
         ↓
5. Фильм становится доступным для поиска
         ↓
6. Redis cache инвалидируется
         ↓
7. Пользователь ищет фильм через /api/v1/search
         ↓
8. Результат кэшируется в Redis (5 мин)
```

## 🔍 Примеры поисковых запросов

### 1. Поиск по названию
```bash
curl "http://localhost:8004/api/v1/search?query=matrix"
```

### 2. Фильтр по жанру и году
```bash
curl "http://localhost:8004/api/v1/search?genres=action,sci-fi&year_from=2000&year_to=2010"
```

### 3. Поиск с рейтингом
```bash
curl "http://localhost:8004/api/v1/search?query=nolan&rating_from=8.0"
```

### 4. Поиск по актеру
```bash
curl "http://localhost:8004/api/v1/search?query=leonardo+dicaprio"
```

### 5. Комплексный фильтр
```bash
curl "http://localhost:8004/api/v1/search?query=inception&genres=sci-fi&year_from=2010&rating_from=8.0&age_rating=PG-13&page=1&size=10"
```

## ✨ Elasticsearch Query Examples

### Multi-match query с весами
```json
{
  "multi_match": {
    "query": "inception",
    "fields": [
      "title^3",
      "original_title^2",
      "description",
      "actors.full_name^2",
      "directors.full_name^2"
    ],
    "type": "best_fields",
    "fuzziness": "AUTO"
  }
}
```

### Nested query для жанров
```json
{
  "nested": {
    "path": "genres",
    "query": {
      "terms": {"genres.slug": ["action", "sci-fi"]}
    }
  }
}
```

### Range filter для года и рейтинга
```json
{
  "bool": {
    "filter": [
      {"range": {"year": {"gte": 2010, "lte": 2020}}},
      {"range": {"rating": {"gte": 8.0}}}
    ]
  }
}
```

## 🚦 Интеграция с Catalog Service

1. Catalog Service создает/обновляет фильм
2. Публикует Kafka event в топик `catalog.movie.{created|updated|published}`
3. Search Service Consumer получает событие
4. Индексирует/обновляет документ в Elasticsearch
5. Инвалидирует Redis cache
6. Фильм сразу доступен для поиска

**Преимущества:**
- ✅ Real-time индексация
- ✅ Decoupled микросервисы
- ✅ Async обработка событий
- ✅ Fault tolerance (Kafka offsets)

## 📈 Performance

- **Autocomplete**: Edge N-gram для быстрого prefix matching
- **Caching**: Популярные запросы в Redis (TTL 5 мин)
- **Indexing**: Real-time через Kafka consumer
- **Search**: Elasticsearch distributed search
- **Pagination**: Offset-based pagination

## 🔧 Production Notes

1. **Elasticsearch cluster**: Используйте минимум 3 ноды с репликацией
2. **Kafka**: Настройте replication_factor ≥ 2
3. **Redis**: Используйте Redis Cluster или Sentinel для HA
4. **Monitoring**: Добавьте метрики (Prometheus, Grafana)
5. **Logging**: Централизованный логгинг (ELK, Loki)

## ✨ Итого

**Всего создано: 20+ файлов**

Search Service готов к использованию и включает:
- ✅ Полнотекстовый поиск с Elasticsearch
- ✅ Edge N-gram autocomplete
- ✅ Kafka consumer для real-time индексации
- ✅ Redis кэширование
- ✅ Продвинутые фильтры (genres, year, rating)
- ✅ Multi-match query с весами
- ✅ Nested queries для связанных данных
- ✅ Docker + Elasticsearch setup
- ✅ Полную документацию

Сервис готов к интеграции с catalog-service через Kafka и предоставляет мощный поисковый API!
