# 🚀 Deployment Guide

## Prerequisites

- GitHub account
- Vercel account (free tier works)
- Unusual Whales API key

## Step 1: Push to GitHub

1. Create new repository on GitHub:
   - Go to https://github.com/new
   - Name: `unusual-whales-scanner` (or your preference)
   - **Public** visibility (for Vercel free tier)
   - **Do NOT** initialize with README, .gitignore, or license

2. Push local repository:
   ```bash
   cd /home/user/uw_scanner
   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy to Vercel

### Option A: Vercel Dashboard (Recommended)

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure project:
   - **Framework Preset:** Other
   - **Build Command:** (leave empty)
   - **Output Directory:** (leave empty)
   - **Install Command:** `pip install -r requirements_vercel.txt`

4. Add Environment Variables:
   - Click "Environment Variables"
   - Add: `UNUSUAL_WHALES_API_KEY` = `your_api_key_here`
   - Add: `REDIS_ENABLED` = `false`
   - Add: `DATABASE_ENABLED` = `false`

5. Click "Deploy"

### Option B: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd /home/user/uw_scanner
vercel --prod

# Set environment variables
vercel env add UNUSUAL_WHALES_API_KEY production
# Enter your API key when prompted
```

## Step 3: Verify Deployment

Once deployed, Vercel will give you a URL like:
```
https://unusual-whales-scanner.vercel.app
```

Test these endpoints:
- `https://your-app.vercel.app/` - Main dashboard
- `https://your-app.vercel.app/api/health` - Health check
- `https://your-app.vercel.app/api/scan-mode1` - Mode 1 scan

## Step 4: Configure Alerts (Optional)

To enable Discord/Telegram alerts:

1. In Vercel dashboard, add environment variables:
   - `DISCORD_WEBHOOK_URL` = your Discord webhook URL
   - `TELEGRAM_BOT_TOKEN` = your Telegram bot token
   - `TELEGRAM_CHAT_ID` = your Telegram chat ID

2. Redeploy (automatic if using git push)

## Limitations on Vercel

**Serverless Function Constraints:**
- 60-second timeout (free tier) / 900 seconds (pro)
- No persistent processes (can't run continuous scanners)
- Cold starts (first request may be slow)

**For Full Scanner Functionality:**

The Vercel deployment provides:
- ✅ Web dashboard
- ✅ API endpoints for on-demand scans
- ✅ Health monitoring
- ✅ Integration testing

For continuous scanning (Mode 1 every 60s, Mode 2 every 5m, Mode 3 every 1h):
- Run `run_all_modes.py` locally
- OR deploy to a server (AWS EC2, DigitalOcean, etc.)
- OR use GitHub Actions for scheduled scans

## Alternative: Full Production Deployment

For 24/7 continuous scanning:

### AWS EC2 / DigitalOcean Droplet

```bash
# SSH into server
ssh user@your-server

# Clone repository
git clone https://github.com/YOUR_USERNAME/unusual-whales-scanner.git
cd unusual-whales-scanner

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Run with supervisor for auto-restart
sudo apt install supervisor
sudo nano /etc/supervisor/conf.d/uw_scanner.conf
```

**Supervisor config:**
```ini
[program:uw_scanner]
command=/usr/bin/python3 /path/to/run_all_modes.py
directory=/path/to/unusual-whales-scanner
user=youruser
autostart=true
autorestart=true
stderr_logfile=/var/log/uw_scanner.err.log
stdout_logfile=/var/log/uw_scanner.out.log
```

```bash
# Start scanner
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start uw_scanner
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_all_modes.py"]
```

```bash
# Build and run
docker build -t uw-scanner .
docker run -d --env-file .env --name uw-scanner uw-scanner
```

## Monitoring

### Check Deployment Status

```bash
# View logs on Vercel
vercel logs

# Or via dashboard
https://vercel.com/your-username/unusual-whales-scanner
```

### Local Testing Before Deploy

```bash
# Test API endpoints locally
python quick_test.py

# Test full scanner
python FINAL_TEST.py

# Run single mode
python run_scanner.py --mode 1
```

## Troubleshooting

**Issue: Import errors on Vercel**
- Solution: Check `requirements_vercel.txt` has all dependencies
- Vercel uses lightweight requirements to avoid timeout

**Issue: API key not working**
- Solution: Verify environment variable name matches exactly
- Check Vercel dashboard -> Settings -> Environment Variables

**Issue: Timeout errors**
- Solution: Serverless functions have time limits
- For continuous scanning, use server deployment instead

**Issue: Cold starts slow**
- Solution: Keep functions warm with scheduled pings
- Or upgrade to Vercel Pro for better performance

## Next Steps

1. ✅ Deploy to Vercel (web dashboard)
2. Add Tier 1 features (politician portfolios, news, etc.)
3. Set up continuous scanning on a server
4. Configure alerts (Discord/Telegram)
5. Build web dashboard with real-time updates

## Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Python on Vercel](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Unusual Whales API Docs](https://docs.unusualwhales.com/)
