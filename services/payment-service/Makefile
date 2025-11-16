.PHONY: help install run docker-build docker-up docker-down migrate test clean

help:
	@echo "Payment Service - Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make run            - Run service locally"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-up      - Start all services with docker-compose"
	@echo "  make docker-down    - Stop all services"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migration      - Create new migration (use MSG='message')"
	@echo "  make test           - Run tests"
	@echo "  make logs           - Show service logs"
	@echo "  make clean          - Clean temporary files"

install:
	pip install -r requirements.txt

run:
	python -m app.main

docker-build:
	docker build -t payment-service .

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services are ready!"
	@echo "Payment Service: http://localhost:8007"
	@echo "API Docs: http://localhost:8007/docs"
	@echo "Adminer: http://localhost:8080"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f payment-service

logs:
	docker-compose logs -f

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(MSG)"

test:
	pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
