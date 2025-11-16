# ETL Service - Online Cinema Platform

ETL (Extract, Transform, Load) system для онлайн-кинотеатра, построенный на Apache Airflow и Celery.

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        ETL System                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────────────────────────┐  │
│  │   Airflow    │         │      Celery Workers              │  │
│  │              │         │                                  │  │
│  │  - Scheduler │────────▶│  - Transcoding (2 workers)      │  │
│  │  - Webserver │         │  - Thumbnails (4 workers)       │  │
│  │  - Worker    │         │  - Indexing (4 workers)         │  │
│  └──────┬───────┘         └────────────┬─────────────────────┘  │
│         │                              │                         │
│         ▼                              ▼                         │
│  ┌──────────────┐         ┌──────────────────────────────────┐  │
│  │  PostgreSQL  │         │         Redis                    │  │
│  │  (Metadata)  │         │  (Broker + Result Backend)       │  │
│  └──────────────┘         └──────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐         ┌──────────────────────────────────┐
│  Catalog DB     │         │    External Services              │
│  (PostgreSQL)   │         │  - S3 (video storage)            │
│  - Movies       │         │  - Elasticsearch (search)        │
│  - Videos       │         │  - TMDb API (metadata)           │
└─────────────────┘         └──────────────────────────────────┘
```

## Компоненты

### Airflow DAGs

1. **sync_catalog_to_elasticsearch.py**
   - Расписание: Каждый час
   - Функция: Синхронизация каталога фильмов в Elasticsearch
   - Процесс:
     - Извлечение фильмов из PostgreSQL
     - Трансформация данных
     - Загрузка в Elasticsearch
     - Верификация синхронизации

2. **fetch_external_metadata.py**
   - Расписание: Ежедневно в 2:00
   - Функция: Обновление метаданных фильмов из TMDb
   - Процесс:
     - Поиск фильмов без метаданных или с устаревшими данными
     - Запросы к TMDb API
     - Обновление базы данных

3. **video_transcoding.py**
   - Расписание: Каждые 10 минут
   - Функция: Планирование задач транскодинга
   - Процесс:
     - Поиск загруженных видео
     - Создание Celery задач для транскодинга
     - Создание Celery задач для генерации превью
     - Мониторинг выполнения

### Celery Tasks

1. **transcoding.py**
   - Очередь: `transcoding`
   - Конкурентность: 2 воркера
   - Функции:
     - Транскодинг в HLS/DASH форматы
     - Генерация плейлистов
     - Множественные разрешения (1080p, 720p, 480p, 360p)

2. **thumbnails.py**
   - Очередь: `thumbnails`
   - Конкурентность: 4 воркера
   - Функции:
     - Извлечение кадров из видео
     - Генерация анимированных превью (GIF)
     - Оптимизация изображений

3. **indexing.py**
   - Очередь: `indexing`
   - Конкурентность: 4 воркера
   - Функции:
     - Индексация фильмов в Elasticsearch
     - Массовая индексация
     - Полная переиндексация

## Установка и запуск

### Предварительные требования

- Docker и Docker Compose
- Минимум 4GB RAM
- Подключение к внешним сервисам (PostgreSQL, Elasticsearch, S3)

### Шаги установки

1. **Клонирование репозитория**
   ```bash
   cd etl/
   ```

2. **Конфигурация окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл с вашими настройками
   ```

3. **Запуск сервисов**
   ```bash
   docker-compose up -d
   ```

4. **Проверка статуса**
   ```bash
   docker-compose ps
   ```

5. **Доступ к интерфейсам**
   - Airflow UI: http://localhost:8080 (admin/admin)
   - Flower (Celery monitoring): http://localhost:5555

## Конфигурация

### Подключение к PostgreSQL (Catalog DB)

В Airflow UI создайте Connection:
- **Conn Id**: `catalog_postgres`
- **Conn Type**: `Postgres`
- **Host**: `catalog-postgres`
- **Schema**: `catalog`
- **Login**: `catalog`
- **Password**: `catalog_password`
- **Port**: `5432`

### Подключение к Elasticsearch

В Airflow UI создайте Connection:
- **Conn Id**: `elasticsearch_default`
- **Conn Type**: `Elasticsearch`
- **Host**: `elasticsearch`
- **Port**: `9200`
- **Login**: `elastic` (опционально)
- **Password**: `changeme` (опционально)

### Переменные Airflow

Создайте следующие Variables в Airflow UI:

```python
{
  "tmdb_api_key": "your-tmdb-api-key",
  "s3_bucket": "cinema-videos",
  "elasticsearch_movies_index": "movies"
}
```

### AWS Credentials

Для работы с S3 создайте AWS Connection:
- **Conn Id**: `aws_default`
- **Conn Type**: `Amazon Web Services`
- **AWS Access Key ID**: `your-access-key`
- **AWS Secret Access Key**: `your-secret-key`
- **Region Name**: `us-east-1`

## Использование

### Запуск DAG вручную

```bash
# Через CLI
docker exec etl-airflow-scheduler airflow dags trigger sync_catalog_to_elasticsearch

# Или через Web UI
# Airflow UI -> DAGs -> Выберите DAG -> Trigger DAG
```

### Отправка Celery задачи вручную

```python
from celery import Celery

app = Celery('etl_tasks', broker='redis://localhost:6379/0')

# Транскодинг видео
result = app.send_task(
    'tasks.transcoding.transcode_video',
    kwargs={
        'video_id': 'video-uuid',
        'movie_id': 'movie-uuid',
        's3_key': 'uploads/video.mp4',
        'original_file_path': '/path/to/video.mp4'
    },
    queue='transcoding'
)

print(f"Task ID: {result.id}")
```

### Мониторинг задач

1. **Airflow Tasks**
   - Web UI: http://localhost:8080
   - Логи: `./airflow/logs/`

2. **Celery Tasks**
   - Flower: http://localhost:5555
   - Логи: Docker logs

```bash
# Просмотр логов конкретного воркера
docker logs -f etl-celery-transcoding
docker logs -f etl-celery-thumbnails
docker logs -f etl-celery-indexing
```

## Разработка

### Структура проекта

```
etl/
├── airflow/
│   ├── dags/
│   │   ├── sync_catalog_to_elasticsearch.py
│   │   ├── fetch_external_metadata.py
│   │   └── video_transcoding.py
│   ├── logs/
│   └── plugins/
├── celery-workers/
│   ├── tasks/
│   │   ├── transcoding.py
│   │   ├── thumbnails.py
│   │   └── indexing.py
│   ├── celeryconfig.py
│   └── worker.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Добавление нового DAG

1. Создайте файл в `airflow/dags/`
2. Определите DAG и задачи
3. DAG будет автоматически обнаружен Airflow

Пример:
```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data-team',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

dag = DAG(
    'my_new_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
)

def my_task():
    print("Running my task")

task = PythonOperator(
    task_id='my_task',
    python_callable=my_task,
    dag=dag,
)
```

### Добавление новой Celery задачи

1. Создайте файл в `celery-workers/tasks/`
2. Определите функции задач
3. Обновите `celeryconfig.py` (imports)
4. Перезапустите воркеры

## Производственные рекомендации

### Безопасность

- Измените дефолтные пароли в `.env`
- Используйте секреты для API ключей
- Настройте SSL/TLS для Airflow UI
- Ограничьте доступ к Flower

### Масштабирование

- Увеличьте количество воркеров в `docker-compose.yml`
- Используйте отдельные очереди для разных типов задач
- Настройте автоскейлинг на основе длины очереди

### Мониторинг

- Настройте алерты в Airflow (email_on_failure)
- Интегрируйте с Prometheus/Grafana
- Мониторьте использование диска для временных файлов

### Резервное копирование

- Регулярное бэкапирование Airflow metadata DB
- Бэкап DAG файлов в Git
- Логирование в централизованную систему

## Troubleshooting

### Airflow не запускается

```bash
# Проверьте логи
docker logs etl-airflow-webserver

# Инициализируйте БД вручную
docker exec etl-airflow-webserver airflow db init
```

### Celery задачи не выполняются

```bash
# Проверьте подключение к Redis
docker exec etl-redis redis-cli ping

# Проверьте очереди
docker exec etl-flower celery -A worker inspect active_queues
```

### Недостаточно места для видео

```bash
# Очистите временные файлы
docker exec etl-celery-transcoding rm -rf /tmp/videos/*
docker exec etl-celery-thumbnails rm -rf /tmp/thumbnails/*
```

## Производительность

### Оптимизация транскодинга

- Используйте GPU для ускорения FFmpeg
- Настройте `preset` в зависимости от требований (fast/medium/slow)
- Уменьшите количество разрешений для экономии ресурсов

### Оптимизация Elasticsearch

- Используйте bulk indexing
- Настройте refresh_interval
- Оптимизируйте маппинги

## Лицензия

Проприетарный код для онлайн-кинотеатра.
