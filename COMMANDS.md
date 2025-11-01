# 🎮 Command Reference - UW Scanner

Quick reference for all available commands.

## 🚀 Setup Commands

```bash
# Full first-time setup
make setup

# Install dependencies only
make install

# Create .env file
make setup-env

# Start databases
make docker-up

# Start with GUI tools (pgAdmin + Redis Commander)
make docker-tools

# Stop databases
make docker-down

# Initialize database tables
make db-init
```

## ✅ Testing Commands

```bash
# Quick API connection test
make test

# Full test suite
make test-full

# Run specific example
python examples/basic_usage.py

# Run all examples
make run-examples
```

## 🔍 Development Commands

```bash
# Open Python shell with imports
make shell

# View recent logs
make logs

# Clean cache and temp files
make clean

# Format code (requires black, isort)
make format

# Lint code (requires pylint)
make lint

# Check dependencies
make check-deps

# Update dependencies
make update-deps
```

## 💾 Database Commands

```bash
# Initialize tables
make db-init

# Backup database
make backup

# View backup instructions
make restore

# Access PostgreSQL directly
docker-compose exec postgres psql -U uw_user -d uw_scanner

# Access Redis directly
docker-compose exec redis redis-cli
```

## 📊 Monitoring Commands

```bash
# View logs in real-time
tail -f logs/scanner.log

# View Docker logs
docker-compose logs -f

# Check database status
docker-compose ps

# View resource usage
docker stats
```

## 🌐 Web Interfaces (if using docker-tools)

```bash
# pgAdmin (PostgreSQL GUI)
open http://localhost:8080
# Default: admin@uwscanner.local / admin

# Redis Commander (Redis GUI)
open http://localhost:8081
```

## 🐍 Python API Commands

### Basic Usage
```bash
# Run Python with auto-imports
make shell

# Then in Python:
>>> async with UWClient() as client:
...     data = await client.get_stock_state('SPY')
...     print(data)
```

### Direct Python Execution
```python
# Test API connection
python tests/test_api.py

# Run examples interactively
python examples/basic_usage.py

# Custom script
python your_script.py
```

## 📦 Package Management

```bash
# Install in development mode
pip install -e .

# Install specific extras
pip install -r requirements.txt

# Freeze current environment
pip freeze > requirements-frozen.txt

# Check for outdated packages
pip list --outdated
```

## 🔧 Configuration

```bash
# View current configuration
python -c "from config.settings import settings; print(settings.dict())"

# Test configuration
python -c "from config.settings import settings; print(f'API: {settings.uw_base_url}')"

# Validate settings
python -c "from config.settings import settings; print('Config valid!' if settings.uw_api_key else 'Add API key')"
```

## 📝 Common Workflows

### First Time Setup
```bash
cd uw_scanner
make setup           # Full setup
# Edit .env with your API key
make test           # Verify
make run-examples   # Try it out
```

### Daily Development
```bash
make docker-up      # Start databases
make test          # Verify API
make shell         # Start coding
make logs          # Check issues
make docker-down   # Cleanup
```

### Before Committing
```bash
make clean         # Clean temp files
make format        # Format code
make lint          # Check quality
make test-full     # Run all tests
```

### Deployment
```bash
make backup        # Backup database
make docker-up     # Start services
make db-init       # Initialize DB
# Deploy your scanner
```

## 🆘 Troubleshooting Commands

```bash
# Check if API key is set
echo $UW_API_KEY

# Verify Python version
python --version  # Should be 3.11+

# Check Docker
docker --version
docker-compose --version

# Test PostgreSQL connection
docker-compose exec postgres pg_isready

# Test Redis connection
docker-compose exec redis redis-cli ping

# View all environment variables
env | grep UW_

# Check port availability
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8501  # Streamlit (future)
```

## 📚 Documentation Commands

```bash
# Read main documentation
cat README.md | less

# Read quick start
cat QUICKSTART.md | less

# Check project status
cat PROJECT_STATUS.md | less

# View this file
cat COMMANDS.md | less

# Generate API documentation (requires pdoc)
pdoc --html api/ database/ config/
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Restart service
docker-compose restart postgres

# Execute command in container
docker-compose exec postgres psql -U uw_user

# View resource usage
docker-compose stats
```

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Setup everything | `make setup` |
| Test API | `make test` |
| Start databases | `make docker-up` |
| Run examples | `make run-examples` |
| View logs | `make logs` |
| Clean up | `make clean` |
| Open shell | `make shell` |
| Stop databases | `make docker-down` |

## 💡 Pro Tips

```bash
# Chain commands
make clean && make test && make run-examples

# Run in background
nohup make docker-up > /dev/null 2>&1 &

# Watch logs
watch -n 1 "docker-compose ps && docker-compose logs --tail=20"

# Quick health check
make docker-up && sleep 5 && make test

# Export database
docker-compose exec -T postgres pg_dump -U uw_user uw_scanner > backup.sql

# Import database
cat backup.sql | docker-compose exec -T postgres psql -U uw_user uw_scanner
```

## 🔐 Security Commands

```bash
# Generate secure password
openssl rand -base64 32

# Check for vulnerabilities
pip install safety
safety check

# Update security packages
pip install --upgrade pip setuptools wheel
```

## 📊 Statistics Commands

```bash
# Count lines of code
find . -name "*.py" -not -path "./venv/*" | xargs wc -l

# List largest files
find . -name "*.py" -not -path "./venv/*" -exec ls -lh {} \; | sort -k5 -h

# Count functions
grep -r "def " --include="*.py" | wc -l

# Count classes
grep -r "class " --include="*.py" | wc -l
```

## 🎨 Customization

```bash
# Edit configuration
nano .env

# Edit Makefile
nano Makefile

# Edit database models
nano database/models.py

# Edit API endpoints
nano api/endpoints.py
```

---

## Need More Help?

- **Documentation**: See `README.md`
- **Quick Start**: See `QUICKSTART.md`
- **Project Status**: See `PROJECT_STATUS.md`
- **Issues**: Check logs with `make logs`

---

**Pro Tip**: Bookmark this file! 📌

All commands in one place for quick reference.
