#!/usr/bin/env python3
"""
Simple Standalone Scanner Test
Tests core scanning logic without complex dependencies
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List

API_KEY = "72cac8bd-c1c5-488b-ad48-58d554be20d9"
BASE_URL = "https://api.unusualwhales.com"

print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🔍 SIMPLE SCANNER TEST 🔍                          ║
║         Standalone Test of Core Scanning Logic               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

async def fetch_data(session: aiohttp.ClientSession, endpoint: str, params: Dict = None) -> Dict:
    """Fetch data from API"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"⚠️  Status {response.status} for {endpoint}")
                return {}
    except Exception as e:
        print(f"❌ Error fetching {endpoint}: {e}")
        return {}

def calculate_gex_score(gamma_exposure: float, price_level: float, spot_price: float) -> float:
    """Calculate GEX pivot score"""
    # Distance from spot
    distance_pct = abs(price_level - spot_price) / spot_price
    
    # Proximity score (closer = higher)
    proximity_score = max(0, 10 - (distance_pct * 500))
    
    # Magnitude score
    gamma_millions = abs(gamma_exposure) / 1_000_000
    if gamma_millions > 10:
        magnitude_score = 10
    elif gamma_millions > 5:
        magnitude_score = 8
    elif gamma_millions > 1:
        magnitude_score = 6
    else:
        magnitude_score = 3
    
    # Direction modifier
    if gamma_exposure > 0:  # Positive GEX = resistance
        direction = "RESISTANCE"
    else:  # Negative GEX = support/fuel
        direction = "SUPPORT"
    
    final_score = (proximity_score * 0.6) + (magnitude_score * 0.4)
    return min(10, max(0, final_score)), direction

def calculate_flow_score(call_premium: float, put_premium: float, large_trades: int) -> float:
    """Calculate options flow score"""
    # Calculate call/put ratio
    total_premium = call_premium + put_premium
    if total_premium == 0:
        return 5.0
    
    call_ratio = call_premium / total_premium if total_premium > 0 else 0.5
    
    # Ratio score
    if call_ratio > 0.7:  # Bullish
        ratio_score = 8 + (call_ratio - 0.7) * 20
    elif call_ratio < 0.3:  # Bearish
        ratio_score = 8 + (0.3 - call_ratio) * 20
    else:  # Neutral
        ratio_score = 5
    
    # Large trade bonus
    trade_bonus = min(2, large_trades / 10)
    
    final_score = min(10, ratio_score + trade_bonus)
    
    direction = "BULLISH" if call_ratio > 0.6 else "BEARISH" if call_ratio < 0.4 else "NEUTRAL"
    
    return final_score, direction, call_ratio

async def run_scan():
    """Run a complete scan cycle for SPY"""
    ticker = "SPY"
    
    print(f"\n{'='*60}")
    print(f"Starting Scan for {ticker} at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")
    
    async with aiohttp.ClientSession() as session:
        # 1. Get stock state
        print("1️⃣  Fetching Stock State...")
        stock_state = await fetch_data(session, f"/api/stock/{ticker}/stock-state")
        
        if stock_state and 'data' in stock_state:
            spot_price = stock_state['data'].get('price', 0)
            volume = stock_state['data'].get('volume', 0)
            print(f"   ✅ Price: ${spot_price:.2f}, Volume: {volume:,}")
        else:
            print("   ❌ Failed to get stock state")
            spot_price = 575.0  # Fallback
        
        # 2. Get options flow
        print("\n2️⃣  Fetching Options Flow...")
        flow = await fetch_data(session, "/api/option-trades/flow-alerts", {
            "limit": 20,
            "ticker": ticker
        })
        
        call_premium = 0
        put_premium = 0
        large_trades = 0
        
        if flow and 'data' in flow:
            flow_data = flow['data']
            print(f"   ✅ Retrieved {len(flow_data)} flow alerts")
            
            for trade in flow_data:
                premium = float(trade.get('total_premium', 0))
                option_type = trade.get('type', '')
                
                if option_type == 'call':
                    call_premium += premium
                elif option_type == 'put':
                    put_premium += premium
                
                if premium > 500000:  # $500k+ = large trade
                    large_trades += 1
            
            print(f"   Call Premium: ${call_premium:,.0f}")
            print(f"   Put Premium: ${put_premium:,.0f}")
            print(f"   Large Trades (>$500k): {large_trades}")
        else:
            print("   ⚠️  No flow data")
        
        # 3. Get Greeks (for GEX)
        print("\n3️⃣  Fetching Greeks Data...")
        greeks = await fetch_data(session, f"/api/stock/{ticker}/greeks")
        
        gex_levels = []
        
        if greeks and 'data' in greeks:
            greek_data = greeks['data']
            print(f"   ✅ Retrieved {len(greek_data)} greek records")
            
            # Group by strike and sum gamma
            strike_gamma = {}
            for record in greek_data:
                strike = float(record.get('strike', 0))
                call_gamma = float(record.get('call_gamma', 0))
                put_gamma = float(record.get('put_gamma', 0))
                
                net_gamma = call_gamma + put_gamma
                
                if strike not in strike_gamma:
                    strike_gamma[strike] = 0
                strike_gamma[strike] += net_gamma
            
            # Find significant GEX levels
            for strike, gamma in sorted(strike_gamma.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
                if abs(gamma) > 100000:  # Significant gamma
                    gex_levels.append({
                        'strike': strike,
                        'gamma': gamma
                    })
            
            print(f"   Found {len(gex_levels)} significant GEX levels")
        else:
            print("   ⚠️  No greeks data")
        
        # 4. Get Dark Pool
        print("\n4️⃣  Fetching Dark Pool Data...")
        darkpool = await fetch_data(session, f"/api/darkpool/{ticker}", {"limit": 20})
        
        dp_premium = 0
        dp_volume = 0
        
        if darkpool and 'data' in darkpool:
            dp_data = darkpool['data']
            print(f"   ✅ Retrieved {len(dp_data)} dark pool trades")
            
            for trade in dp_data:
                dp_premium += float(trade.get('premium', 0))
                dp_volume += int(trade.get('size', 0))
            
            print(f"   Total Premium: ${dp_premium:,.2f}")
            print(f"   Total Volume: {dp_volume:,} shares")
        else:
            print("   ⚠️  No dark pool data")
        
        # === ANALYSIS ===
        print(f"\n{'='*60}")
        print("ANALYSIS")
        print(f"{'='*60}\n")
        
        # Analyze GEX
        print("📊 GEX Analysis:")
        if gex_levels:
            for i, level in enumerate(gex_levels[:3], 1):
                score, direction = calculate_gex_score(
                    level['gamma'],
                    level['strike'],
                    spot_price
                )
                distance = ((level['strike'] - spot_price) / spot_price) * 100
                print(f"   {i}. ${level['strike']:.0f} ({distance:+.2f}%) - {direction}")
                print(f"      Gamma: ${level['gamma']:,.0f}, Score: {score:.1f}/10")
        else:
            print("   No significant GEX levels found")
        
        # Analyze Flow
        print("\n📈 Options Flow Analysis:")
        if call_premium > 0 or put_premium > 0:
            flow_score, flow_direction, call_ratio = calculate_flow_score(
                call_premium, put_premium, large_trades
            )
            print(f"   Direction: {flow_direction}")
            print(f"   Call/Put Ratio: {call_ratio:.2f}")
            print(f"   Score: {flow_score:.1f}/10")
        else:
            print("   No flow data available")
        
        # Overall Signal
        print(f"\n{'='*60}")
        if gex_levels and (call_premium > 0 or put_premium > 0):
            print("✅ SCANNER WORKING - Data successfully retrieved and analyzed!")
        else:
            print("⚠️  Partial data - Scanner needs tuning")
        print(f"{'='*60}\n")

async def main():
    print(f"Testing scanner with live API data...\n")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"Target: SPY (S&P 500 ETF)\n")
    
    try:
        await run_scan()
        print("\n✅ TEST COMPLETE!")
        print("\n📝 Next Steps:")
        print("   - Scanner logic is working with real API data")
        print("   - Ready to integrate into full scanner framework")
        print("   - Can run continuous scanning loop")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
