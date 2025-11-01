# 🚀 QUICK START GUIDE

Get the Ultimate Scanner running in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Unusual Whales API key
- Terminal/command line access

## Step 1: Install Dependencies

```bash
cd /home/user/uw_scanner

# Install core packages
pip install aiohttp loguru pydantic pydantic-settings python-dotenv rich sqlalchemy asyncpg redis tenacity backoff
```

## Step 2: Configure API Key

Your API key is already configured in `.env`:
```
UW_API_KEY=72cac8bd-c1c5-488b-ad48-58d554be20d9
```

✅ **API Tested & Working!**

## Step 3: Run Quick Test

Verify everything works:

```bash
python FINAL_TEST.py
```

Expected output:
```
✅ Stock State: $681.75
✅ Options Flow: 10/10 (BEARISH)
✅ Dark Pool: $3.8B tracked
✅ Composite Score: 7.9/10 (STRONG)
```

## Step 4: Choose Your Mode

### Option A: Run Single Mode

**Mode 1 - Intraday SPY (Fast scalps)**
```bash
python run_scanner.py
```
- Scans every 60 seconds
- 0-2 DTE options
- Quick signals for day trading

**Mode 2 - Swing Trading (Multi-day holds)**
```bash
python run_scanner.py --mode 2
```
- Scans every 5 minutes
- 30-45 DTE options
- 50+ ticker watchlist

**Mode 3 - Long-Term (Investment plays)**
```bash
python run_scanner.py --mode 3
```
- Scans every hour
- Tracks Congress trades
- Multi-month horizon

### Option B: Run All Modes Simultaneously

```bash
python run_all_modes.py
```

Runs all 3 scanners in parallel:
- Mode 1: Every 60s
- Mode 2: Every 5m
- Mode 3: Every 1h

Press `Ctrl+C` to stop.

---

## Configuration Options

### Basic Settings (.env file)

```bash
# API
UW_API_KEY=your_key_here

# Scanner Settings
SCAN_INTERVAL=60          # Mode 1 scan frequency (seconds)
LOG_LEVEL=INFO            # Logging detail
MODE=1                    # Default mode (1, 2, or 3)

# Alerts (Optional)
MIN_ALERT_SCORE=7.0       # Minimum score to trigger alert
ALERT_COOLDOWN=300        # Seconds between duplicate alerts
```

### Discord Alerts (Optional)

1. Create a Discord webhook:
   - Server Settings → Integrations → Webhooks → New Webhook
   - Copy the webhook URL

2. Add to `.env`:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_here
```

3. Restart scanner - alerts will auto-send!

### Telegram Alerts (Optional)

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Add to `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## Understanding Signals

### Mode 1 (Intraday) Signals

```
Score: 7.9/10 (STRONG)
Direction: BEARISH
Type: GEX_RESISTANCE
Confidence: 85%
```

- **Score 8-10**: Extreme signal, high conviction
- **Score 7-8**: Strong signal, actionable
- **Score 6-7**: Moderate signal, watch for confirmation
- **Score <6**: Weak signal, wait for better setup

### Mode 2 (Swing) Signals

```
Ticker: AAPL @ $175.50
Score: 8.2/10
Direction: BULLISH
Strategy: Call Debit Spread
Target DTE: 30-45 days
Confidence: HIGH
```

**Strategies Recommended:**
- **Bull/Bear Spreads**: Directional with defined risk
- **Iron Condor**: Sideways/low volatility
- **Debit Spreads**: Low IV environments

### Mode 3 (Long-Term) Signals

```
Ticker: NVDA @ $850.00
Score: 8.7/10
Thesis: Congress accumulation + Institutional buying
Catalysts:
  • Recent congress buying (3 purchases)
  • Institutional accumulation (+12%)
  • Seasonal tailwind
Conviction: VERY HIGH
Horizon: 3-12 months
```

**Key Factors:**
- **Congress Trades**: Lawmakers buying = BULLISH
- **Institutional**: 13F filings showing accumulation
- **Short Squeeze**: High short interest + catalysts
- **Seasonality**: Historical patterns

---

## Monitoring Your Scanner

### Live Dashboard

The scanner displays:
- Current signals
- Scan statistics
- Alert history
- System health

Example output:
```
════════════════════════════════════════════════
  📊 COMPOSITE ANALYSIS
════════════════════════════════════════════════

  ⚡────────────────────────────────────────────⚡
    COMPOSITE SCORE: 7.9/10 | ⚡ STRONG
  ⚡────────────────────────────────────────────⚡

  Component Scores:
     Options Flow:  10.0/10 (weight: 35%)
     GEX Pivots:    5.0/10 (weight: 30%)
     Dark Pool:     10.0/10 (weight: 20%)

  🎯 ACTIONABLE SIGNAL - Consider entering position
     Direction: 🔴 BEARISH
```

### Logs

Logs are saved to `logs/scanner.log`:
```bash
tail -f logs/scanner.log
```

---

## Troubleshooting

### Issue: API Key Invalid
```
❌ Authentication failed
```
**Fix:** Check your API key in `.env` file

### Issue: Rate Limiting
```
⚠️ Rate limit exceeded
```
**Fix:** Scanner has built-in rate limiting. This shouldn't happen.  
If it does, increase `SCAN_INTERVAL` in `.env`

### Issue: No Signals Found
```
⏸️ NO SIGNAL - Wait for better setup
```
**This is normal!** Not every scan produces a signal.  
The scanner is selective - it only alerts on high-quality setups.

### Issue: Missing Dependencies
```
ModuleNotFoundError: No module named 'X'
```
**Fix:** 
```bash
pip install X
```
Or install all at once:
```bash
pip install -r requirements.txt
```

---

## Performance Tips

### 1. Run in Background

```bash
# Linux/Mac
nohup python run_all_modes.py > scanner.log 2>&1 &

# Check if running
ps aux | grep python

# Stop
pkill -f run_all_modes.py
```

### 2. Use Screen/Tmux

```bash
# Start screen session
screen -S scanner

# Run scanner
python run_all_modes.py

# Detach: Ctrl+A then D
# Reattach: screen -r scanner
```

### 3. Optimize for Your Use Case

**Day Trader?** → Use Mode 1 only
```bash
python run_scanner.py --mode 1
```

**Swing Trader?** → Use Mode 2 only
```bash
python run_scanner.py --mode 2
```

**Investor?** → Use Mode 3 only
```bash
python run_scanner.py --mode 3
```

**Want it all?** → Run all modes
```bash
python run_all_modes.py
```

---

## Advanced Usage

### Custom Watchlist (Mode 2)

Edit `scanners/mode2_swing.py`:
```python
self.core_watchlist = [
    "AAPL", "MSFT", "GOOGL",  # Add your tickers here
    # ... more tickers
]
```

### Adjust Scoring Weights

Edit `core/scoring.py` to change how signals are scored.

### Database Integration

To store signals in database:

1. Install PostgreSQL
2. Update `DATABASE_URL` in `.env`
3. Run migrations:
```bash
python init_project.py
```

Scanner will auto-save all signals.

---

## What's Next?

### After Running Successfully

1. **Monitor for 24 hours** - See what signals it generates
2. **Set up alerts** - Discord/Telegram for real-time notifications
3. **Backtest signals** - Review historical accuracy
4. **Paper trade** - Test signals without real money
5. **Go live** - Start trading with real capital (at your own risk!)

### Recommended Workflow

```
1. Morning: Check Mode 3 signals (long-term picks)
   ↓
2. During Market: Monitor Mode 1 (intraday scalps)
   ↓
3. Evening: Review Mode 2 signals (swing setups)
   ↓
4. Weekend: Analyze performance, adjust settings
```

---

## Support & Resources

### Documentation
- `README.md` - Full documentation
- `PROJECT_STATUS.md` - Current build status
- `PHASE_1_COMPLETE.md` - API integration details
- `PHASE_2_COMPLETE.md` - Mode 1 scanner details

### Testing
- `quick_test.py` - API connectivity test
- `simple_scanner_test.py` - Basic scanner test
- `FINAL_TEST.py` - Comprehensive test

### Need Help?

1. Check logs: `logs/scanner.log`
2. Run test suite: `python FINAL_TEST.py`
3. Verify API key: `python quick_test.py`

---

## Success Checklist

Before starting live trading:

- [ ] API key configured and tested
- [ ] Quick test passes (FINAL_TEST.py)
- [ ] Scanner runs without errors
- [ ] Signals are being generated
- [ ] Understand signal scoring
- [ ] Alerts configured (optional)
- [ ] Monitored for 24+ hours
- [ ] Backtested signals (if possible)
- [ ] Paper traded successfully
- [ ] Risk management plan in place

---

## Current Status

✅ **API Integration** - Fully operational  
✅ **Mode 1 Scanner** - Tested with live data  
✅ **Mode 2 Scanner** - Built, ready to test  
✅ **Mode 3 Scanner** - Built, ready to test  
✅ **Alert System** - Discord/Telegram ready  

**Last Test Result:**
- Score: 7.9/10 (STRONG)
- Signal: BEARISH on SPY
- Dark Pool: $3.8B tracked
- Flow: 10/10 (Extreme bearish)

🔥 **The Monster is ALIVE!** 🔥

---

**Questions? Issues?**  
Check `PROJECT_STATUS.md` for latest updates and known issues.

**Ready to trade?**  
Remember: This is a tool, not financial advice. Always use proper risk management!
