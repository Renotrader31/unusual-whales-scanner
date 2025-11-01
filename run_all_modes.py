#!/usr/bin/env python3
"""
🚀 ULTIMATE SCANNER - ALL MODES
Run all three scanner modes simultaneously
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from api.client import UnusualWhalesClient
from scanners import IntradaySPYScanner, SwingTradingScanner, LongTermScanner

console = Console()


class UltimateScanner:
    """Master scanner orchestrator running all 3 modes"""
    
    def __init__(self):
        self.settings = Settings()
        self.api_client = UnusualWhalesClient(
            api_key=self.settings.UW_API_KEY,
            rate_limit=10.0
        )
        
        # Initialize all scanners
        self.mode1 = IntradaySPYScanner(
            config=self.settings,
            api_client=self.api_client
        )
        
        self.mode2 = SwingTradingScanner(
            config=self.settings,
            api_client=self.api_client
        )
        
        self.mode3 = LongTermScanner(
            config=self.settings,
            api_client=self.api_client
        )
        
        self.results = {
            'mode1': {},
            'mode2': {},
            'mode3': {}
        }
        
        self.scan_count = 0
    
    async def run_mode1(self):
        """Run intraday scanner"""
        while True:
            try:
                console.print("[cyan]⚡ Running Mode 1 (Intraday SPY)...[/cyan]")
                results = await self.mode1.scan()
                self.results['mode1'] = results
                
                if results.get('signals'):
                    for signal in results['signals'][:3]:
                        self._show_mode1_alert(signal)
                
            except Exception as e:
                console.print(f"[red]Mode 1 error: {e}[/red]")
            
            await asyncio.sleep(60)  # Every 60 seconds
    
    async def run_mode2(self):
        """Run swing trading scanner"""
        while True:
            try:
                console.print("[yellow]📊 Running Mode 2 (Swing Trading)...[/yellow]")
                results = await self.mode2.scan()
                self.results['mode2'] = results
                
                if results.get('top_signals'):
                    for signal in results['top_signals'][:3]:
                        self._show_mode2_alert(signal)
                
            except Exception as e:
                console.print(f"[red]Mode 2 error: {e}[/red]")
            
            await asyncio.sleep(300)  # Every 5 minutes
    
    async def run_mode3(self):
        """Run long-term investment scanner"""
        while True:
            try:
                console.print("[green]🎯 Running Mode 3 (Long-Term)...[/green]")
                results = await self.mode3.scan()
                self.results['mode3'] = results
                
                if results.get('top_picks'):
                    for signal in results['top_picks'][:2]:
                        self._show_mode3_alert(signal)
                
            except Exception as e:
                console.print(f"[red]Mode 3 error: {e}[/red]")
            
            await asyncio.sleep(3600)  # Every 1 hour
    
    def _show_mode1_alert(self, signal: Dict):
        """Display Mode 1 alert"""
        panel = Panel(
            f"[bold cyan]SPY Signal[/bold cyan]\n"
            f"Score: {signal.get('score', 0):.1f}/10\n"
            f"Direction: {signal.get('direction', 'N/A')}\n"
            f"Type: {signal.get('signal_type', 'N/A')}\n"
            f"Confidence: {signal.get('confidence', 0):.0f}%",
            title=f"⚡ MODE 1 - {datetime.now().strftime('%H:%M:%S')}",
            border_style="cyan"
        )
        console.print(panel)
    
    def _show_mode2_alert(self, signal: Dict):
        """Display Mode 2 alert"""
        panel = Panel(
            f"[bold yellow]{signal.get('ticker', 'N/A')}[/bold yellow] @ ${signal.get('price', 0):.2f}\n"
            f"Score: {signal.get('score', 0):.1f}/10\n"
            f"Direction: {signal.get('direction', 'N/A')}\n"
            f"Strategy: {signal.get('strategy', 'N/A')}\n"
            f"Target DTE: {signal.get('target_dte', 'N/A')}\n"
            f"Confidence: {signal.get('confidence', 'N/A')}",
            title=f"📊 MODE 2 - {datetime.now().strftime('%H:%M:%S')}",
            border_style="yellow"
        )
        console.print(panel)
    
    def _show_mode3_alert(self, signal: Dict):
        """Display Mode 3 alert"""
        catalysts = signal.get('catalysts', [])
        catalyst_str = ", ".join(catalysts[:2]) if catalysts else "None"
        
        panel = Panel(
            f"[bold green]{signal.get('ticker', 'N/A')}[/bold green] @ ${signal.get('price', 0):.2f}\n"
            f"Score: {signal.get('score', 0):.1f}/10\n"
            f"Thesis: {signal.get('thesis', 'N/A')}\n"
            f"Catalysts: {catalyst_str}\n"
            f"Conviction: {signal.get('conviction', 'N/A')}\n"
            f"Horizon: {signal.get('time_horizon', 'N/A')}",
            title=f"🎯 MODE 3 - {datetime.now().strftime('%H:%M:%S')}",
            border_style="green"
        )
        console.print(panel)
    
    async def display_dashboard(self):
        """Display live dashboard"""
        while True:
            try:
                layout = Layout()
                
                # Create header
                header = Table.grid()
                header.add_row(
                    Text("🚀 ULTIMATE SCANNER", style="bold magenta"),
                    Text(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
                )
                
                # Mode 1 stats
                mode1_results = self.results.get('mode1', {})
                mode1_table = Table(title="⚡ Mode 1: Intraday SPY", border_style="cyan")
                mode1_table.add_column("Metric", style="cyan")
                mode1_table.add_column("Value", style="bold")
                
                if mode1_results:
                    mode1_table.add_row("Signals Found", str(len(mode1_results.get('signals', []))))
                    mode1_table.add_row("Last Scan", mode1_results.get('timestamp', 'N/A')[:19])
                
                # Mode 2 stats
                mode2_results = self.results.get('mode2', {})
                mode2_table = Table(title="📊 Mode 2: Swing Trading", border_style="yellow")
                mode2_table.add_column("Metric", style="yellow")
                mode2_table.add_column("Value", style="bold")
                
                if mode2_results:
                    mode2_table.add_row("Tickers Scanned", str(mode2_results.get('tickers_scanned', 0)))
                    mode2_table.add_row("Signals Found", str(mode2_results.get('signals_found', 0)))
                    mode2_table.add_row("Last Scan", mode2_results.get('timestamp', 'N/A')[:19])
                
                # Mode 3 stats
                mode3_results = self.results.get('mode3', {})
                mode3_table = Table(title="🎯 Mode 3: Long-Term", border_style="green")
                mode3_table.add_column("Metric", style="green")
                mode3_table.add_column("Value", style="bold")
                
                if mode3_results:
                    mode3_table.add_row("Tickers Scanned", str(mode3_results.get('tickers_scanned', 0)))
                    mode3_table.add_row("Top Picks", str(len(mode3_results.get('top_picks', []))))
                    mode3_table.add_row("Last Scan", mode3_results.get('timestamp', 'N/A')[:19])
                
                console.print("\n")
                console.print(mode1_table)
                console.print(mode2_table)
                console.print(mode3_table)
                
            except Exception as e:
                console.print(f"[red]Dashboard error: {e}[/red]")
            
            await asyncio.sleep(10)  # Update every 10 seconds
    
    async def run(self):
        """Run all scanners in parallel"""
        console.print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🚀 ULTIMATE SCANNER ACTIVATED 🚀               ║
║                                                              ║
║  Mode 1: Intraday SPY (Every 60s)                           ║
║  Mode 2: Swing Trading (Every 5m)                           ║
║  Mode 3: Long-Term (Every 1h)                               ║
║                                                              ║
║  Press Ctrl+C to stop                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        try:
            # Run all scanners in parallel
            await asyncio.gather(
                self.run_mode1(),
                self.run_mode2(),
                self.run_mode3(),
                # self.display_dashboard(),  # Optional dashboard
                return_exceptions=True
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down scanners...[/yellow]")
        finally:
            await self.api_client.close()
            console.print("[green]✅ Scanners stopped[/green]")


async def main():
    """Main entry point"""
    scanner = UltimateScanner()
    await scanner.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
