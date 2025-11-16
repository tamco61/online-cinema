.PHONY: help up down restart logs ps clean test lint format migrate init-db seed-data

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

help: ## Show this help message
	@echo '${YELLOW}Online Cinema - Makefile Commands${RESET}'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${RESET} %s\n", $$1, $$2}'
	@echo ''

# ================================
# Docker Compose
# ================================

up: ## Start all infrastructure services
	@echo "${GREEN}Starting infrastructure services...${RESET}"
	docker-compose up -d
	@echo "${GREEN}Services started. Run 'make ps' to check status.${RESET}"

down: ## Stop all services
	@echo "${YELLOW}Stopping all services...${RESET}"
	docker-compose down

restart: ## Restart all services
	@echo "${YELLOW}Restarting services...${RESET}"
	docker-compose restart

logs: ## Show logs for all services
	docker-compose logs -f

ps: ## Show running containers
	docker-compose ps

clean: ## Remove all containers, volumes, and networks
	@echo "${YELLOW}Removing all containers, volumes, and networks...${RESET}"
	docker-compose down -v --remove-orphans
	@echo "${GREEN}Cleanup complete.${RESET}"

# ================================
# Database
# ================================

init-db: ## Initialize databases and run migrations
	@echo "${GREEN}Initializing databases...${RESET}"
	chmod +x scripts/init-multiple-databases.sh
	./scripts/init-db.sh

migrate: ## Run database migrations for all services
	@echo "${GREEN}Running migrations...${RESET}"
	./scripts/migrate.sh

seed-data: ## Seed databases with sample data
	@echo "${GREEN}Seeding sample data...${RESET}"
	python scripts/seed-data.py

# ================================
# Development
# ================================

test: ## Run all tests
	@echo "${GREEN}Running tests...${RESET}"
	pytest tests/ -v --cov=services

test-service: ## Run tests for specific service (usage: make test-service SERVICE=auth)
	@echo "${GREEN}Running tests for $(SERVICE) service...${RESET}"
	cd services/$(SERVICE)-service && pytest tests/ -v

lint: ## Run linters (ruff, mypy)
	@echo "${GREEN}Running linters...${RESET}"
	ruff check .
	mypy services/

format: ## Format code with black and isort
	@echo "${GREEN}Formatting code...${RESET}"
	black .
	isort .

# ================================
# Monitoring
# ================================

monitoring: ## Open monitoring dashboards
	@echo "${GREEN}Opening monitoring dashboards...${RESET}"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Jaeger: http://localhost:16686"
	@echo "Kibana: http://localhost:5601"
	@echo "Kafka UI: http://localhost:8080"

# ================================
# Infrastructure
# ================================

infra-check: ## Check health of all infrastructure services
	@echo "${GREEN}Checking infrastructure health...${RESET}"
	@docker-compose ps | grep -E "(postgres|redis|kafka|elasticsearch|clickhouse|minio)" || echo "${YELLOW}Some services are not running${RESET}"

infra-restart: ## Restart infrastructure services
	docker-compose restart postgres redis kafka zookeeper elasticsearch clickhouse minio

# ================================
# MinIO
# ================================

minio-console: ## Open MinIO console
	@echo "${GREEN}Opening MinIO console at http://localhost:9001${RESET}"
	@echo "Credentials: minioadmin / minioadmin123"

# ================================
# Kubernetes
# ================================

k8s-deploy: ## Deploy to Kubernetes
	@echo "${GREEN}Deploying to Kubernetes...${RESET}"
	kubectl apply -f infrastructure/k8s/

k8s-delete: ## Delete Kubernetes resources
	kubectl delete -f infrastructure/k8s/

k8s-logs: ## Show Kubernetes logs (usage: make k8s-logs SERVICE=catalog-service)
	kubectl logs -f deployment/$(SERVICE) --tail=100

# ================================
# Utilities
# ================================

shell-postgres: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U cinema -d cinema

shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli -a redis123

shell-kafka: ## Open Kafka container shell
	docker-compose exec kafka bash

env-setup: ## Copy .env.example to .env
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "${GREEN}.env file created from .env.example${RESET}"; \
	else \
		echo "${YELLOW}.env file already exists${RESET}"; \
	fi

# ================================
# Default
# ================================

.DEFAULT_GOAL := help
