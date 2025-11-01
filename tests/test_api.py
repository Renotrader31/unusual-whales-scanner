"""
Test script to validate Unusual Whales API connection
Run this to verify your API key and test basic functionality
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.client import UWClient
from config.settings import settings
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import orjson


console = Console()


async def test_api_connection():
    """Test basic API connectivity."""
    console.print("[bold cyan]Testing Unusual Whales API Connection...[/bold cyan]\n")
    
    try:
        async with UWClient() as client:
            # Test 1: Check API key is configured
            console.print("[yellow]Test 1: API Key Configuration[/yellow]")
            if not settings.uw_api_key or settings.uw_api_key == 'your_api_key_here':
                console.print("[red]✗ API key not configured![/red]")
                console.print("[yellow]Please set UW_API_KEY in your .env file[/yellow]")
                return False
            console.print(f"[green]✓ API key configured: {settings.uw_api_key[:10]}...[/green]\n")
            
            # Test 2: Get SPY stock state
            console.print("[yellow]Test 2: Fetch SPY Stock State[/yellow]")
            try:
                spy_state = await client.get_stock_state('SPY')
                console.print(f"[green]✓ Successfully fetched SPY data[/green]")
                console.print(f"  Last Price: ${spy_state.get('last_price', 'N/A')}")
                console.print(f"  Volume: {spy_state.get('volume', 'N/A'):,}\n")
            except Exception as e:
                console.print(f"[red]✗ Failed: {e}[/red]\n")
                return False
            
            # Test 3: Get flow alerts
            console.print("[yellow]Test 3: Fetch Options Flow Alerts[/yellow]")
            try:
                flow_alerts = await client.get_flow_alerts()
                alert_count = len(flow_alerts.get('data', []))
                console.print(f"[green]✓ Successfully fetched {alert_count} flow alerts[/green]")
                
                if alert_count > 0:
                    # Show first alert
                    first_alert = flow_alerts['data'][0]
                    console.print(f"  Latest alert: {first_alert.get('ticker', 'N/A')} "
                                f"{first_alert.get('strike', 'N/A')} "
                                f"{first_alert.get('option_type', 'N/A')}\n")
            except Exception as e:
                console.print(f"[red]✗ Failed: {e}[/red]\n")
                return False
            
            # Test 4: Get GEX data for SPY
            console.print("[yellow]Test 4: Fetch SPY Gamma Exposure (GEX)[/yellow]")
            try:
                gex_data = await client.get_spot_exposures('SPY')
                console.print(f"[green]✓ Successfully fetched GEX data[/green]")
                
                if gex_data and isinstance(gex_data, dict):
                    data_points = len(gex_data.get('data', []))
                    console.print(f"  Data points: {data_points}\n")
            except Exception as e:
                console.print(f"[red]✗ Failed: {e}[/red]\n")
                return False
            
            # Test 5: Get dark pool data
            console.print("[yellow]Test 5: Fetch Dark Pool Data[/yellow]")
            try:
                dark_pool = await client.get_dark_pool('SPY')
                console.print(f"[green]✓ Successfully fetched dark pool data[/green]")
                
                if dark_pool and isinstance(dark_pool, dict):
                    trades = len(dark_pool.get('data', []))
                    console.print(f"  Recent trades: {trades}\n")
            except Exception as e:
                console.print(f"[red]✗ Failed: {e}[/red]\n")
                return False
            
            # Test 6: Get institutional data
            console.print("[yellow]Test 6: Fetch Latest Institutional Filings[/yellow]")
            try:
                filings = await client.get_latest_filings()
                console.print(f"[green]✓ Successfully fetched institutional filings[/green]")
                
                if filings and isinstance(filings, dict):
                    filing_count = len(filings.get('data', []))
                    console.print(f"  Recent filings: {filing_count}\n")
            except Exception as e:
                console.print(f"[red]✗ Failed: {e}[/red]\n")
                return False
            
            # Test 7: Get congress trades
            console.print("[yellow]Test 7: Fetch Congressional Trades[/yellow]")
            try:
                congress = await client.get_congress_trades()
                console.print(f"[green]✓ Successfully fetched congressional trades[/green]")
                
                if congress and isinstance(congress, dict):
                    trade_count = len(congress.get('data', []))
                    console.print(f"  Recent trades: {trade_count}\n")
            except Exception as e:
                console.print(f"[red]✗ Failed: {e}[/red]\n")
                # Congress endpoint might not be available for all plans
                console.print("[yellow]  Note: This endpoint may require specific API plan[/yellow]\n")
            
            # Show client stats
            stats = client.get_stats()
            
            table = Table(title="API Client Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Requests", str(stats['total_requests']))
            table.add_row("Successful", str(stats['successful_requests']))
            table.add_row("Failed", str(stats['failed_requests']))
            table.add_row("Cache Hits", str(stats['cache_hits']))
            table.add_row("Cache Size", str(stats['cache_size']))
            table.add_row("Rate Limit Utilization", 
                         f"{stats['rate_limiter']['utilization_pct']:.1f}%")
            
            console.print(table)
            
            console.print("\n[bold green]✓ All tests passed successfully![/bold green]")
            console.print("[cyan]Your API connection is working correctly.[/cyan]")
            console.print("[cyan]You're ready to start building your scanner![/cyan]")
            
            return True
            
    except Exception as e:
        console.print(f"\n[bold red]✗ Connection test failed: {e}[/bold red]")
        return False


async def test_endpoints_summary():
    """Test and show available endpoints."""
    console.print("\n[bold cyan]Testing Available Endpoints...[/bold cyan]\n")
    
    endpoints_to_test = [
        ("Market Data", [
            ("Top Net Impact", lambda c: c.get_top_net_impact(limit=5)),
            ("Market Correlations", lambda c: c.get_market_correlations(['SPY', 'QQQ'])),
        ]),
        ("Stock Data", [
            ("SPY State", lambda c: c.get_stock_state('SPY')),
            ("SPY OI per Strike", lambda c: c.get_oi_per_strike('SPY')),
            ("SPY Greeks", lambda c: c.get_greeks('SPY')),
        ]),
        ("Options Flow", [
            ("Flow Alerts", lambda c: c.get_flow_alerts()),
        ]),
    ]
    
    async with UWClient() as client:
        for category, endpoints in endpoints_to_test:
            console.print(f"[bold yellow]{category}[/bold yellow]")
            
            for name, fetch_func in endpoints:
                try:
                    await fetch_func(client)
                    console.print(f"  [green]✓ {name}[/green]")
                except Exception as e:
                    console.print(f"  [red]✗ {name}: {str(e)[:50]}[/red]")
            
            console.print()


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]Unusual Whales Scanner - API Connection Test[/bold cyan]\n"
        "This will validate your API key and test key endpoints.",
        border_style="cyan"
    ))
    
    try:
        # Run basic connection test
        result = asyncio.run(test_api_connection())
        
        if result:
            # Run detailed endpoint test
            asyncio.run(test_endpoints_summary())
        else:
            console.print("\n[red]Please fix the issues above and try again.[/red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Test cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
