.PHONY: help install run test lint format clean docker-build docker-run

help: ## Show this help message
	@echo 'Cinema Service - Available Commands:'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Run development server
	uvicorn app.main:app --reload --port 8000

test: ## Run tests
	pytest tests/ -v --cov=app --cov-report=term-missing

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -v

lint: ## Run linters
	ruff check .
	mypy app

format: ## Format code
	black .
	ruff check --fix .

clean: ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -f .coverage

docker-build: ## Build Docker image
	docker build -t cinema-service:latest -f Dockerfile ../..

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env cinema-service:latest

db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback database migration
	alembic downgrade -1

db-init: ## Initialize Alembic
	alembic init alembic
