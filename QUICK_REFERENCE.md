# 🚀 Quick Reference Card

## Common Commands

### Setup
```bash
# Initial setup
python init_project.py

# Test connection
python test_connection.py
```

### Running Components
```bash
# Test API
python -m api.client

# Test WebSocket
python -m api.websocket_client

# Test database
python -m database.connection

# Test rate limiter
python -m api.rate_limiter
```

---

## Code Snippets

### Basic API Usage

```python
import asyncio
from api import UnusualWhalesClient

async def main():
    async with UnusualWhalesClient() as client:
        # Get flow alerts
        flow = await client.get_flow_alerts(ticker='SPY', limit=10)
        
        # Get GEX
        gex = await client.get_spot_exposures('SPY')
        
        # Get dark pool
        dp = await client.get_dark_pool('SPY', limit=50)
        
        print(f"Found {len(flow['data'])} alerts")

asyncio.run(main())
```

### WebSocket Streaming

```python
from api.websocket_client import WebSocketClient, ChannelManager

async def main():
    ws = WebSocketClient()
    manager = ChannelManager(ws)
    
    # Define handlers
    async def on_flow(msg):
        print(f"Flow: {msg['ticker']} ${msg['premium']:,.0f}")
    
    # Subscribe
    await manager.subscribe_flow_alerts(on_flow)
    await manager.subscribe_gex('SPY', on_flow)
    
    # Start
    await ws.start()

asyncio.run(main())
```

### Database Operations

```python
from database import get_db_manager, OptionsFlow
from datetime import datetime

async def main():
    db = get_db_manager()
    
    async with db.get_async_session() as session:
        # Create record
        flow = OptionsFlow(
            timestamp=datetime.utcnow(),
            ticker='SPY',
            strike=600.0,
            premium=250000,
            direction='call_buy'
        )
        session.add(flow)
        await session.commit()
    
    # Query
    async with db.get_async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(OptionsFlow)
            .where(OptionsFlow.ticker == 'SPY')
            .limit(10)
        )
        flows = result.scalars().all()
        print(f"Found {len(flows)} SPY flows")

asyncio.run(main())
```

### Redis Caching

```python
from database import get_redis_manager

async def main():
    redis = get_redis_manager()
    await redis.connect()
    
    # Store
    await redis.set_json('my_data', {'key': 'value'}, expire=300)
    
    # Retrieve
    data = await redis.get_json('my_data')
    
    # Publish/Subscribe
    await redis.publish('alerts', 'New signal!')
    
    await redis.disconnect()

asyncio.run(main())
```

---

## API Endpoints Quick Reference

### Mode 1: Intraday
```python
# Flow
await client.get_flow_alerts(ticker='SPY', min_premium=100000)
await client.get_net_prem_ticks('SPY')
await client.get_flow_per_strike_intraday('SPY')

# GEX
await client.get_spot_exposures('SPY')
await client.get_spot_exposures_by_strike('SPY')
await client.get_greek_exposure_strike('SPY')

# Market
await client.get_market_top_net_impact(limit=20)

# Dark Pool
await client.get_dark_pool('SPY', limit=100)
```

### Mode 2: Swing Trading
```python
# Greeks
await client.get_stock_greeks('AAPL')
await client.get_greek_exposure_strike('AAPL', expiry='2025-02-21')
await client.get_realized_volatility('AAPL')

# OI
await client.get_oi_per_strike('AAPL')
await client.get_oi_per_expiry('AAPL')

# Correlations
await client.get_market_correlations(['SPY', 'QQQ', 'IWM'])
```

### Mode 3: Long-Term
```python
# Institutional
await client.get_institution_latest_filings(limit=50)
await client.get_institution_ownership('AAPL')
await client.get_institution_holdings('Berkshire Hathaway')

# Congress
await client.get_congress_recent_trades(limit=100)

# Shorts
await client.get_shorts_data('GME')
await client.get_shorts_interest_float('GME')

# Seasonality
await client.get_seasonality_ticker_monthly('AAPL')

# News
await client.get_news_headlines(ticker='AAPL', limit=20)
```

---

## Configuration Quick Settings

### .env File

```bash
# API
UW_API_KEY=your_key
UW_RATE_LIMIT=10        # req/s

# Modes
MODE_1_ENABLED=true
MODE_2_ENABLED=true
MODE_3_ENABLED=true

# Mode 1 Settings
MODE_1_TICKER=SPY
MODE_1_GEX_THRESHOLD=1000000

# Mode 2 Settings
MODE_2_MIN_PREMIUM=250000
MODE_2_DTE_MIN=30
MODE_2_DTE_MAX=45

# Mode 3 Settings
MODE_3_MIN_INSTITUTION_POSITION=50000000
MODE_3_SHORT_INTEREST_THRESHOLD=20

# Caching
CACHE_ENABLED=true
CACHE_TTL=300           # seconds
```

---

## Troubleshooting

### Check API Key
```bash
python -c "from config import get_settings; s = get_settings(); print(f'Key: {s.uw_api_key[:10]}...')"
```

### Test Database
```bash
python -c "from database import get_db_manager; db = get_db_manager(); db.initialize_sync(); print('DB OK')"
```

### Test Redis
```bash
redis-cli ping
# Should return: PONG
```

### View Logs
```bash
tail -f logs/uw_scanner.log
```

### Clear Cache
```python
from api import UnusualWhalesClient
client = UnusualWhalesClient()
client.clear_cache()
```

---

## Useful Queries

### Find Large Flow
```sql
SELECT ticker, strike, premium, volume
FROM options_flow
WHERE premium > 500000
  AND timestamp > NOW() - INTERVAL '1 day'
ORDER BY premium DESC
LIMIT 20;
```

### Top GEX Strikes
```sql
SELECT ticker, strike, total_gex, spot_price
FROM gamma_exposure
WHERE ticker = 'SPY'
  AND timestamp = (SELECT MAX(timestamp) FROM gamma_exposure WHERE ticker = 'SPY')
ORDER BY ABS(total_gex) DESC
LIMIT 10;
```

### Recent Dark Pool Activity
```sql
SELECT ticker, price, size, value
FROM dark_pool_trades
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY value DESC
LIMIT 20;
```

### Congress Trades This Week
```sql
SELECT representative, ticker, transaction_type, amount_range
FROM congress_trades
WHERE transaction_date > NOW() - INTERVAL '7 days'
ORDER BY transaction_date DESC;
```

---

## WebSocket Channels

```python
# Available channels
'flow-alerts'           # Real-time flow
'price:SPY'            # Live SPY price
'gex:SPY'              # SPY gamma exposure
'gex_strike:SPY'       # GEX by strike
'gex_strike_expiry:SPY' # GEX by strike & expiry
'lit_trades'           # Exchange trades
'off_lit_trades'       # Dark pool trades
```

---

## Performance Tips

1. **Enable caching**: `CACHE_ENABLED=true`
2. **Use TimescaleDB**: Better performance for time-series
3. **Batch requests**: Group similar API calls
4. **Index queries**: Add indexes for frequent queries
5. **Async operations**: Use `async/await` throughout
6. **Connection pooling**: Already configured
7. **Rate limiting**: Respect limits to avoid bans

---

## Next Steps

- **Phase 2**: Build Mode 1 scanner
- **Phase 3**: Build Mode 2 scanner
- **Phase 4**: Build Mode 3 scanner
- **Phase 5**: Dashboard & alerts

---

**For detailed documentation, see:**
- `README.md` - Complete guide
- `GETTING_STARTED.md` - Setup instructions
- `PROJECT_SUMMARY.md` - What's built
