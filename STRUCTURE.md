# Online Cinema - Repository Structure

```
online-cinema/
├── .github/
│   └── workflows/                # CI/CD pipelines (GitHub Actions)
│
├── api-gateway/
│   ├── kong/                    # Kong API Gateway configs
│   └── nginx/                   # NGINX configs
│       └── conf.d/
│
├── docs/
│   ├── api/                     # OpenAPI specifications
│   ├── architecture/            # Architecture Decision Records (ADRs)
│   └── runbooks/                # Operational guides
│
├── etl/
│   ├── airflow/                 # Apache Airflow
│   │   ├── config/
│   │   ├── dags/               # DAG definitions
│   │   └── plugins/            # Custom operators
│   └── celery-workers/          # Background task workers
│       └── tasks/
│
├── infrastructure/
│   ├── docker/                  # Docker configs
│   ├── k8s/                     # Kubernetes manifests
│   │   ├── configmaps/
│   │   ├── deployments/
│   │   ├── ingress/
│   │   ├── secrets/
│   │   └── services/
│   ├── monitoring/              # Observability stack
│   │   ├── elk/
│   │   ├── grafana/
│   │   │   ├── dashboards/
│   │   │   └── datasources/
│   │   ├── jaeger/
│   │   ├── pgadmin/
│   │   ├── prometheus/
│   │   └── clickhouse/
│   └── terraform/               # Infrastructure as Code
│       ├── aws/
│       └── gcp/
│
├── scripts/                     # Utility scripts
│   ├── init-db.sh
│   ├── init-multiple-databases.sh
│   ├── migrate.sh
│   └── seed-data.py
│
├── services/                    # Microservices
│   ├── analytics-service/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── endpoints/
│   │   │   │   │   └── router.py
│   │   │   │   └── deps.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py
│   │   │   │   └── middleware.py
│   │   │   ├── db/
│   │   │   │   ├── models.py
│   │   │   │   ├── repositories.py
│   │   │   │   └── session.py
│   │   │   ├── schemas/
│   │   │   ├── services/
│   │   │   ├── utils/
│   │   │   │   ├── metrics.py
│   │   │   │   └── tracing.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── auth-service/            # Authentication & JWT
│   │   └── [similar structure]
│   │
│   ├── catalog-service/         # Movie metadata CRUD
│   │   └── [similar structure]
│   │
│   ├── notification-service/    # Email/Push notifications
│   │   └── [similar structure]
│   │
│   ├── payment-service/         # Payment processing
│   │   └── [similar structure]
│   │
│   ├── recommendation-service/  # ML recommendations
│   │   └── [similar structure]
│   │
│   ├── search-service/          # Elasticsearch integration
│   │   └── [similar structure]
│   │
│   ├── streaming-service/       # Video streaming
│   │   └── [similar structure]
│   │
│   └── user-service/            # User profiles & subscriptions
│       └── [similar structure]
│
├── shared/                      # Shared libraries
│   ├── proto/                  # Protocol Buffers (gRPC)
│   └── python-common/          # Common Python utilities
│       ├── middleware/
│       │   ├── correlation_id.py
│       │   ├── error_handler.py
│       │   └── rate_limiter.py
│       └── utils/
│           ├── logger.py
│           ├── metrics.py
│           └── tracer.py
│
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── ARCHITECTURE.md              # Architecture documentation
├── docker-compose.yml           # Infrastructure services
├── Makefile                     # Development commands
├── README.md                    # Project overview
└── STRUCTURE.md                 # This file
```

## Service Count: 9 Microservices

1. **auth-service** - Authentication & Authorization
2. **user-service** - User Management
3. **catalog-service** - Movie Catalog
4. **search-service** - Search Engine
5. **streaming-service** - Video Streaming
6. **analytics-service** - Data Analytics
7. **recommendation-service** - ML Recommendations
8. **payment-service** - Payments
9. **notification-service** - Notifications

## Infrastructure Components

- PostgreSQL (Primary database)
- Redis (Cache & Sessions)
- Kafka + Zookeeper (Message broker)
- Elasticsearch (Search engine)
- ClickHouse (Analytics DB)
- MinIO (S3-compatible storage)
- Prometheus (Metrics)
- Grafana (Dashboards)
- Jaeger (Distributed tracing)
- Kibana (Log visualization)
