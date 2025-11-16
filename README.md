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

- **Microservices Architecture** - 8 independent services with clear responsibilities ✅
- **Elastic Search** - Fast full-text search across movie catalog ✅
- **Video Streaming** - Adaptive bitrate streaming (HLS/DASH) with CDN support ✅
- **Real-time Analytics** - User behavior tracking with ClickHouse ✅
- **Payment Integration** - YooMoney integration with idempotency ✅
- **Notifications** - Email (SendGrid/AWS SES) and Push (FCM) ✅
- **Event-Driven** - Apache Kafka for async communication and event sourcing ✅
- **Observability** - Complete monitoring, logging, and distributed tracing ✅
- **ETL Pipeline** - Apache Airflow + Celery for video transcoding ✅
- **API Gateway** - NGINX + Kong with JWT auth, rate limiting ✅

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
├── services/                    # Microservices (✅ All Implemented)
│   ├── auth-service/           # Authentication & JWT ✅
│   ├── user-service/           # User profiles & subscriptions ✅
│   ├── catalog-service/        # Movie metadata CRUD ✅
│   ├── search-service/         # Elasticsearch integration ✅
│   ├── streaming-service/      # Video streaming & access control ✅
│   ├── analytics-service/      # Event collection & ClickHouse ✅
│   ├── payment-service/        # YooMoney integration ✅
│   └── notification-service/   # Email/Push notifications ✅
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

> **🚀 TL;DR**: Complete platform setup in 3 commands!

```bash
cd infrastructure
make init    # Initialize environment
make up      # Start everything (infrastructure + all 8 microservices)
make health-check  # Verify (wait 2-3 min after start)
```

📖 **Detailed guide**: [infrastructure/QUICKSTART.md](infrastructure/QUICKSTART.md)

### Prerequisites

- ✅ **Docker Desktop** (or Docker Engine + Docker Compose)
- ✅ **8GB RAM minimum** (12GB recommended)
- ✅ **20GB free disk space**
- ✅ **Make** (optional, but recommended)

### What Gets Started

**Infrastructure (12 components)**:
- PostgreSQL, Redis, ClickHouse, Elasticsearch
- Kafka + Zookeeper
- MinIO (S3-compatible storage)
- NGINX + Kong (API Gateway)
- Prometheus + Grafana (Monitoring)
- Jaeger (Distributed Tracing)
- ELK Stack (Logging)

**Microservices (8 services)**:
- ✅ auth-service → http://localhost:8001
- ✅ user-service → http://localhost:8002
- ✅ catalog-service → http://localhost:8003
- ✅ search-service → http://localhost:8004
- ✅ streaming-service → http://localhost:8005
- ✅ analytics-service → http://localhost:8006
- ✅ payment-service → http://localhost:8007
- ✅ notification-service → http://localhost:8008

### Access Points After Start

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Gateway** | http://localhost | - |
| **Kong Admin** | http://localhost:8001 | - |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger** | http://localhost:16686 | - |
| **Kibana** | http://localhost:5601 | - |
| **MinIO Console** | http://localhost:9001 | minio/minio_dev_password |

### Quick Health Check

```bash
# Check all services
make health-check

# Or manually
curl http://localhost/health                # NGINX
curl http://localhost:8001/status           # Kong
curl http://localhost:8003/health          # Catalog service
curl http://localhost:8006/health          # Analytics service
```

### Useful Commands

```bash
make status              # Show container status
make logs                # View all logs
make logs-service SERVICE=catalog-service  # Service-specific logs
make down                # Stop everything
make clean-volumes       # Clean all data (CAUTION!)

# Monitoring
make open-grafana        # Open Grafana in browser
make open-prometheus     # Open Prometheus
make open-jaeger         # Open Jaeger
```

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

Each service exposes auto-generated OpenAPI docs (Swagger UI):

| Service | Swagger UI | Description |
|---------|-----------|-------------|
| Auth | http://localhost:8001/docs | Login, register, JWT tokens |
| User | http://localhost:8002/docs | User profiles, subscriptions |
| Catalog | http://localhost:8003/docs | Movies, genres, actors |
| Search | http://localhost:8004/docs | Full-text search |
| Streaming | http://localhost:8005/docs | Video URLs, access control |
| Analytics | http://localhost:8006/docs | Viewing events, statistics |
| Payment | http://localhost:8007/docs | Subscriptions, invoices |
| Notification | http://localhost:8008/docs | Send notifications |

### Example API Usage

```bash
# Register user
curl -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Login
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Get movies (through API Gateway)
curl http://localhost/api/v1/catalog/movies?page=1&limit=10

# Search movies
curl http://localhost/api/v1/search?q=inception

# Get streaming URL (with JWT)
curl http://localhost/api/v1/stream/movies/123/hls \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

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

### Phase 1: Core Platform ✅ (COMPLETED)
- [x] Microservices architecture design
- [x] Infrastructure setup (Docker Compose)
- [x] Implement all 8 microservices
  - [x] auth-service (JWT, refresh tokens)
  - [x] user-service (profiles, subscriptions)
  - [x] catalog-service (movies CRUD, genres, actors)
  - [x] search-service (Elasticsearch integration)
  - [x] streaming-service (HLS/DASH, access control)
  - [x] analytics-service (ClickHouse, real-time events)
  - [x] payment-service (YooMoney, idempotency)
  - [x] notification-service (Email/Push, Kafka consumers)
- [x] API Gateway (NGINX + Kong)
- [x] ETL Pipeline (Airflow + Celery)
- [x] Monitoring stack (Prometheus, Grafana, Jaeger, ELK)

### Phase 2: Deployment & CI/CD ✅ (COMPLETED)
- [x] Kubernetes deployment manifests
- [x] HPA (Horizontal Pod Autoscaler)
- [x] Ingress configuration
- [x] ConfigMaps and Secrets management
- [x] CI/CD pipelines (GitHub Actions)
  - [x] CI: Lint, test, security scan, build
  - [x] CD: Deploy to staging/production

### Phase 3: Production Ready 🚧 (IN PROGRESS)
- [ ] Load testing (Locust/k6)
- [ ] Security audit (OWASP, penetration testing)
- [ ] Performance optimization
- [ ] Documentation completion
- [ ] Runbooks and playbooks

### Phase 4: Advanced Features 📋 (PLANNED)
- [ ] ML-based recommendations (TensorFlow/PyTorch)
- [ ] Mobile app integration (iOS/Android)
- [ ] Multi-region deployment (CDN, geo-routing)
- [ ] A/B testing framework
- [ ] Real-time chat/comments
- [ ] Social features (sharing, ratings)

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## Documentation

### Getting Started
- 📖 [Quick Start Guide](infrastructure/QUICKSTART.md) - Get running in 5 minutes
- 📖 [Infrastructure README](infrastructure/README.md) - Complete infrastructure documentation
- 📖 [ETL Documentation](etl/README.md) - Airflow & Celery pipelines
- 📖 [API Gateway Guide](api-gateway/README.md) - NGINX + Kong setup

### Service Documentation
Each microservice has its own README with API documentation:
- [auth-service](services/auth-service/README.md)
- [user-service](services/user-service/README.md)
- [catalog-service](services/catalog-service/README.md)
- [search-service](services/search-service/README.md)
- [streaming-service](services/streaming-service/README.md)
- [analytics-service](services/analytics-service/README.md)
- [payment-service](services/payment-service/README.md)
- [notification-service](services/notification-service/README.md)

## Support

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
