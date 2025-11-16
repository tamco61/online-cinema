# Online Cinema - Microservices Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-latest-blue.svg" alt="Docker">
  <img src="https://img.shields.io/badge/Kubernetes-1.28+-326CE5.svg" alt="Kubernetes">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

## Overview

Scalable microservices-based online cinema platform built with modern Python stack. Designed to handle millions of concurrent users with high availability and performance.

### Key Features

- **Microservices Architecture** - 9 independent services with clear responsibilities
- **Elastic Search** - Fast full-text search across movie catalog
- **Video Streaming** - Adaptive bitrate streaming (HLS/DASH) with CDN support
- **Real-time Analytics** - User behavior tracking and business intelligence
- **Recommendations** - ML-powered personalized content suggestions
- **Event-Driven** - Apache Kafka for async communication and event sourcing
- **Observability** - Complete monitoring, logging, and distributed tracing

---

## Architecture

```
┌─────────────┐
│   Clients   │  (Web, Mobile, Smart TV)
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────────┐
│         NGINX + Kong API Gateway                │
└──────┬──────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────┐
│              Microservices Layer                │
│  ┌──────────┬──────────┬────────────┬─────────┐ │
│  │   Auth   │   User   │  Catalog   │ Search  │ │
│  ├──────────┼──────────┼────────────┼─────────┤ │
│  │Streaming │Analytics │Recommend.  │ Payment │ │
│  └──────────┴──────────┴────────────┴─────────┘ │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│             Data & Message Layer                │
│  PostgreSQL │ Redis │ Elasticsearch │ Kafka    │
│  ClickHouse │ MinIO (S3) │ Zookeeper           │
└─────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed design.

---

## Tech Stack

### Backend
- **Framework**: FastAPI 0.104+ (async, type hints, auto OpenAPI docs)
- **Language**: Python 3.11+
- **Validation**: Pydantic v2
- **ORM**: SQLAlchemy 2.0 + Alembic (migrations)
- **Testing**: pytest + pytest-asyncio + httpx

### Databases & Storage
- **Primary DB**: PostgreSQL 15 (ACID transactions, JSONB support)
- **Cache**: Redis 7 (sessions, rate limiting, hot data)
- **Search**: Elasticsearch 8 (full-text search, aggregations)
- **Analytics**: ClickHouse (OLAP, time-series)
- **Object Storage**: MinIO (S3-compatible, video files)

### Message Broker
- **Event Streaming**: Apache Kafka 3.5+
- **Coordination**: Zookeeper (for Kafka)

### ETL & Background Jobs
- **Orchestration**: Apache Airflow 2.7+
- **Task Queue**: Celery 5.3+ (async workers)
- **Broker**: Redis (Celery backend)

### API Gateway & Load Balancing
- **Reverse Proxy**: NGINX
- **API Gateway**: Kong (rate limiting, auth, plugins)

### Monitoring & Observability
- **Metrics**: Prometheus + Grafana
- **Tracing**: Jaeger (OpenTelemetry)
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **APM**: Sentry (error tracking)

### Infrastructure
- **Containerization**: Docker 24+ / Docker Compose
- **Orchestration**: Kubernetes 1.28+
- **IaC**: Terraform (AWS/GCP)
- **CI/CD**: GitHub Actions

---

## Repository Structure

```
online-cinema/
├── services/                    # Microservices
│   ├── auth-service/           # Authentication & JWT
│   ├── user-service/           # User profiles & subscriptions
│   ├── catalog-service/        # Movie metadata CRUD
│   ├── search-service/         # Elasticsearch integration
│   ├── streaming-service/      # Video streaming & access control
│   ├── analytics-service/      # Event collection & ClickHouse
│   ├── recommendation-service/ # ML-based recommendations
│   ├── payment-service/        # Stripe/PayPal integration
│   └── notification-service/   # Email/Push notifications
│
├── etl/                        # Data pipelines
│   ├── airflow/               # DAGs & workflows
│   └── celery-workers/        # Background tasks (transcoding, etc.)
│
├── api-gateway/               # Entry point
│   ├── nginx/                # Load balancer
│   └── kong/                 # API gateway
│
├── infrastructure/           # Deployment configs
│   ├── docker/              # Docker Compose files
│   ├── k8s/                 # Kubernetes manifests
│   ├── terraform/           # IaC for AWS/GCP
│   └── monitoring/          # Prometheus, Grafana, Jaeger configs
│
├── shared/                  # Shared libraries
│   ├── python-common/      # Middleware, utils, logging
│   └── proto/              # Protocol Buffers (if using gRPC)
│
├── docs/                   # Documentation
│   ├── api/               # OpenAPI specs
│   ├── architecture/      # ADRs, diagrams
│   └── runbooks/          # Operational guides
│
├── scripts/               # Utility scripts
│   ├── init-db.sh
│   ├── migrate.sh
│   └── seed-data.py
│
├── .github/
│   └── workflows/         # CI/CD pipelines
│
├── docker-compose.yml     # Local development environment
├── .env.example          # Environment variables template
├── README.md             # This file
└── ARCHITECTURE.md       # Detailed architecture docs
```

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose 2.20+
- Python 3.11+
- Make (optional, for convenience)
- 16GB RAM recommended (for running all services locally)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/online-cinema.git
cd online-cinema
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# vim .env
```

### 3. Start Infrastructure

Start PostgreSQL, Redis, Kafka, Elasticsearch, ClickHouse, MinIO:

```bash
docker-compose up -d
```

Verify all services are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
postgres            Up (healthy)        5432
redis               Up (healthy)        6379
kafka               Up (healthy)        9092
zookeeper           Up (healthy)        2181
elasticsearch       Up (healthy)        9200, 9300
clickhouse          Up (healthy)        8123, 9000
minio               Up (healthy)        9000, 9001
```

### 4. Initialize Databases

```bash
# Run migrations
./scripts/init-db.sh

# Seed sample data (optional)
python scripts/seed-data.py
```

### 5. Start Microservices (Development)

Each service can be run independently:

```bash
# Example: Auth Service
cd services/auth-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Example: Catalog Service
cd services/catalog-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

Or use Docker Compose for all services (coming soon):

```bash
docker-compose -f docker-compose.services.yml up
```

### 6. Access Services

| Service              | URL                          | Credentials       |
|----------------------|------------------------------|-------------------|
| PostgreSQL           | localhost:5432               | cinema/cinema     |
| Redis                | localhost:6379               | -                 |
| Kafka                | localhost:9092               | -                 |
| Elasticsearch        | http://localhost:9200        | -                 |
| ClickHouse           | http://localhost:8123        | default/(empty)   |
| MinIO Console        | http://localhost:9001        | minioadmin/...    |
| Prometheus           | http://localhost:9090        | -                 |
| Grafana              | http://localhost:3000        | admin/admin       |
| Jaeger UI            | http://localhost:16686       | -                 |
| Kibana               | http://localhost:5601        | -                 |

---

## Development

### Running Tests

```bash
# All services
pytest

# Specific service
cd services/auth-service
pytest tests/ -v --cov=app

# Integration tests
pytest tests/integration/ -v
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy services/

# Formatting
black .
isort .
```

### Database Migrations

```bash
# Create new migration
cd services/catalog-service
alembic revision --autogenerate -m "Add movies table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding a New Service

```bash
# Use cookiecutter template
cookiecutter templates/fastapi-service

# Follow the prompts to generate boilerplate
```

---

## Deployment

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f infrastructure/k8s/

# Check rollout status
kubectl rollout status deployment/catalog-service

# View logs
kubectl logs -f deployment/catalog-service --tail=100
```

### Terraform (AWS)

```bash
cd infrastructure/terraform/aws

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

---

## Monitoring

### Metrics (Prometheus + Grafana)

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

Pre-configured dashboards:
- Service Health (CPU, Memory, RPS)
- Database Performance
- Kafka Lag
- Business KPIs (concurrent users, streaming quality)

### Distributed Tracing (Jaeger)

- **Jaeger UI**: http://localhost:16686

Trace requests across all microservices:
1. Search for service (e.g., `catalog-service`)
2. View span details and dependencies
3. Analyze latency bottlenecks

### Logs (ELK Stack)

- **Kibana**: http://localhost:5601

Centralized logging with structured JSON:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "catalog-service",
  "level": "INFO",
  "trace_id": "abc123",
  "message": "Movie fetched successfully",
  "movie_id": 42
}
```

---

## API Documentation

Each service exposes auto-generated OpenAPI docs:

- Auth Service: http://localhost:8001/docs
- Catalog Service: http://localhost:8002/docs
- Search Service: http://localhost:8003/docs
- Streaming Service: http://localhost:8004/docs

Interactive Swagger UI for testing endpoints.

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(catalog): add movie rating endpoint
fix(auth): resolve JWT expiration bug
docs: update README with deployment instructions
refactor(streaming): optimize video URL generation
```

---

## Roadmap

- [x] Microservices architecture design
- [x] Infrastructure setup (Docker Compose)
- [ ] Implement all 9 microservices
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipelines (GitHub Actions)
- [ ] Load testing (Locust)
- [ ] Security audit (OWASP)
- [ ] Mobile app integration
- [ ] ML-based recommendations (TensorFlow)
- [ ] Multi-region deployment

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/online-cinema/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/online-cinema/discussions)
- **Email**: devops@cinema.example.com

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Inspired by Netflix, Spotify, and Uber architectures
- Special thanks to the open-source community

---

**Made with ❤️ by the Online Cinema Team**
