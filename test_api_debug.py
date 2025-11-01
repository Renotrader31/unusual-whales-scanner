import asyncio
import aiohttp
import json

async def test_endpoints():
    api_key = '72cac8bd-c1c5-488b-ad48-58d554be20d9'
    
    # Try different endpoint patterns
    endpoints = [
        "https://api.unusualwhales.com/api/stock/SPY",
        "https://api.unusualwhales.com/stock/SPY",
        "https://api.unusualwhales.com/v1/stock/SPY",
        "https://phx.unusualwhales.com/api/stock/SPY",
        "https://api.unusualwhales.com/api/options/flow?symbol=SPY&limit=1",
        "https://api.unusualwhales.com/api/market/overview",
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        for url in endpoints:
            try:
                print(f"\nTrying: {url}")
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    print(f"Status: {status}")
                    
                    if status == 200:
                        data = await response.json()
                        print(f"✅ SUCCESS! Data: {json.dumps(data, indent=2)[:500]}")
                        break
                    else:
                        text = await response.text()
                        print(f"Response: {text[:200]}")
            except Exception as e:
                print(f"Error: {e}")

asyncio.run(test_endpoints())
