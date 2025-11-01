"""
Quick API Connection Test
Run this to verify your API key and connection
"""
import asyncio
from rich.console import Console
from rich.table import Table
from rich import box
from api import UnusualWhalesClient

console = Console()


async def test_connection():
    """Test basic API connectivity"""
    
    console.print("\n[bold cyan]🐋 Testing Unusual Whales API Connection[/bold cyan]\n")
    
    try:
        async with UnusualWhalesClient() as client:
            console.print("[yellow]→[/yellow] Connecting to API...")
            
            # Test 1: Get SPY flow alerts
            console.print("[yellow]→[/yellow] Fetching SPY flow alerts...")
            flow = await client.get_flow_alerts(ticker='SPY', limit=5)
            flow_count = len(flow.get('data', []))
            
            # Test 2: Get SPY GEX
            console.print("[yellow]→[/yellow] Fetching SPY gamma exposure...")
            gex = await client.get_spot_exposures('SPY')
            
            # Test 3: Get market top movers
            console.print("[yellow]→[/yellow] Fetching market top movers...")
            top_impact = await client.get_market_top_net_impact(limit=5)
            top_count = len(top_impact.get('data', []))
            
            # Test 4: Get institutional filings
            console.print("[yellow]→[/yellow] Fetching institutional filings...")
            inst = await client.get_institution_latest_filings(limit=5)
            inst_count = len(inst.get('data', []))
            
            # Test 5: Get Congress trades
            console.print("[yellow]→[/yellow] Fetching Congressional trades...")
            congress = await client.get_congress_recent_trades(limit=5)
            congress_count = len(congress.get('data', []))
            
            # Display results
            console.print("\n[bold green]✅ Connection Successful![/bold green]\n")
            
            # Create results table
            table = Table(title="API Test Results", box=box.ROUNDED)
            table.add_column("Endpoint", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Records", justify="right", style="yellow")
            
            table.add_row("Flow Alerts (SPY)", "✅ Success", str(flow_count))
            table.add_row("Gamma Exposure (SPY)", "✅ Success", "Available")
            table.add_row("Market Top Impact", "✅ Success", str(top_count))
            table.add_row("Institutional Filings", "✅ Success", str(inst_count))
            table.add_row("Congressional Trades", "✅ Success", str(congress_count))
            
            console.print(table)
            
            # Display client stats
            stats = client.get_stats()
            console.print(f"\n[bold]API Statistics:[/bold]")
            console.print(f"  Total Requests: {stats['total_requests']}")
            console.print(f"  Successful: {stats['successful_requests']}")
            console.print(f"  Cache Hits: {stats['cache_hits']}")
            console.print(f"  Rate Limiter:")
            console.print(f"    Current Rate: {stats['rate_limiter']['current_rate']:.1f} req/s")
            console.print(f"    Total Waits: {stats['rate_limiter']['total_waits']}")
            
            # Sample data preview
            if flow_count > 0:
                console.print("\n[bold cyan]Sample Flow Alert:[/bold cyan]")
                sample = flow['data'][0]
                console.print(f"  Ticker: [yellow]{sample.get('ticker', 'N/A')}[/yellow]")
                console.print(f"  Strike: ${sample.get('strike', 0):,.2f}")
                console.print(f"  Premium: ${sample.get('premium', 0):,.0f}")
                console.print(f"  Type: {sample.get('option_type', 'N/A')}")
            
            console.print("\n[green]🎉 All tests passed! Your API is working perfectly.[/green]\n")
            return True
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Connection Failed![/bold red]")
        console.print(f"[red]Error: {e}[/red]\n")
        console.print("[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Check your API key in .env file")
        console.print("  2. Verify your API subscription is active")
        console.print("  3. Check your internet connection")
        console.print("  4. Review rate limits\n")
        return False


if __name__ == '__main__':
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
