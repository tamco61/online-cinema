.PHONY: help install run docker-build docker-up docker-down test clean

help:
	@echo "Analytics Service - Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run service locally"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start all services with docker-compose"
	@echo "  make docker-down  - Stop all services"
	@echo "  make test         - Run tests"
	@echo "  make test-events  - Generate test events"
	@echo "  make logs         - Show service logs"
	@echo "  make clean        - Clean temporary files"

install:
	pip install -r requirements.txt

run:
	python -m app.main

docker-build:
	docker build -t analytics-service .

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services are ready!"
	@echo "Analytics Service: http://localhost:8006"
	@echo "ClickHouse HTTP: http://localhost:8123"
	@echo "API Docs: http://localhost:8006/docs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f analytics-service

logs:
	docker-compose logs -f

test:
	pytest

test-events:
	python test_events.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
