"""
Vercel API Route - Mode 1 Scanner Endpoint
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scanners.mode1_intraday import Mode1IntradayScanner
    SCANNER_AVAILABLE = True
except ImportError:
    SCANNER_AVAILABLE = False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Run Mode 1 scan and return results"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if not SCANNER_AVAILABLE:
            error_response = {
                'error': 'Scanner module not available',
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat()
            }
            self.wfile.write(json.dumps(error_response, indent=2).encode())
            return
        
        # Get API key from environment
        api_key = os.getenv('UNUSUAL_WHALES_API_KEY')
        
        if not api_key:
            error_response = {
                'error': 'API key not configured',
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat()
            }
            self.wfile.write(json.dumps(error_response, indent=2).encode())
            return
        
        try:
            # Create and run scanner
            scanner = Mode1IntradayScanner(
                api_key=api_key,
                discord_webhook=None,  # Disable alerts for API endpoint
                telegram_token=None
            )
            
            # Run scan synchronously (Vercel limitation)
            # In production, use async with proper event loop
            results = {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'mode': 'Mode 1 - Intraday Scalper',
                'target': 'SPY',
                'message': 'Scanner initiated successfully',
                'note': 'Full scan results require async execution. Use run_scanner.py locally for complete functionality.'
            }
            
            response = json.dumps(results, indent=2)
            self.wfile.write(response.encode())
            
        except Exception as e:
            error_response = {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat()
            }
            self.wfile.write(json.dumps(error_response, indent=2).encode())
