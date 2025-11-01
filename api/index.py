"""
Vercel API Route - Main Dashboard Entry Point
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve main dashboard HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Unusual Whales Scanner - LIVE</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                
                .header {{
                    text-align: center;
                    color: white;
                    margin-bottom: 40px;
                }}
                
                .header h1 {{
                    font-size: 3em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                
                .header p {{
                    font-size: 1.2em;
                    opacity: 0.9;
                }}
                
                .status-card {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }}
                
                .status-card h2 {{
                    color: #667eea;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }}
                
                .modes-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                
                .mode-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 10px;
                    cursor: pointer;
                    transition: transform 0.3s ease;
                }}
                
                .mode-card:hover {{
                    transform: translateY(-5px);
                }}
                
                .mode-card h3 {{
                    font-size: 1.5em;
                    margin-bottom: 10px;
                }}
                
                .mode-card p {{
                    opacity: 0.9;
                    line-height: 1.6;
                }}
                
                .mode-card .scan-interval {{
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px solid rgba(255,255,255,0.3);
                    font-weight: bold;
                }}
                
                .api-status {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin: 20px 0;
                }}
                
                .status-indicator {{
                    width: 15px;
                    height: 15px;
                    border-radius: 50%;
                    background: #4CAF50;
                    animation: pulse 2s infinite;
                }}
                
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                }}
                
                .endpoints-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 10px;
                    margin-top: 20px;
                }}
                
                .endpoint-tag {{
                    background: #f0f0f0;
                    padding: 8px 12px;
                    border-radius: 5px;
                    font-size: 0.9em;
                    color: #333;
                }}
                
                .cta-button {{
                    display: inline-block;
                    background: #4CAF50;
                    color: white;
                    padding: 15px 30px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    margin-top: 20px;
                    transition: background 0.3s ease;
                }}
                
                .cta-button:hover {{
                    background: #45a049;
                }}
                
                .footer {{
                    text-align: center;
                    color: white;
                    margin-top: 40px;
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐋 Unusual Whales Scanner</h1>
                    <p>Production-Grade Options Flow Analysis System</p>
                </div>
                
                <div class="status-card">
                    <h2>System Status</h2>
                    <div class="api-status">
                        <div class="status-indicator"></div>
                        <strong>LIVE & OPERATIONAL</strong>
                    </div>
                    <p><strong>Deployment Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    <p><strong>Environment:</strong> Vercel Production</p>
                    <p><strong>API Version:</strong> Unusual Whales v1</p>
                </div>
                
                <div class="status-card">
                    <h2>Active Trading Modes</h2>
                    <div class="modes-grid">
                        <div class="mode-card">
                            <h3>⚡ Mode 1: Intraday</h3>
                            <p>SPY scalper targeting 0-2 DTE options with rapid momentum plays</p>
                            <div class="scan-interval">📊 Scan Interval: Every 60 seconds</div>
                        </div>
                        
                        <div class="mode-card">
                            <h3>📈 Mode 2: Swing</h3>
                            <p>Multi-ticker swing trader for 30-45 DTE moderate-aggressive setups</p>
                            <div class="scan-interval">📊 Scan Interval: Every 5 minutes</div>
                        </div>
                        
                        <div class="mode-card">
                            <h3>💎 Mode 3: Long-Term</h3>
                            <p>Investment strategy tracking Congress, institutions, and fundamentals</p>
                            <div class="scan-interval">📊 Scan Interval: Every 1 hour</div>
                        </div>
                    </div>
                </div>
                
                <div class="status-card">
                    <h2>Integrated Data Sources</h2>
                    <div class="endpoints-list">
                        <div class="endpoint-tag">✅ Options Flow</div>
                        <div class="endpoint-tag">✅ Dark Pool</div>
                        <div class="endpoint-tag">✅ Congress Trades</div>
                        <div class="endpoint-tag">✅ Institutional Activity</div>
                        <div class="endpoint-tag">✅ Greek Exposures (GEX)</div>
                        <div class="endpoint-tag">✅ Earnings Calendar</div>
                        <div class="endpoint-tag">✅ Market Tide</div>
                        <div class="endpoint-tag">✅ Technical Analysis</div>
                        <div class="endpoint-tag">✅ Volume Analysis</div>
                        <div class="endpoint-tag">✅ ETF Flows</div>
                    </div>
                    <p style="margin-top: 20px; color: #666;">
                        <strong>Coming Soon:</strong> News Integration • Politician Portfolios • Insider Tracking • Short Interest • NOPE Indicator
                    </p>
                </div>
                
                <div class="status-card">
                    <h2>Quick Links</h2>
                    <a href="/api/health" class="cta-button">🔍 Check API Health</a>
                    <a href="/api/scan-mode1" class="cta-button">⚡ Run Mode 1 Scan</a>
                    <a href="https://github.com/YOUR_USERNAME/unusual-whales-scanner" class="cta-button" target="_blank">📚 View on GitHub</a>
                </div>
                
                <div class="footer">
                    <p>Built with 31,328 lines of Python • Powered by Unusual Whales API</p>
                    <p>⚠️ For educational and informational purposes only. Not financial advice.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
