# Makefile for UW Scanner
# Common commands for development and deployment

.PHONY: help install test clean docker-up docker-down db-init run-examples

# Default target
help:
	@echo "UW Scanner - Available Commands:"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run API connection tests"
	@echo "  make test-full    - Run full test suite"
	@echo "  make docker-up    - Start PostgreSQL and Redis"
	@echo "  make docker-down  - Stop databases"
	@echo "  make docker-tools - Start databases + GUI tools"
	@echo "  make db-init      - Initialize database tables"
	@echo "  make run-examples - Run usage examples"
	@echo "  make clean        - Clean cache and temp files"
	@echo "  make logs         - Show recent logs"
	@echo "  make shell        - Open Python shell with imports"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Run API connection test
test:
	@echo "Testing API connection..."
	python tests/test_api.py

# Run full test suite
test-full:
	@echo "Running full test suite..."
	pytest tests/ -v --cov=.

# Start Docker services (databases only)
docker-up:
	@echo "Starting PostgreSQL and Redis..."
	docker-compose up -d postgres redis
	@echo "✓ Databases started"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

# Start Docker services with GUI tools
docker-tools:
	@echo "Starting all services including GUI tools..."
	docker-compose --profile tools up -d
	@echo "✓ All services started"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"
	@echo "pgAdmin: http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"

# Stop Docker services
docker-down:
	@echo "Stopping all services..."
	docker-compose down
	@echo "✓ Services stopped"

# Initialize database
db-init:
	@echo "Initializing database..."
	python -c "import asyncio; from database import db_manager; asyncio.run(db_manager.initialize()); asyncio.run(db_manager.create_tables())"
	@echo "✓ Database initialized"

# Run usage examples
run-examples:
	@echo "Running usage examples..."
	python examples/basic_usage.py

# Clean cache and temporary files
clean:
	@echo "Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

# Show recent logs
logs:
	@echo "Recent logs (last 50 lines):"
	@tail -n 50 logs/scanner.log 2>/dev/null || echo "No logs yet"

# Open Python shell with imports
shell:
	@echo "Opening Python shell..."
	@python -i -c "import asyncio; from api.client import UWClient; from api.websocket_client import UWWebSocketClient; from database import db_manager; from config.settings import settings; print('Imports loaded: UWClient, UWWebSocketClient, db_manager, settings, asyncio')"

# Development mode - watch for changes
dev:
	@echo "Starting development mode..."
	watchmedo auto-restart --directory=. --pattern="*.py" --recursive -- python main.py

# Format code
format:
	@echo "Formatting code..."
	black . --line-length 100
	isort .
	@echo "✓ Code formatted"

# Lint code
lint:
	@echo "Linting code..."
	pylint api/ database/ config/ scanners/ core/ alerts/
	@echo "✓ Linting complete"

# Check dependencies
check-deps:
	@echo "Checking dependencies..."
	pip check
	@echo "✓ Dependencies OK"

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	pip install --upgrade -r requirements.txt
	@echo "✓ Dependencies updated"

# Create .env from example
setup-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file - please edit with your API key"; \
	else \
		echo ".env already exists"; \
	fi

# Full setup (first time)
setup: setup-env install docker-up db-init
	@echo ""
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env and add your UW_API_KEY"
	@echo "2. Run: make test"
	@echo "3. Run: make run-examples"
	@echo ""

# Backup database
backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U uw_user uw_scanner > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✓ Backup created in backups/"

# Restore database
restore:
	@echo "Restoring database from backup..."
	@echo "Available backups:"
	@ls -1 backups/*.sql 2>/dev/null || echo "No backups found"
	@echo "Run: cat backups/backup_XXXXXX.sql | docker-compose exec -T postgres psql -U uw_user uw_scanner"
