#!/usr/bin/env python3
"""
Scanner Test Suite
Comprehensive testing before deployment
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

sys.path.insert(0, str(Path(__file__).parent))

console = Console()


async def test_1_configuration():
    """Test 1: Configuration loading"""
    console.print("\n[bold cyan]Test 1: Configuration Loading[/bold cyan]")
    
    try:
        from config import get_settings
        settings = get_settings()
        
        table = Table(box=box.SIMPLE)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_column("Status", style="green")
        
        # Check API key
        api_key_ok = len(settings.uw_api_key) > 10
        table.add_row(
            "API Key",
            f"{settings.uw_api_key[:10]}..." if api_key_ok else "MISSING",
            "✅" if api_key_ok else "❌"
        )
        
        # Check database
        db_ok = "postgresql" in settings.database_url.lower()
        table.add_row(
            "Database",
            settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url,
            "✅" if db_ok else "❌"
        )
        
        # Check Redis
        redis_ok = "redis" in settings.redis_url.lower()
        table.add_row(
            "Redis",
            settings.redis_url,
            "✅" if redis_ok else "❌"
        )
        
        # Check Mode 1
        table.add_row(
            "Mode 1 Enabled",
            str(settings.mode_1_enabled),
            "✅" if settings.mode_1_enabled else "⚠️"
        )
        
        table.add_row(
            "Mode 1 Ticker",
            settings.mode_1_ticker,
            "✅"
        )
        
        console.print(table)
        
        if api_key_ok and db_ok and redis_ok:
            console.print("[green]✅ Configuration OK[/green]")
            return True
        else:
            console.print("[red]❌ Configuration has issues[/red]")
            return False
    
    except Exception as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        return False


async def test_2_api_connection():
    """Test 2: API connectivity"""
    console.print("\n[bold cyan]Test 2: API Connection[/bold cyan]")
    
    try:
        from api import UnusualWhalesClient
        
        async with UnusualWhalesClient() as client:
            # Test simple endpoint
            console.print("  Testing API endpoint...")
            result = await client.get('/api/stock/SPY/stock-state', use_cache=False)
            
            if result and 'price' in result:
                console.print(f"[green]✅ API Connected - SPY Price: ${result['price']:.2f}[/green]")
                return True
            else:
                console.print("[yellow]⚠️ API connected but unexpected response[/yellow]")
                return False
    
    except Exception as e:
        console.print(f"[red]❌ API connection failed: {e}[/red]")
        return False


async def test_3_database_connection():
    """Test 3: Database connectivity"""
    console.print("\n[bold cyan]Test 3: Database Connection[/bold cyan]")
    
    try:
        from database import get_db_manager
        
        db = get_db_manager()
        db.initialize_async()
        
        async with db.get_async_session() as session:
            result = await session.execute("SELECT 1")
            value = result.scalar()
            
            if value == 1:
                console.print("[green]✅ Database Connected[/green]")
                return True
            else:
                console.print("[red]❌ Database query failed[/red]")
                return False
    
    except Exception as e:
        console.print(f"[red]❌ Database connection failed: {e}[/red]")
        console.print("[yellow]Note: Make sure PostgreSQL is running[/yellow]")
        return False


async def test_4_redis_connection():
    """Test 4: Redis connectivity"""
    console.print("\n[bold cyan]Test 4: Redis Connection[/bold cyan]")
    
    try:
        from database import get_redis_manager
        
        redis = get_redis_manager()
        await redis.connect()
        
        # Test set/get
        await redis.set('test_key', 'test_value', expire=10)
        value = await redis.get('test_key')
        
        await redis.disconnect()
        
        if value == 'test_value':
            console.print("[green]✅ Redis Connected[/green]")
            return True
        else:
            console.print("[red]❌ Redis test failed[/red]")
            return False
    
    except Exception as e:
        console.print(f"[red]❌ Redis connection failed: {e}[/red]")
        console.print("[yellow]Note: Make sure Redis is running[/yellow]")
        return False


async def test_5_scanner_initialization():
    """Test 5: Scanner initialization"""
    console.print("\n[bold cyan]Test 5: Scanner Initialization[/bold cyan]")
    
    try:
        from scanners import IntradaySPYScanner
        
        scanner = IntradaySPYScanner(ticker='SPY')
        
        # Initialize
        await scanner.initialize()
        
        console.print(f"  Scanner name: {scanner.name}")
        console.print(f"  Scanner mode: {scanner.mode.value}")
        console.print(f"  Ticker: {scanner.ticker}")
        console.print(f"  GEX threshold: ${scanner.gex_threshold:,.0f}")
        
        # Cleanup
        await scanner.cleanup()
        
        console.print("[green]✅ Scanner Initialized Successfully[/green]")
        return True
    
    except Exception as e:
        console.print(f"[red]❌ Scanner initialization failed: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False


async def test_6_data_fetching():
    """Test 6: Data fetching"""
    console.print("\n[bold cyan]Test 6: Data Fetching[/bold cyan]")
    
    try:
        from scanners import IntradaySPYScanner
        
        scanner = IntradaySPYScanner(ticker='SPY')
        await scanner.initialize()
        
        results = Table(box=box.SIMPLE)
        results.add_column("Data Source", style="cyan")
        results.add_column("Status", style="green")
        results.add_column("Records", style="yellow")
        
        # Test GEX
        try:
            gex_data = await scanner._fetch_gex_data()
            gex_ok = bool(gex_data)
            results.add_row("GEX Data", "✅" if gex_ok else "❌", "Available" if gex_ok else "None")
        except Exception as e:
            results.add_row("GEX Data", "❌", str(e)[:30])
        
        # Test Flow
        try:
            flow_data = await scanner._fetch_flow_data()
            flow_count = len(flow_data)
            results.add_row("Flow Alerts", "✅", str(flow_count))
        except Exception as e:
            results.add_row("Flow Alerts", "❌", str(e)[:30])
        
        # Test Dark Pool
        try:
            dark_pool_data = await scanner._fetch_dark_pool_data()
            dark_pool_count = len(dark_pool_data)
            results.add_row("Dark Pool", "✅", str(dark_pool_count))
        except Exception as e:
            results.add_row("Dark Pool", "❌", str(e)[:30])
        
        # Test Net Premium
        try:
            net_prem_data = await scanner._fetch_net_premium_data()
            net_prem_ok = bool(net_prem_data)
            results.add_row("Net Premium", "✅" if net_prem_ok else "❌", "Available" if net_prem_ok else "None")
        except Exception as e:
            results.add_row("Net Premium", "❌", str(e)[:30])
        
        console.print(results)
        
        await scanner.cleanup()
        
        console.print("[green]✅ Data Fetching Test Complete[/green]")
        return True
    
    except Exception as e:
        console.print(f"[red]❌ Data fetching failed: {e}[/red]")
        return False


async def test_7_single_scan():
    """Test 7: Full single scan"""
    console.print("\n[bold cyan]Test 7: Full Single Scan[/bold cyan]")
    
    try:
        from scanners import IntradaySPYScanner
        
        scanner = IntradaySPYScanner(ticker='SPY')
        await scanner.initialize()
        
        console.print("  Running scan...")
        results = await scanner.scan()
        
        console.print(f"\n  [green]Scan Results:[/green]")
        console.print(f"    Tickers scanned: {results.get('tickers_scanned', 0)}")
        console.print(f"    Signals found: {len(results.get('signals', []))}")
        console.print(f"    Alerts generated: {results.get('alerts_generated', 0)}")
        
        # Show first few signals
        signals = results.get('signals', [])
        if signals:
            console.print(f"\n  [yellow]Sample Signals:[/yellow]")
            for i, signal in enumerate(signals[:3], 1):
                console.print(f"    {i}. {signal.get('title', 'Unknown')}")
                console.print(f"       Priority: {signal.get('priority', 0)}/10 | Score: {signal.get('score', 0):.1f}/10")
        else:
            console.print("  [dim]No signals found (this is normal if market is quiet)[/dim]")
        
        await scanner.cleanup()
        
        console.print("[green]✅ Single Scan Successful[/green]")
        return True
    
    except Exception as e:
        console.print(f"[red]❌ Scan failed: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False


async def test_8_scoring_engine():
    """Test 8: Scoring engine"""
    console.print("\n[bold cyan]Test 8: Scoring Engine[/bold cyan]")
    
    try:
        from core import ScoringEngine
        
        engine = ScoringEngine()
        
        # Test individual scores
        flow_score = engine.score_flow_signal(premium=500000, volume=1000, unusual_factor=1.5)
        gex_score = engine.score_gex_signal(gex_value=2000000, distance_from_spot_pct=0.8)
        
        # Test composite
        composite = engine.calculate_composite_score(
            flow_score=flow_score,
            gex_score=gex_score,
            dark_pool_score=6.0
        )
        
        console.print(f"  Flow Score: {flow_score:.2f}/10")
        console.print(f"  GEX Score: {gex_score:.2f}/10")
        console.print(f"  Composite Score: {composite.composite:.2f}/10")
        console.print(f"  Strength: {composite.strength.name}")
        console.print(f"  Confidence: {composite.confidence:.0%}")
        
        console.print("[green]✅ Scoring Engine Working[/green]")
        return True
    
    except Exception as e:
        console.print(f"[red]❌ Scoring engine failed: {e}[/red]")
        return False


async def main():
    """Run all tests"""
    console.print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🧪 SCANNER TEST SUITE 🧪                           ║
║              Pre-Deployment Validation                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """, style="bold cyan")
    
    tests = [
        ("Configuration", test_1_configuration),
        ("API Connection", test_2_api_connection),
        ("Database Connection", test_3_database_connection),
        ("Redis Connection", test_4_redis_connection),
        ("Scanner Initialization", test_5_scanner_initialization),
        ("Data Fetching", test_6_data_fetching),
        ("Single Scan", test_7_single_scan),
        ("Scoring Engine", test_8_scoring_engine),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"[red]Test crashed: {e}[/red]")
            results.append((test_name, False))
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]TEST SUMMARY[/bold cyan]")
    console.print("="*60 + "\n")
    
    summary_table = Table(box=box.ROUNDED)
    summary_table.add_column("Test", style="cyan")
    summary_table.add_column("Result", justify="center")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            summary_table.add_row(test_name, "[green]✅ PASS[/green]")
            passed += 1
        else:
            summary_table.add_row(test_name, "[red]❌ FAIL[/red]")
            failed += 1
    
    console.print(summary_table)
    
    console.print(f"\n[bold]Results: {passed} passed, {failed} failed[/bold]")
    
    if failed == 0:
        console.print("\n[bold green]🎉 ALL TESTS PASSED! Scanner is ready to use! 🎉[/bold green]")
        console.print("\n[yellow]Next step: Run the scanner with:[/yellow]")
        console.print("[cyan]python run_scanner.py --once[/cyan]")
        return 0
    else:
        console.print("\n[bold red]⚠️  Some tests failed. Please fix issues before using scanner.[/bold red]")
        
        if any("Database" in name for name, result in results if not result):
            console.print("\n[yellow]Database tip:[/yellow] Make sure PostgreSQL is running:")
            console.print("  macOS: brew services start postgresql")
            console.print("  Linux: sudo systemctl start postgresql")
        
        if any("Redis" in name for name, result in results if not result):
            console.print("\n[yellow]Redis tip:[/yellow] Make sure Redis is running:")
            console.print("  macOS: brew services start redis")
            console.print("  Linux: sudo systemctl start redis")
        
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
