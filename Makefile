.PHONY: test test-db test-up test-down test-clean

# Start test database
test-up:
	docker-compose up -d postgres-test
	@echo "Waiting for test database to be ready..."
	@sleep 3
	@docker-compose exec -T postgres-test pg_isready -U postgres || (sleep 2 && docker-compose exec -T postgres-test pg_isready -U postgres)

# Stop test database
test-down:
	docker-compose down postgres-test

# Clean test database (remove volumes)
test-clean:
	docker-compose down postgres-test -v

# Run tests with PostgreSQL
test: test-up
	/usr/local/bin/python3.12 -m pytest tests/ -v
	$(MAKE) test-down

# Run tests and keep database running
test-db:
	/usr/local/bin/python3.12 -m pytest tests/ -v

# Start both dev and test databases
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Run development server
dev:
	/usr/local/bin/python3.12 -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
install:
	/usr/local/bin/python3.12 -m pip install -e ".[dev]"

# Run linting
lint:
	/usr/local/bin/python3.12 -m ruff check src/ tests/

# Format code
format:
	/usr/local/bin/python3.12 -m ruff check --fix src/ tests/
