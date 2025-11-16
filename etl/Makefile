.PHONY: help build up down restart logs clean test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services started!"
	@echo "Airflow UI: http://localhost:8080"
	@echo "Flower: http://localhost:5555"

down: ## Stop all services
	docker-compose down

restart: down up ## Restart all services

logs: ## Show logs from all services
	docker-compose logs -f

logs-airflow: ## Show Airflow webserver logs
	docker-compose logs -f airflow-webserver

logs-scheduler: ## Show Airflow scheduler logs
	docker-compose logs -f airflow-scheduler

logs-transcoding: ## Show transcoding worker logs
	docker-compose logs -f celery-worker-transcoding

logs-thumbnails: ## Show thumbnails worker logs
	docker-compose logs -f celery-worker-thumbnails

logs-indexing: ## Show indexing worker logs
	docker-compose logs -f celery-worker-indexing

ps: ## Show running containers
	docker-compose ps

clean: ## Remove volumes and containers
	docker-compose down -v
	rm -rf airflow/logs/*

shell-scheduler: ## Open shell in scheduler container
	docker exec -it etl-airflow-scheduler bash

shell-worker: ## Open shell in transcoding worker
	docker exec -it etl-celery-transcoding bash

trigger-sync: ## Trigger catalog sync DAG
	docker exec etl-airflow-scheduler airflow dags trigger sync_catalog_to_elasticsearch

trigger-metadata: ## Trigger metadata fetch DAG
	docker exec etl-airflow-scheduler airflow dags trigger fetch_external_metadata

trigger-transcoding: ## Trigger transcoding DAG
	docker exec etl-airflow-scheduler airflow dags trigger video_transcoding

list-dags: ## List all DAGs
	docker exec etl-airflow-scheduler airflow dags list

test: ## Run tests (placeholder)
	@echo "No tests configured yet"

init: ## Initialize environment
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created. Please edit it with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi
