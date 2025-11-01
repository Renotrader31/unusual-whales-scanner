# 🚀 Getting Started with UW Scanner

Welcome! This guide will walk you through setting up and running your Ultimate Unusual Whales Scanner.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [First Run](#first-run)
5. [Testing](#testing)
6. [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

- **Python 3.11 or higher** ([Download](https://www.python.org/downloads/))
- **PostgreSQL 14+** ([Download](https://www.postgresql.org/download/))
  - Or [TimescaleDB](https://www.timescale.com/download) for better performance (recommended)
- **Redis 6+** ([Download](https://redis.io/download))
- **Unusual Whales API Key** ([Get one here](https://unusualwhales.com/public-api))

### System Requirements

- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 10GB+ for historical data
- **Network**: Stable internet connection

---

## Installation

### Step 1: Extract the Scanner

```bash
# Navigate to the scanner directory
cd uw_scanner
```

### Step 2: Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Installing TA-Lib may require additional steps on some systems. See [TA-Lib Installation Guide](https://github.com/mrjbq7/ta-lib#installation) if you encounter issues.

---

## Configuration

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

### Step 2: Edit Configuration

Open `.env` in your text editor and configure these **required** settings:

```bash
# Your Unusual Whales API key
UW_API_KEY=your_actual_api_key_here

# Database connection (adjust for your setup)
DATABASE_URL=postgresql://username:password@localhost:5432/uw_scanner

# Redis connection
REDIS_URL=redis://localhost:6379/0
```

### Step 3: Set Up Database

**Create PostgreSQL Database:**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE uw_scanner;

# Exit
\q
```

**For TimescaleDB users:**
```sql
CREATE DATABASE uw_scanner;
\c uw_scanner
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

---

## First Run

### Initialize the Project

Run the initialization script to set up everything:

```bash
python init_project.py
```

This will:
- ✅ Check your configuration
- ✅ Test database connection
- ✅ Test Redis connection
- ✅ Verify API access
- ✅ Create database tables
- ✅ Set up TimescaleDB (if available)
- ✅ Create necessary directories

**Expected output:**
```
============================================================
🐋 Unusual Whales Scanner - Initialization
============================================================

📋 Step 1: Checking environment...
✅ .env file found
✅ All required packages installed

⚙️ Step 2: Testing configuration...
✅ Configuration loaded successfully
   API Base URL: https://api.unusualwhales.com
   Rate Limit: 10 req/s
   ...

🔌 Step 3: Testing connections...
✅ Database connection successful
✅ Redis connection successful
✅ API connection successful
   Retrieved 5 flow alert(s)

🗄️ Step 4: Setting up database...
✅ Database tables created
✅ TimescaleDB hypertables configured

📁 Step 5: Creating directories...
✅ Created directories: logs, data, backups

============================================================
📊 Initialization Summary
============================================================
✅ Environment file
✅ Dependencies
✅ Configuration
✅ Database
✅ Redis
✅ API
✅ Tables
✅ TimescaleDB

============================================================
🎉 Initialization Complete!
============================================================
```

---

## Testing

### Test 1: API Connection

Run the connection test to verify everything works:

```bash
python test_connection.py
```

You should see:
```
🐋 Testing Unusual Whales API Connection

→ Connecting to API...
→ Fetching SPY flow alerts...
→ Fetching SPY gamma exposure...
→ Fetching market top movers...
→ Fetching institutional filings...
→ Fetching Congressional trades...

✅ Connection Successful!

╭─────────────────────────────────────────────╮
│            API Test Results                 │
├────────────────────────┬──────────┬─────────┤
│ Endpoint               │ Status   │ Records │
├────────────────────────┼──────────┼─────────┤
│ Flow Alerts (SPY)      │ ✅ Success│       5 │
│ Gamma Exposure (SPY)   │ ✅ Success│Available│
│ Market Top Impact      │ ✅ Success│       5 │
│ Institutional Filings  │ ✅ Success│       5 │
│ Congressional Trades   │ ✅ Success│       5 │
╰────────────────────────┴──────────┴─────────╯

🎉 All tests passed! Your API is working perfectly.
```

### Test 2: Individual Components

Test specific components:

```bash
# Test database
python -m database.connection

# Test API client
python -m api.client

# Test WebSocket
python -m api.websocket_client

# Test rate limiter
python -m api.rate_limiter
```

---

## Next Steps

### 🎯 What to Do Next

Now that your scanner is set up, you can:

1. **Explore the API**
   ```bash
   python
   >>> import asyncio
   >>> from api import UnusualWhalesClient
   >>> 
   >>> async def test():
   ...     async with UnusualWhalesClient() as client:
   ...         flow = await client.get_flow_alerts(ticker='SPY', limit=10)
   ...         print(flow)
   ... 
   >>> asyncio.run(test())
   ```

2. **Wait for Scanner Implementation** (Coming in Phase 2)
   - Mode 1: Intraday SPY Scanner
   - Mode 2: Swing Trading Scanner
   - Mode 3: Long-Term Investment Scanner

3. **Customize Your Setup**
   - Adjust rate limits in `.env`
   - Configure scanner modes
   - Set up notifications (Discord/Telegram)

4. **Monitor Logs**
   ```bash
   tail -f logs/uw_scanner.log
   ```

### 📚 Learning Resources

- **README.md**: Complete documentation
- **API Endpoints**: Check `api/endpoints.py` for all available endpoints
- **Database Models**: See `database/models.py` for data structures
- **Examples**: Each module has test code at the bottom (run with `if __name__ == '__main__'`)

### 🎨 Customization Ideas

- **Add custom scanners** in `scanners/`
- **Create alert rules** using `database/models.py`
- **Build dashboards** with Streamlit
- **Integrate ML models** for predictions
- **Add new data sources** to complement UW data

---

## 🐛 Troubleshooting

### Problem: "API key invalid"

**Solution:**
1. Check your `.env` file has the correct `UW_API_KEY`
2. Verify your subscription is active at unusualwhales.com
3. Make sure there are no extra spaces or quotes around the key

### Problem: "Database connection failed"

**Solution:**
1. Ensure PostgreSQL is running:
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   
   # Windows
   # Start from Services or pgAdmin
   ```
2. Check `DATABASE_URL` in `.env` is correct
3. Verify the database exists:
   ```bash
   psql -U postgres -c "SELECT datname FROM pg_database WHERE datname = 'uw_scanner';"
   ```

### Problem: "Redis connection failed"

**Solution:**
1. Start Redis:
   ```bash
   # macOS
   brew services start redis
   
   # Linux
   sudo systemctl start redis
   
   # Windows
   # Download from https://github.com/microsoftarchive/redis/releases
   ```
2. Test Redis:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### Problem: "Module not found"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Problem: "Rate limit exceeded"

**Solution:**
1. Reduce `UW_RATE_LIMIT` in `.env` (default: 10)
2. Increase `CACHE_TTL` to cache more (default: 300 seconds)
3. Enable caching: `CACHE_ENABLED=true`

---

## 📞 Getting Help

If you run into issues:

1. **Check the logs**: `logs/uw_scanner.log`
2. **Review README.md**: Comprehensive documentation
3. **Test components individually**: Use the test scripts
4. **Check API status**: [unusualwhales.com/status](https://unusualwhales.com)

---

## ✅ You're Ready!

Once you see all green checkmarks from `init_project.py`, you're ready to start building with the scanner!

**Next Phase**: Scanner implementations coming soon!

- ⏳ Mode 1: Intraday SPY Scanner
- ⏳ Mode 2: Swing Trading Scanner  
- ⏳ Mode 3: Long-Term Investment Scanner

**Happy Trading! 📈🐋**
