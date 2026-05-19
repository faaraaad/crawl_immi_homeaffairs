.PHONY: install lint test up down migrate crawl shell help

# Default target
help:
	@echo "Immi Crawler developer targets:"
	@echo "  make install  - Install dependencies and Playwright browser"
	@echo "  make lint     - Run Ruff and Mypy strict checks"
	@echo "  make test     - Execute pytest test suites"
	@echo "  make up       - Launch Postgres and Redis in docker-compose"
	@echo "  make down     - Tear down docker-compose stack"
	@echo "  make migrate  - Run alembic database migrations"
	@echo "  make crawl    - Dispatch full crawl run via Celery"

install:
	pip install -e .[dev]
	playwright install chromium
	playwright install-deps chromium

lint:
	ruff check src/
	mypy src/

test:
	pytest tests/ -v

up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	alembic upgrade head

crawl:
	immi-crawler crawl --sync
