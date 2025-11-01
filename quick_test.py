#!/usr/bin/env python3
"""
Quick API Connection Test
Tests basic API connectivity without database/Redis dependencies
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🔍 QUICK API CONNECTION TEST 🔍                    ║
║         Testing Unusual Whales API Access                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

async def test_api_connection():
    """Test basic API connectivity"""
    try:
        print("\n1️⃣  Checking for API Key...")
        
        # Try to get API key from environment
        api_key = os.getenv("UW_API_KEY")
        
        if not api_key:
            print("❌ No API key found in environment")
            print("\n💡 Please set your API key:")
            print("   export UW_API_KEY='your_api_key_here'")
            print("\n   Or create a .env file:")
            print("   echo 'UW_API_KEY=your_api_key_here' > .env")
            return False
            
        print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
        
        print("\n2️⃣  Testing API Connection...")
        
        import aiohttp
        
        # Test a simple endpoint - stock state for SPY
        url = "https://api.unusualwhales.com/api/stock/SPY/stock-state"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    print("✅ API Connection Successful!")
                    print(f"\n📊 SPY Stock State Retrieved:")
                    if 'data' in data:
                        info = data['data']
                        print(f"   Symbol: SPY")
                        print(f"   Price: ${info.get('price', 'N/A')}")
                        print(f"   Volume: {info.get('volume', 'N/A'):,}")
                    else:
                        print(f"   Data: {str(data)[:200]}")
                    return True
                elif status == 401:
                    print("❌ Authentication Failed")
                    print("   Your API key may be invalid or expired")
                    print("   Please check your Unusual Whales subscription")
                    return False
                elif status == 429:
                    print("⚠️  Rate Limit Exceeded")
                    print("   Too many requests. Wait a moment and try again.")
                    return False
                else:
                    text = await response.text()
                    print(f"❌ API Error: Status {status}")
                    print(f"   Response: {text[:200]}")
                    return False
                    
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install aiohttp")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_options_endpoint():
    """Test options flow endpoint"""
    try:
        print("\n3️⃣  Testing Options Flow Endpoint...")
        
        api_key = os.getenv("UW_API_KEY")
        if not api_key:
            return False
            
        import aiohttp
        
        # Test options flow endpoint
        url = "https://api.unusualwhales.com/api/option-trades/flow-alerts"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        params = {
            "symbol": "SPY",
            "limit": 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    print("✅ Options Flow Endpoint Working!")
                    
                    if isinstance(data, dict) and 'data' in data:
                        flows = data['data'][:3]  # First 3 flows
                    elif isinstance(data, list):
                        flows = data[:3]
                    else:
                        flows = []
                    
                    if flows:
                        print(f"\n📈 Recent SPY Options Flow (showing {len(flows)}):")
                        for i, flow in enumerate(flows, 1):
                            side = flow.get('side', 'N/A')
                            size = flow.get('size', 0)
                            premium = flow.get('premium', 0)
                            strike = flow.get('strike', 'N/A')
                            print(f"   {i}. {side} {size} contracts @ ${strike} (${premium:,.0f})")
                    return True
                else:
                    print(f"⚠️  Options endpoint returned status {status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Options test error: {e}")
        return False

async def main():
    """Run all quick tests"""
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    results = []
    
    # Test 1: Basic API Connection
    result1 = await test_api_connection()
    results.append(("API Connection", result1))
    
    if result1:
        # Test 2: Options Flow (only if basic connection works)
        result2 = await test_options_endpoint()
        results.append(("Options Flow", result2))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nResults: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Your API connection is working!")
        print("✅ Ready to run the full scanner")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        
    return passed_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
