import asyncio
import aiohttp
import json

async def test_endpoints():
    api_key = '72cac8bd-c1c5-488b-ad48-58d554be20d9'
    
    # Test actual endpoints from the OpenAPI spec
    tests = [
        ("Market Tide", "https://api.unusualwhales.com/api/market/market-tide"),
        ("SPY Greeks", "https://api.unusualwhales.com/api/stock/SPY/greeks"),
        ("Flow Alerts", "https://api.unusualwhales.com/api/option-trades/flow-alerts?limit=5"),
        ("Dark Pool Recent", "https://api.unusualwhales.com/api/darkpool/recent?limit=5"),
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        for name, url in tests:
            try:
                print(f"\n{'='*60}")
                print(f"Testing: {name}")
                print(f"URL: {url}")
                print("="*60)
                
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    print(f"Status: {status}")
                    
                    if status == 200:
                        data = await response.json()
                        print(f"✅ SUCCESS!")
                        print(f"Response preview:")
                        print(json.dumps(data, indent=2)[:500])
                        print("...")
                    elif status == 401:
                        print(f"❌ AUTH FAILED - Invalid API key")
                    elif status == 429:
                        print(f"⚠️  RATE LIMITED")
                    else:
                        text = await response.text()
                        print(f"❌ Error: {text[:200]}")
                        
            except Exception as e:
                print(f"❌ Exception: {e}")

asyncio.run(test_endpoints())
