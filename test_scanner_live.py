#!/usr/bin/env python3
"""
Live Scanner Test - Tests actual scanning logic with real API data
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🚀 LIVE SCANNER TEST 🚀                            ║
║         Testing Scanner Logic with Real API Data             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

async def test_scanner_data_fetching():
    """Test fetching all required data for scanner"""
    try:
        print("\n1️⃣  Importing Scanner Components...")
        from api.client import UnusualWhalesClient
        from config.settings import Settings
        
        settings = Settings()
        print(f"✅ Settings loaded")
        print(f"   API Key: {settings.UW_API_KEY[:10]}...{settings.UW_API_KEY[-4:]}")
        
        print("\n2️⃣  Initializing API Client...")
        client = UnusualWhalesClient(
            api_key=settings.UW_API_KEY,
            rate_limit=10.0
        )
        print("✅ Client initialized")
        
        ticker = "SPY"
        
        # Test 1: Stock State
        print(f"\n3️⃣  Fetching Stock State for {ticker}...")
        stock_state = await client.get_stock_state(ticker)
        if stock_state:
            data = stock_state.get('data', {})
            price = data.get('price', 'N/A')
            volume = data.get('volume', 'N/A')
            print(f"✅ Stock State Retrieved")
            print(f"   Price: ${price}")
            print(f"   Volume: {volume:,}" if isinstance(volume, (int, float)) else f"   Volume: {volume}")
        else:
            print("⚠️  No stock state data")
        
        # Test 2: Greeks (for GEX)
        print(f"\n4️⃣  Fetching Greeks for {ticker}...")
        greeks = await client.get_greeks(ticker)
        if greeks and 'data' in greeks:
            greek_data = greeks['data']
            print(f"✅ Greeks Retrieved: {len(greek_data)} records")
            if len(greek_data) > 0:
                sample = greek_data[0]
                print(f"   Sample: Strike={sample.get('strike')}, Call Delta={sample.get('call_delta')}, Put Delta={sample.get('put_delta')}")
        else:
            print("⚠️  No greeks data")
        
        # Test 3: Options Flow
        print(f"\n5️⃣  Fetching Options Flow Alerts...")
        flow_params = {
            "limit": 10,
            "ticker": ticker
        }
        flow = await client.get_flow_alerts(**flow_params)
        if flow and 'data' in flow:
            flow_data = flow['data']
            print(f"✅ Flow Alerts Retrieved: {len(flow_data)} records")
            if len(flow_data) > 0:
                for i, trade in enumerate(flow_data[:3], 1):
                    strike = trade.get('strike', 'N/A')
                    premium = trade.get('total_premium', 0)
                    volume = trade.get('volume', 0)
                    print(f"   {i}. Strike ${strike}, Premium ${premium:,.0f}, Volume {volume}")
        else:
            print("⚠️  No flow data")
        
        # Test 4: Dark Pool
        print(f"\n6️⃣  Fetching Dark Pool Data for {ticker}...")
        darkpool_params = {
            "limit": 10
        }
        darkpool = await client.get_darkpool(ticker, **darkpool_params)
        if darkpool and 'data' in darkpool:
            dp_data = darkpool['data']
            print(f"✅ Dark Pool Retrieved: {len(dp_data)} records")
            if len(dp_data) > 0:
                total_premium = sum(float(d.get('premium', 0)) for d in dp_data)
                total_size = sum(int(d.get('size', 0)) for d in dp_data)
                print(f"   Total Premium (last 10): ${total_premium:,.2f}")
                print(f"   Total Size (last 10): {total_size:,} shares")
        else:
            print("⚠️  No dark pool data")
        
        # Test 5: Net Premium Ticks
        print(f"\n7️⃣  Fetching Net Premium Ticks for {ticker}...")
        net_prem = await client.get_net_prem_ticks(ticker)
        if net_prem and 'data' in net_prem:
            np_data = net_prem['data']
            print(f"✅ Net Premium Ticks Retrieved: {len(np_data)} records")
            if len(np_data) > 0:
                latest = np_data[0]
                call_vol = latest.get('call_volume', 0)
                put_vol = latest.get('put_volume', 0)
                ratio = call_vol / put_vol if put_vol > 0 else 0
                print(f"   Latest: Call Volume={call_vol:,}, Put Volume={put_vol:,}")
                print(f"   Call/Put Ratio: {ratio:.2f}")
        else:
            print("⚠️  No net premium data")
        
        await client.close()
        print("\n✅ All data fetching tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Scanner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scoring_system():
    """Test the scoring algorithms"""
    try:
        print("\n\n8️⃣  Testing Scoring System...")
        from core.scoring import ScoringEngine
        
        scorer = ScoringEngine()
        
        # Test GEX scoring
        test_gex = {
            "gamma_per_one_percent_move_dir": 5000000,  # Strong positive GEX
            "price": 575.0,
            "spot_price": 573.0  # Very close to GEX level
        }
        
        gex_score = scorer.score_gex_pivot(
            gex_value=test_gex["gamma_per_one_percent_move_dir"],
            price_level=test_gex["price"],
            spot_price=test_gex["spot_price"]
        )
        print(f"✅ GEX Scoring Works")
        print(f"   Test: ${test_gex['price']} GEX level with spot at ${test_gex['spot_price']}")
        print(f"   Score: {gex_score}/10")
        
        # Test Flow scoring
        test_flow = {
            "call_premium": 50000000,
            "put_premium": 10000000,
            "large_trades": 15
        }
        
        flow_score = scorer.score_flow_pressure(
            call_premium=test_flow["call_premium"],
            put_premium=test_flow["put_premium"],
            large_trade_count=test_flow["large_trades"]
        )
        print(f"\n✅ Flow Scoring Works")
        print(f"   Test: ${test_flow['call_premium']:,} calls vs ${test_flow['put_premium']:,} puts")
        print(f"   Score: {flow_score}/10")
        
        # Test composite scoring
        composite = scorer.calculate_composite_score({
            'gex_score': gex_score,
            'flow_score': flow_score,
            '0dte_score': 7.0,
            'darkpool_score': 6.0
        })
        print(f"\n✅ Composite Scoring Works")
        print(f"   Combined Score: {composite['total_score']:.1f}/10")
        print(f"   Strength: {composite['strength']}")
        print(f"   Confidence: {composite['confidence']:.0f}%")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    results = []
    
    # Test 1: Data Fetching
    result1 = await test_scanner_data_fetching()
    results.append(("Data Fetching", result1))
    
    # Test 2: Scoring System
    result2 = await test_scoring_system()
    results.append(("Scoring System", result2))
    
    # Summary
    print("\n" + "="*60)
    print("LIVE SCANNER TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nResults: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Scanner is ready to run!")
        print("\n📝 Next Steps:")
        print("   1. Run: python run_scanner.py")
        print("   2. The scanner will start monitoring SPY")
        print("   3. Press Ctrl+C to stop")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        
    return passed_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
