"""
Base Scanner Class
All scanner modes inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
import asyncio

from api import UnusualWhalesClient
from database import get_db_manager, get_redis_manager, ScannerAlert, ScannerRun, ScannerMode
from config import get_settings


class BaseScanner(ABC):
    """
    Abstract base class for all scanner modes
    
    Provides common functionality:
    - API client management
    - Database operations
    - Redis caching
    - Alert generation
    - Statistics tracking
    """
    
    def __init__(
        self,
        mode: ScannerMode,
        ticker: Optional[str] = None,
        name: Optional[str] = None
    ):
        """
        Initialize base scanner
        
        Args:
            mode: Scanner mode enum
            ticker: Primary ticker to scan (optional)
            name: Scanner name (optional)
        """
        self.settings = get_settings()
        self.mode = mode
        self.ticker = ticker
        self.name = name or f"{mode.value}_scanner"
        
        # Managers
        self.api_client: Optional[UnusualWhalesClient] = None
        self.db = get_db_manager()
        self.redis = get_redis_manager()
        
        # State
        self.is_running = False
        self.scan_count = 0
        self.alert_count = 0
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'alerts_generated': 0,
            'errors': 0,
            'last_scan_time': None,
            'average_scan_duration': 0.0,
            'start_time': None
        }
        
        logger.info(f"Scanner initialized: {self.name} ({self.mode.value})")
    
    async def initialize(self):
        """Initialize scanner resources"""
        logger.info(f"Initializing scanner: {self.name}")
        
        # Connect to Redis
        await self.redis.connect()
        
        # Initialize API client
        self.api_client = UnusualWhalesClient()
        await self.api_client._ensure_session()
        
        # Initialize database
        self.db.initialize_async()
        
        # Call custom initialization
        await self.on_initialize()
        
        self.stats['start_time'] = datetime.utcnow()
        logger.info(f"✅ Scanner ready: {self.name}")
    
    async def cleanup(self):
        """Cleanup scanner resources"""
        logger.info(f"Cleaning up scanner: {self.name}")
        
        # Call custom cleanup
        await self.on_cleanup()
        
        # Close API client
        if self.api_client:
            await self.api_client.close()
        
        # Disconnect Redis
        await self.redis.disconnect()
        
        # Close database
        await self.db.close_async()
        
        logger.info(f"✅ Scanner cleaned up: {self.name}")
    
    async def start(self, interval: Optional[int] = None):
        """
        Start the scanner
        
        Args:
            interval: Scan interval in seconds (None for single run)
        """
        await self.initialize()
        
        self.is_running = True
        logger.info(f"🚀 Starting scanner: {self.name}")
        
        try:
            if interval is None:
                # Single run
                await self._run_scan()
            else:
                # Continuous scanning
                while self.is_running:
                    await self._run_scan()
                    await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Scanner interrupted by user")
        
        except Exception as e:
            logger.error(f"Scanner error: {e}")
            self.stats['errors'] += 1
        
        finally:
            await self.cleanup()
    
    async def stop(self):
        """Stop the scanner"""
        logger.info(f"Stopping scanner: {self.name}")
        self.is_running = False
    
    async def _run_scan(self):
        """Internal scan runner with error handling and tracking"""
        start_time = datetime.utcnow()
        
        try:
            # Create scan run record
            scan_run = ScannerRun(
                start_time=start_time,
                scanner_mode=self.mode,
                status='running'
            )
            
            # Execute the scan
            logger.info(f"🔍 Running scan #{self.scan_count + 1}")
            results = await self.scan()
            
            # Update statistics
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self.scan_count += 1
            self.stats['scans_completed'] += 1
            self.stats['last_scan_time'] = end_time
            
            # Update average duration
            if self.stats['average_scan_duration'] == 0:
                self.stats['average_scan_duration'] = duration
            else:
                self.stats['average_scan_duration'] = (
                    self.stats['average_scan_duration'] * 0.9 + duration * 0.1
                )
            
            # Update scan run record
            scan_run.end_time = end_time
            scan_run.execution_time_ms = int(duration * 1000)
            scan_run.status = 'success'
            scan_run.tickers_scanned = results.get('tickers_scanned', 0)
            scan_run.alerts_generated = results.get('alerts_generated', 0)
            scan_run.results_summary = results
            
            # Save to database
            async with self.db.get_async_session() as session:
                session.add(scan_run)
                await session.commit()
            
            logger.info(
                f"✅ Scan completed in {duration:.2f}s - "
                f"Alerts: {results.get('alerts_generated', 0)}"
            )
        
        except Exception as e:
            logger.error(f"❌ Scan failed: {e}")
            self.stats['errors'] += 1
            
            # Update scan run with error
            if 'scan_run' in locals():
                scan_run.end_time = datetime.utcnow()
                scan_run.status = 'failed'
                scan_run.error_message = str(e)
                
                async with self.db.get_async_session() as session:
                    session.add(scan_run)
                    await session.commit()
    
    async def create_alert(
        self,
        alert_type: str,
        ticker: str,
        title: str,
        description: str,
        priority: int = 5,
        composite_score: Optional[float] = None,
        **scores
    ) -> ScannerAlert:
        """
        Create and save an alert
        
        Args:
            alert_type: Type of alert (from AlertType enum)
            ticker: Ticker symbol
            title: Alert title
            description: Alert description
            priority: Priority 1-10 (10 = highest)
            composite_score: Overall score
            **scores: Individual scores (flow_score, gex_score, etc.)
        
        Returns:
            Created alert
        """
        alert = ScannerAlert(
            alert_type=alert_type,
            scanner_mode=self.mode,
            ticker=ticker,
            title=title,
            description=description,
            priority=priority,
            composite_score=composite_score,
            flow_score=scores.get('flow_score'),
            gex_score=scores.get('gex_score'),
            dark_pool_score=scores.get('dark_pool_score'),
            institutional_score=scores.get('institutional_score'),
            sentiment_score=scores.get('sentiment_score'),
            related_data=scores.get('related_data', {})
        )
        
        # Save to database
        async with self.db.get_async_session() as session:
            session.add(alert)
            await session.commit()
        
        # Cache in Redis for quick access
        cache_key = f"alert:{alert.id}"
        await self.redis.set_json(cache_key, {
            'id': alert.id,
            'ticker': ticker,
            'title': title,
            'priority': priority,
            'timestamp': alert.timestamp.isoformat()
        }, expire=3600)
        
        self.alert_count += 1
        self.stats['alerts_generated'] += 1
        
        logger.info(f"🚨 Alert created: {title} ({ticker}) - Priority {priority}")
        
        return alert
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scanner statistics"""
        return {
            **self.stats,
            'name': self.name,
            'mode': self.mode.value,
            'ticker': self.ticker,
            'is_running': self.is_running,
            'scan_count': self.scan_count,
            'alert_count': self.alert_count
        }
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def scan(self) -> Dict[str, Any]:
        """
        Main scan logic - must be implemented by subclass
        
        Returns:
            Dict with scan results including:
            - tickers_scanned: int
            - alerts_generated: int
            - Any other relevant data
        """
        pass
    
    async def on_initialize(self):
        """Optional initialization hook - override in subclass"""
        pass
    
    async def on_cleanup(self):
        """Optional cleanup hook - override in subclass"""
        pass


if __name__ == '__main__':
    # Test base scanner
    class TestScanner(BaseScanner):
        async def scan(self):
            logger.info("Test scan running...")
            await asyncio.sleep(1)
            return {'tickers_scanned': 1, 'alerts_generated': 0}
    
    async def test():
        scanner = TestScanner(ScannerMode.MODE_1_INTRADAY, ticker='SPY')
        await scanner.start()
    
    asyncio.run(test())
