"""
Vercel API Route - Health Check Endpoint
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.client import UnusualWhalesClient
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Get API key from environment
        api_key = os.getenv('UNUSUAL_WHALES_API_KEY')
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': 'production',
            'checks': {
                'client_import': CLIENT_AVAILABLE,
                'api_key_configured': bool(api_key),
                'vercel_deployment': True
            }
        }
        
        # Try to ping UW API if client is available
        if CLIENT_AVAILABLE and api_key:
            try:
                client = UnusualWhalesClient(api_key=api_key)
                # Quick test - get market general data
                test_response = client.get_market_general()
                health_status['checks']['api_connection'] = True
                health_status['checks']['api_response'] = 'success'
            except Exception as e:
                health_status['checks']['api_connection'] = False
                health_status['checks']['api_error'] = str(e)
                health_status['status'] = 'degraded'
        
        response = json.dumps(health_status, indent=2)
        self.wfile.write(response.encode())
