# 📦 Installation Guide

Complete step-by-step installation instructions for the Ultimate Unusual Whales Scanner.

---

## 🖥️ System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 10 GB free
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Internet**: Stable broadband connection

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **OS**: Latest version
- **Internet**: High-speed connection

---

## 📥 Prerequisites Installation

### 1. Python 3.11+

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Verify
python3 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
```

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Verify in Command Prompt: `python --version`

### 2. PostgreSQL 14+

**macOS:**
```bash
# Using Homebrew
brew install postgresql@14
brew services start postgresql@14

# Create user (optional)
createuser -s postgres
```

**Linux (Ubuntu):**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create user
sudo -u postgres createuser -s $USER
```

**Windows:**
1. Download from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run installer (remember password!)
3. Start PostgreSQL from Services

**Verify:**
```bash
psql --version
# Should show: psql (PostgreSQL) 14.x
```

### 3. Redis 6+

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu):**
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Windows:**
1. Download from [github.com/microsoftarchive/redis](https://github.com/microsoftarchive/redis/releases)
2. Extract and run `redis-server.exe`
3. Or use [Memurai](https://www.memurai.com/) (Redis for Windows)

**Verify:**
```bash
redis-cli ping
# Should return: PONG
```

### 4. Git (Optional but Recommended)

**macOS:**
```bash
brew install git
```

**Linux:**
```bash
sudo apt install git
```

**Windows:**
- Download from [git-scm.com](https://git-scm.com/download/win)

---

## 🚀 Scanner Installation

### Step 1: Get the Scanner

If you have the scanner as a zip file:
```bash
# Extract
unzip uw_scanner.zip
cd uw_scanner
```

If you have it in a Git repository:
```bash
git clone <repository-url>
cd uw_scanner
```

### Step 2: Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

Your prompt should now show `(venv)`.

### Step 3: Install Python Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**If you encounter TA-Lib installation errors:**

**macOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

**Linux:**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib
```

**Windows:**
```bash
# Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# Then install:
pip install TA_Lib‑0.4.XX‑cpXX‑cpXXm‑win_amd64.whl
```

---

## ⚙️ Configuration

### Step 1: Create Environment File

```bash
cp .env.example .env
```

### Step 2: Get Your API Key

1. Go to [unusualwhales.com/public-api](https://unusualwhales.com/public-api)
2. Subscribe to a plan
3. Copy your API key

### Step 3: Configure .env File

Open `.env` in a text editor and set:

```bash
# ============================================================
# REQUIRED SETTINGS
# ============================================================

# Your Unusual Whales API key
UW_API_KEY=your_actual_api_key_here

# Database connection
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/uw_scanner

# Redis connection  
REDIS_URL=redis://localhost:6379/0

# ============================================================
# OPTIONAL SETTINGS
# ============================================================

# Rate limiting
UW_RATE_LIMIT=10
UW_BURST_LIMIT=20

# Scanner modes
MODE_1_ENABLED=true
MODE_2_ENABLED=true
MODE_3_ENABLED=true

# Notifications (optional)
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Logging
LOG_LEVEL=INFO
```

**Important**: Replace placeholders with your actual values!

---

## 🗄️ Database Setup

### Step 1: Create Database

**Using psql:**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE uw_scanner;

# Exit
\q
```

**Or one-liner:**
```bash
createdb -U postgres uw_scanner
```

### Step 2: (Optional) Install TimescaleDB

For better performance with time-series data:

**macOS:**
```bash
brew tap timescale/tap
brew install timescaledb
```

**Linux:**
```bash
# Add repository
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"

# Install
sudo apt install timescaledb-2-postgresql-14

# Setup
sudo timescaledb-tune
```

**Enable in database:**
```bash
psql -U postgres -d uw_scanner -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

---

## 🧪 Initialize & Test

### Step 1: Run Initialization

```bash
python init_project.py
```

This will:
- ✅ Check configuration
- ✅ Test database connection
- ✅ Test Redis connection
- ✅ Verify API access
- ✅ Create all database tables
- ✅ Set up TimescaleDB (if available)

**Expected output:**
```
============================================================
🐋 Unusual Whales Scanner - Initialization
============================================================
...
🎉 Initialization Complete!
============================================================
```

### Step 2: Test API Connection

```bash
python test_connection.py
```

You should see green checkmarks for all endpoints.

---

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Problem: "Database connection failed"

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   # macOS
   brew services list | grep postgresql
   
   # Linux
   sudo systemctl status postgresql
   
   # Windows
   # Check Services app for "postgresql" service
   ```

2. **Verify credentials:**
   ```bash
   psql -U postgres -d uw_scanner
   # If this fails, your DATABASE_URL is wrong
   ```

3. **Check DATABASE_URL format:**
   ```
   postgresql://username:password@host:port/database
   
   Example:
   postgresql://postgres:mypassword@localhost:5432/uw_scanner
   ```

### Problem: "Redis connection failed"

**Solutions:**

1. **Check Redis is running:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Start Redis:**
   ```bash
   # macOS
   brew services start redis
   
   # Linux
   sudo systemctl start redis
   
   # Windows
   # Run redis-server.exe
   ```

### Problem: "API authentication failed"

**Solutions:**

1. **Check API key:**
   ```bash
   python -c "from config import get_settings; print(get_settings().uw_api_key[:10])"
   ```

2. **Verify subscription:**
   - Log in to unusualwhales.com
   - Check your subscription is active
   - Generate a new API key if needed

3. **Check for extra spaces:**
   - Open `.env` file
   - Make sure no spaces around `=`
   - No quotes around the key

### Problem: "Permission denied"

**Linux/macOS:**
```bash
# Fix permissions
chmod +x init_project.py
chmod +x test_connection.py
```

### Problem: "Port already in use"

**PostgreSQL (5432):**
```bash
# Find what's using the port
lsof -i :5432

# Kill the process or use a different port
# Update DATABASE_URL to use different port
```

**Redis (6379):**
```bash
# Find what's using the port
lsof -i :6379

# Or use different Redis database number in REDIS_URL
# redis://localhost:6379/1  (change /0 to /1)
```

---

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] Python 3.11+ installed (`python --version`)
- [ ] PostgreSQL running (`psql --version`)
- [ ] Redis running (`redis-cli ping`)
- [ ] Virtual environment activated (`which python`)
- [ ] All packages installed (`pip list`)
- [ ] `.env` file configured
- [ ] Database created (`psql -U postgres -l | grep uw_scanner`)
- [ ] `init_project.py` completed successfully
- [ ] `test_connection.py` shows all green checkmarks
- [ ] No errors in `logs/uw_scanner.log`

---

## 🎉 You're Ready!

If all checks pass, you're ready to use the scanner!

**Next steps:**
1. Read `GETTING_STARTED.md` for usage instructions
2. Check `QUICK_REFERENCE.md` for code examples
3. Explore the API with `python -m api.client`

**Need help?**
- Check `README.md` for detailed documentation
- Review code comments for implementation details
- Check logs: `logs/uw_scanner.log`

---

## 📚 Additional Resources

- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Redis Docs](https://redis.io/docs/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Unusual Whales API Docs](https://api.unusualwhales.com/docs)
- [TimescaleDB Docs](https://docs.timescale.com/)

---

**Installation complete! Happy trading! 📈🐋**
