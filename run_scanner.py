#!/usr/bin/env python3
"""
Scanner Runner CLI
Easy command-line interface to run the scanners
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich import box
from datetime import datetime
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scanners.mode1_intraday import IntradaySPYScanner
from config import get_settings
from loguru import logger

console = Console()


def print_banner():
    """Print scanner banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🐋 UNUSUAL WHALES SCANNER - MODE 1 🐋              ║
║              Intraday SPY Scalper v1.0                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def create_stats_table(scanner) -> Table:
    """Create statistics table"""
    stats = scanner.get_summary()
    
    table = Table(title="Scanner Statistics", box=box.ROUNDED, show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow", justify="right")
    
    table.add_row("Status", "🟢 RUNNING" if scanner.is_running else "🔴 STOPPED")
    table.add_row("Ticker", stats.get('ticker', 'N/A'))
    table.add_row("Spot Price", f"${stats.get('spot_price', 0):.2f}")
    table.add_row("Total Scans", str(stats.get('scans_completed', 0)))
    table.add_row("Alerts Generated", str(stats.get('alerts_generated', 0)))
    table.add_row("Active Flow Count", str(stats.get('flow_count', 0)))
    table.add_row("Dark Pool Trades", str(stats.get('dark_pool_count', 0)))
    table.add_row("Avg Scan Duration", f"{stats.get('average_scan_duration', 0):.2f}s")
    
    if stats.get('last_scan_time'):
        table.add_row("Last Scan", stats['last_scan_time'].strftime('%H:%M:%S'))
    
    return table


def create_alerts_table(signals) -> Table:
    """Create alerts table"""
    table = Table(title="🚨 Recent Signals", box=box.ROUNDED, show_header=True)
    table.add_column("Time", style="dim")
    table.add_column("Priority", justify="center")
    table.add_column("Type", style="cyan")
    table.add_column("Signal", style="yellow")
    
    for signal in signals[-10:]:  # Last 10 signals
        priority = signal.get('priority', 5)
        
        # Priority emoji
        if priority >= 9:
            priority_str = "🔥🔥"
        elif priority >= 7:
            priority_str = "🔥"
        else:
            priority_str = "⚠️"
        
        # Signal type emoji
        signal_type = signal.get('signal_type', '')
        if 'bullish' in signal_type:
            type_emoji = "🟢"
        elif 'bearish' in signal_type:
            type_emoji = "🔴"
        elif 'gex' in signal_type or 'gamma' in signal_type:
            type_emoji = "⚡"
        elif 'dark_pool' in signal_type:
            type_emoji = "🏦"
        else:
            type_emoji = "📊"
        
        table.add_row(
            datetime.now().strftime('%H:%M:%S'),
            priority_str,
            type_emoji,
            signal.get('title', 'Unknown')[:60]
        )
    
    return table


async def run_continuous_scan(ticker: str = 'SPY', interval: int = 60):
    """
    Run scanner continuously with live updates
    
    Args:
        ticker: Ticker to scan
        interval: Scan interval in seconds
    """
    scanner = IntradaySPYScanner(ticker=ticker)
    all_signals = []
    
    try:
        await scanner.initialize()
        scanner.is_running = True
        
        console.print(f"\n[green]✅ Scanner initialized for {ticker}[/green]")
        console.print(f"[yellow]⏱️  Scan interval: {interval} seconds[/yellow]")
        console.print("[dim]Press Ctrl+C to stop\n[/dim]")
        
        while scanner.is_running:
            try:
                # Run scan
                results = await scanner.scan()
                
                # Collect signals
                if 'signals' in results:
                    all_signals.extend(results['signals'])
                    # Keep only last 50 signals
                    all_signals = all_signals[-50:]
                
                # Display results
                console.clear()
                print_banner()
                
                # Stats table
                console.print(create_stats_table(scanner))
                console.print()
                
                # Alerts table
                if all_signals:
                    console.print(create_alerts_table(all_signals))
                else:
                    console.print("[dim]No signals yet...[/dim]")
                
                console.print(f"\n[dim]Next scan in {interval} seconds...[/dim]")
                
                # Wait for next scan
                await asyncio.sleep(interval)
            
            except KeyboardInterrupt:
                break
            
            except Exception as e:
                console.print(f"[red]❌ Scan error: {e}[/red]")
                await asyncio.sleep(5)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Scanner stopped by user[/yellow]")
    
    finally:
        await scanner.cleanup()
        console.print("[green]✅ Scanner shut down cleanly[/green]")


async def run_single_scan(ticker: str = 'SPY'):
    """
    Run a single scan and display results
    
    Args:
        ticker: Ticker to scan
    """
    print_banner()
    console.print(f"\n[cyan]Running single scan for {ticker}...[/cyan]\n")
    
    scanner = IntradaySPYScanner(ticker=ticker)
    
    try:
        await scanner.initialize()
        results = await scanner.scan()
        
        # Display results
        console.print(f"[green]✅ Scan completed![/green]\n")
        
        # Stats
        stats = scanner.get_summary()
        console.print(f"[cyan]Spot Price:[/cyan] ${stats.get('spot_price', 0):.2f}")
        console.print(f"[cyan]Signals Found:[/cyan] {len(results.get('signals', []))}")
        console.print(f"[cyan]Alerts Generated:[/cyan] {results.get('alerts_generated', 0)}")
        console.print()
        
        # Show signals
        if results.get('signals'):
            console.print("[bold yellow]🚨 Signals:[/bold yellow]\n")
            
            for i, signal in enumerate(results['signals'], 1):
                priority = signal.get('priority', 5)
                priority_emoji = "🔥" if priority >= 7 else "⚠️"
                
                panel = Panel(
                    f"[bold]{signal.get('title', 'Unknown')}[/bold]\n\n"
                    f"{signal.get('description', 'No description')}\n\n"
                    f"[dim]Score: {signal.get('score', 0):.1f}/10 | "
                    f"Priority: {priority} | "
                    f"Type: {signal.get('signal_type', 'unknown')}[/dim]",
                    title=f"{priority_emoji} Signal #{i}",
                    border_style="yellow" if priority >= 7 else "blue"
                )
                console.print(panel)
        else:
            console.print("[dim]No signals found in this scan.[/dim]")
    
    finally:
        await scanner.cleanup()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Unusual Whales Scanner - Mode 1: Intraday SPY Scalper',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--ticker',
        type=str,
        default='SPY',
        help='Ticker to scan (default: SPY)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Scan interval in seconds for continuous mode (default: 60)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run single scan and exit (default: continuous)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - run single scan with verbose output'
    )
    
    args = parser.parse_args()
    
    # Configure logger
    if args.test:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add("logs/scanner.log", rotation="1 day", level="INFO")
    
    try:
        # Check settings
        settings = get_settings()
        if not settings.uw_api_key or len(settings.uw_api_key) < 10:
            console.print("[red]❌ Error: Invalid API key in .env file[/red]")
            console.print("[yellow]Please set UW_API_KEY in your .env file[/yellow]")
            sys.exit(1)
        
        # Run scanner
        if args.once or args.test:
            asyncio.run(run_single_scan(ticker=args.ticker))
        else:
            asyncio.run(run_continuous_scan(ticker=args.ticker, interval=args.interval))
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Scanner stopped[/yellow]")
        sys.exit(0)
    
    except Exception as e:
        console.print(f"[red]❌ Fatal error: {e}[/red]")
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == '__main__':
    main()
