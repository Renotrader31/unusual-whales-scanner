"""
Basic Usage Examples for UW Scanner
Demonstrates key functionality with practical examples
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.client import UWClient
from api.websocket_client import UWWebSocketClient
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
import orjson

console = Console()


async def example_1_spy_analysis():
    """Example 1: Comprehensive SPY Analysis."""
    console.print(Panel("[bold cyan]Example 1: SPY Deep Dive Analysis[/bold cyan]"))
    
    async with UWClient() as client:
        # 1. Current stock state
        console.print("\n[yellow]📊 Current SPY State[/yellow]")
        state = await client.get_stock_state('SPY')
        console.print(f"  Last Price: ${state.get('last_price', 0):.2f}")
        console.print(f"  Volume: {state.get('volume', 0):,}")
        console.print(f"  Prev Close: ${state.get('prev_close_price', 0):.2f}")
        
        # 2. Options flow
        console.print("\n[yellow]💰 Recent Options Flow[/yellow]")
        flow = await client.get_flow_per_strike_intraday('SPY')
        if flow and 'data' in flow:
            console.print(f"  Active strikes with flow: {len(flow['data'])}")
        
        # 3. GEX levels
        console.print("\n[yellow]⚡ Gamma Exposure (GEX)[/yellow]")
        gex = await client.get_spot_exposures('SPY')
        if gex and 'data' in gex:
            # Find strikes with highest GEX
            gex_data = gex['data']
            if gex_data:
                sorted_gex = sorted(gex_data, key=lambda x: abs(x.get('total_gamma', 0)), reverse=True)[:5]
                
                table = Table(title="Top GEX Strikes")
                table.add_column("Strike", style="cyan")
                table.add_column("Total GEX", style="green")
                table.add_column("Type", style="yellow")
                
                for item in sorted_gex:
                    strike = item.get('strike', 0)
                    total_gex = item.get('total_gamma', 0)
                    gex_type = "Resistance" if total_gex > 0 else "Support"
                    table.add_row(f"${strike:.0f}", f"{total_gex:,.0f}", gex_type)
                
                console.print(table)
        
        # 4. Dark pool activity
        console.print("\n[yellow]🌑 Dark Pool Activity (Last 24h)[/yellow]")
        dark_pool = await client.get_dark_pool('SPY')
        if dark_pool and 'data' in dark_pool:
            trades = dark_pool['data']
            if trades:
                total_volume = sum(t.get('size', 0) for t in trades)
                avg_price = sum(t.get('price', 0) * t.get('size', 0) for t in trades) / total_volume if total_volume > 0 else 0
                console.print(f"  Total trades: {len(trades)}")
                console.print(f"  Total volume: {total_volume:,}")
                console.print(f"  Avg price: ${avg_price:.2f}")
        
        # 5. Greeks
        console.print("\n[yellow]📐 Greek Metrics[/yellow]")
        greeks = await client.get_greeks('SPY')
        if greeks:
            console.print(f"  Total Delta: {greeks.get('total_delta', 0):,.0f}")
            console.print(f"  Total Gamma: {greeks.get('total_gamma', 0):,.0f}")
            console.print(f"  Total Vanna: {greeks.get('total_vanna', 0):,.0f}")


async def example_2_flow_scanner():
    """Example 2: Scan for Unusual Flow Across Market."""
    console.print(Panel("[bold cyan]Example 2: Market-Wide Flow Scanner[/bold cyan]"))
    
    async with UWClient() as client:
        # Get recent flow alerts
        console.print("\n[yellow]🔍 Scanning for unusual flow...[/yellow]")
        flow_alerts = await client.get_flow_alerts()
        
        if not flow_alerts or 'data' not in flow_alerts:
            console.print("[red]No flow data available[/red]")
            return
        
        alerts = flow_alerts['data']
        
        # Filter for high premium trades (>$250k)
        high_premium = [a for a in alerts if a.get('premium', 0) > 250000]
        
        console.print(f"\n[green]Found {len(high_premium)} large premium trades[/green]\n")
        
        # Create summary table
        table = Table(title="Top Flow Alerts (>$250k Premium)")
        table.add_column("Ticker", style="cyan", no_wrap=True)
        table.add_column("Strike", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Premium", style="green", justify="right")
        table.add_column("Volume", style="blue", justify="right")
        table.add_column("Side", style="red")
        
        for alert in high_premium[:15]:  # Top 15
            ticker = alert.get('ticker', 'N/A')
            strike = f"${alert.get('strike', 0):.0f}"
            option_type = alert.get('option_type', 'N/A')
            premium = f"${alert.get('premium', 0):,.0f}"
            volume = f"{alert.get('volume', 0):,}"
            side = alert.get('side', 'N/A')
            
            table.add_row(ticker, strike, option_type, premium, volume, side)
        
        console.print(table)


async def example_3_gex_pivot_finder():
    """Example 3: Find GEX Pivot Points for Trading."""
    console.print(Panel("[bold cyan]Example 3: GEX Pivot Point Finder[/bold cyan]"))
    
    tickers = ['SPY', 'QQQ', 'IWM']
    
    async with UWClient() as client:
        for ticker in tickers:
            console.print(f"\n[yellow]📍 Analyzing {ticker} GEX Pivots[/yellow]")
            
            try:
                gex_data = await client.get_spot_exposures(ticker)
                
                if not gex_data or 'data' not in gex_data:
                    console.print(f"[red]No GEX data for {ticker}[/red]")
                    continue
                
                data = gex_data['data']
                if not data:
                    continue
                
                # Sort by absolute gamma
                sorted_data = sorted(data, key=lambda x: abs(x.get('total_gamma', 0)), reverse=True)
                
                # Identify key levels
                positive_gex = [d for d in sorted_data if d.get('total_gamma', 0) > 0][:3]
                negative_gex = [d for d in sorted_data if d.get('total_gamma', 0) < 0][:3]
                
                console.print(f"\n  [green]Positive GEX (Resistance/Price Magnets):[/green]")
                for item in positive_gex:
                    strike = item.get('strike', 0)
                    gamma = item.get('total_gamma', 0)
                    console.print(f"    ${strike:.0f} - GEX: {gamma:,.0f}")
                
                console.print(f"\n  [red]Negative GEX (Support/Amplification):[/red]")
                for item in negative_gex:
                    strike = item.get('strike', 0)
                    gamma = item.get('total_gamma', 0)
                    console.print(f"    ${strike:.0f} - GEX: {gamma:,.0f}")
                    
            except Exception as e:
                console.print(f"[red]Error analyzing {ticker}: {e}[/red]")


async def example_4_institutional_tracker():
    """Example 4: Track Institutional Activity."""
    console.print(Panel("[bold cyan]Example 4: Institutional Activity Tracker[/bold cyan]"))
    
    async with UWClient() as client:
        console.print("\n[yellow]🏦 Recent Institutional Filings[/yellow]")
        
        try:
            filings = await client.get_latest_filings()
            
            if not filings or 'data' not in filings:
                console.print("[red]No filing data available[/red]")
                return
            
            filing_data = filings['data'][:20]  # Top 20
            
            table = Table(title="Latest 13F Filings")
            table.add_column("Institution", style="cyan")
            table.add_column("Ticker", style="yellow")
            table.add_column("Shares", style="green", justify="right")
            table.add_column("Value", style="magenta", justify="right")
            table.add_column("Type", style="blue")
            
            for filing in filing_data:
                inst = filing.get('institution_name', 'N/A')[:30]
                ticker = filing.get('ticker', 'N/A')
                shares = f"{filing.get('shares', 0):,}"
                value = f"${filing.get('value', 0):,.0f}"
                change_type = filing.get('change_type', 'N/A')
                
                table.add_row(inst, ticker, shares, value, change_type)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


async def example_5_realtime_stream():
    """Example 5: Real-time Flow Alerts Stream."""
    console.print(Panel("[bold cyan]Example 5: Real-Time Flow Stream (30 seconds)[/bold cyan]"))
    
    alert_count = 0
    alerts = []
    
    async def on_alert(data):
        nonlocal alert_count, alerts
        alert_count += 1
        alerts.append(data)
        
        ticker = data.get('ticker', 'N/A')
        premium = data.get('premium', 0)
        option_type = data.get('option_type', 'N/A')
        
        console.print(f"  [{alert_count}] {ticker} {option_type} - ${premium:,.0f}")
    
    try:
        async with UWWebSocketClient() as ws:
            await ws.subscribe_flow_alerts(on_alert)
            
            console.print("\n[yellow]📡 Streaming flow alerts... (30 seconds)[/yellow]\n")
            
            await asyncio.sleep(30)
            
            console.print(f"\n[green]Received {alert_count} alerts in 30 seconds[/green]")
            
    except Exception as e:
        console.print(f"[red]WebSocket error: {e}[/red]")
        console.print("[yellow]Note: WebSocket access may require specific API plan[/yellow]")


async def example_6_congress_tracker():
    """Example 6: Congressional Trade Tracker."""
    console.print(Panel("[bold cyan]Example 6: Congressional Trade Tracker[/bold cyan]"))
    
    async with UWClient() as client:
        console.print("\n[yellow]🏛️ Recent Congressional Trades[/yellow]")
        
        try:
            trades = await client.get_congress_trades()
            
            if not trades or 'data' not in trades:
                console.print("[red]No congressional trade data available[/red]")
                return
            
            trade_data = trades['data'][:15]  # Top 15
            
            table = Table(title="Recent Congressional Trades")
            table.add_column("Member", style="cyan")
            table.add_column("Party", style="yellow")
            table.add_column("Ticker", style="magenta")
            table.add_column("Type", style="green")
            table.add_column("Amount", style="blue")
            table.add_column("Date", style="red")
            
            for trade in trade_data:
                member = trade.get('member_name', 'N/A')[:25]
                party = trade.get('party', 'N/A')
                ticker = trade.get('ticker', 'N/A')
                trade_type = trade.get('transaction_type', 'N/A')
                amount = trade.get('amount_range', 'N/A')
                date = trade.get('transaction_date', 'N/A')[:10]
                
                table.add_row(member, party, ticker, trade_type, amount, date)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Note: Congress endpoint may require specific API plan[/yellow]")


def main():
    """Run all examples."""
    examples = [
        ("SPY Deep Dive", example_1_spy_analysis),
        ("Market Flow Scanner", example_2_flow_scanner),
        ("GEX Pivot Finder", example_3_gex_pivot_finder),
        ("Institutional Tracker", example_4_institutional_tracker),
        ("Real-time Stream", example_5_realtime_stream),
        ("Congress Tracker", example_6_congress_tracker),
    ]
    
    console.print(Panel.fit(
        "[bold cyan]UW Scanner - Usage Examples[/bold cyan]\n"
        "Practical examples demonstrating key functionality",
        border_style="cyan"
    ))
    
    console.print("\n[bold]Available Examples:[/bold]")
    for i, (name, _) in enumerate(examples, 1):
        console.print(f"  {i}. {name}")
    
    console.print("\n[yellow]Choose an example (1-6) or 'all' to run all:[/yellow] ", end="")
    
    try:
        choice = input().strip().lower()
        
        if choice == 'all':
            for name, func in examples:
                console.print(f"\n{'='*60}")
                asyncio.run(func())
                console.print()
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            name, func = examples[int(choice) - 1]
            asyncio.run(func())
        else:
            console.print("[red]Invalid choice[/red]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
