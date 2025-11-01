"""
WebSocket Client for Real-Time Data Streaming
Handles live options flow, GEX updates, price feeds, etc.
"""
import asyncio
import websockets
import json
from typing import Callable, Dict, Any, Optional, List, Set
from loguru import logger
from datetime import datetime
import backoff

from config import get_settings


class WebSocketClient:
    """
    Async WebSocket client for real-time UW data streams
    
    Supports multiple channels:
    - flow-alerts: Real-time flow alerts
    - price:{ticker}: Live price updates
    - gex:{ticker}: Gamma exposure updates
    - gex_strike:{ticker}: GEX by strike
    - lit_trades: Exchange trades
    - off_lit_trades: Dark pool trades
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        ws_url: Optional[str] = None
    ):
        """
        Initialize WebSocket client
        
        Args:
            api_key: UW API key
            ws_url: WebSocket server URL
        """
        self.settings = get_settings()
        self.api_key = api_key or self.settings.uw_api_key
        self.ws_url = ws_url or "wss://api.unusualwhales.com/ws"
        
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: Set[str] = set()
        self.handlers: Dict[str, List[Callable]] = {}
        self.is_connected = False
        self.is_running = False
        
        # Reconnection settings
        self.reconnect_delay = self.settings.ws_reconnect_delay
        self.max_reconnect_attempts = self.settings.ws_max_reconnect_attempts
        self.reconnect_attempts = 0
        
        # Message statistics
        self.stats = {
            'messages_received': 0,
            'messages_by_channel': {},
            'errors': 0,
            'reconnections': 0,
            'last_message_time': None
        }
        
        logger.info(f"WebSocket client initialized: {self.ws_url}")
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            # Add authentication to connection
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("✅ WebSocket connected")
            
            # Resubscribe to channels after reconnection
            if self.subscriptions:
                await self._resubscribe()
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self.is_running = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.is_connected = False
        logger.info("WebSocket disconnected")
    
    async def subscribe(self, channel: str, handler: Optional[Callable] = None):
        """
        Subscribe to a channel
        
        Args:
            channel: Channel name (e.g., 'flow-alerts', 'price:SPY', 'gex:SPY')
            handler: Optional callback function for messages on this channel
        """
        if not self.is_connected:
            await self.connect()
        
        # Send subscription message
        subscribe_msg = {
            'action': 'subscribe',
            'channel': channel
        }
        
        await self.websocket.send(json.dumps(subscribe_msg))
        self.subscriptions.add(channel)
        
        # Register handler
        if handler:
            if channel not in self.handlers:
                self.handlers[channel] = []
            self.handlers[channel].append(handler)
        
        logger.info(f"📡 Subscribed to channel: {channel}")
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from a channel"""
        if channel not in self.subscriptions:
            return
        
        unsubscribe_msg = {
            'action': 'unsubscribe',
            'channel': channel
        }
        
        await self.websocket.send(json.dumps(unsubscribe_msg))
        self.subscriptions.remove(channel)
        
        # Remove handlers
        if channel in self.handlers:
            del self.handlers[channel]
        
        logger.info(f"Unsubscribed from channel: {channel}")
    
    async def _resubscribe(self):
        """Resubscribe to all channels after reconnection"""
        logger.info(f"Resubscribing to {len(self.subscriptions)} channels...")
        
        for channel in list(self.subscriptions):
            subscribe_msg = {
                'action': 'subscribe',
                'channel': channel
            }
            await self.websocket.send(json.dumps(subscribe_msg))
        
        logger.info("✅ Resubscribed to all channels")
    
    async def _handle_message(self, message: Dict[str, Any]):
        """
        Process received message and call appropriate handlers
        
        Args:
            message: Parsed message data
        """
        self.stats['messages_received'] += 1
        self.stats['last_message_time'] = datetime.now()
        
        # Extract channel from message
        channel = message.get('channel')
        
        if channel:
            # Update channel statistics
            if channel not in self.stats['messages_by_channel']:
                self.stats['messages_by_channel'][channel] = 0
            self.stats['messages_by_channel'][channel] += 1
            
            # Call registered handlers
            if channel in self.handlers:
                for handler in self.handlers[channel]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    except Exception as e:
                        logger.error(f"Handler error for channel {channel}: {e}")
                        self.stats['errors'] += 1
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=10,
        max_time=300
    )
    async def _reconnect_loop(self):
        """Reconnection loop with exponential backoff"""
        while self.is_running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.warning(f"Attempting reconnection ({self.reconnect_attempts + 1}/{self.max_reconnect_attempts})...")
                await self.connect()
                return
            
            except Exception as e:
                self.reconnect_attempts += 1
                self.stats['reconnections'] += 1
                wait_time = min(60, self.reconnect_delay * (2 ** self.reconnect_attempts))
                logger.error(f"Reconnection failed: {e}. Waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        logger.error("Max reconnection attempts reached. Giving up.")
        self.is_running = False
    
    async def start(self):
        """Start receiving messages (blocking)"""
        if not self.is_connected:
            await self.connect()
        
        self.is_running = True
        logger.info("🚀 WebSocket client started")
        
        try:
            while self.is_running:
                try:
                    # Receive message with timeout
                    message_str = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=60.0
                    )
                    
                    # Parse and handle message
                    try:
                        message = json.loads(message_str)
                        await self._handle_message(message)
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received: {e}")
                        self.stats['errors'] += 1
                
                except asyncio.TimeoutError:
                    # No message received in timeout period - send ping
                    if self.websocket:
                        try:
                            pong = await self.websocket.ping()
                            await asyncio.wait_for(pong, timeout=10)
                        except Exception:
                            logger.warning("Ping failed, reconnecting...")
                            raise
                
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed. Reconnecting...")
                    self.is_connected = False
                    await self._reconnect_loop()
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.stats['errors'] += 1
        
        finally:
            await self.disconnect()
    
    def register_handler(self, channel: str, handler: Callable):
        """
        Register a message handler for a channel
        
        Args:
            channel: Channel name
            handler: Callback function (can be sync or async)
        """
        if channel not in self.handlers:
            self.handlers[channel] = []
        self.handlers[channel].append(handler)
        logger.info(f"Handler registered for channel: {channel}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            **self.stats,
            'is_connected': self.is_connected,
            'is_running': self.is_running,
            'active_subscriptions': len(self.subscriptions),
            'subscribed_channels': list(self.subscriptions)
        }
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info(f"WebSocket Stats: {stats}")


class ChannelManager:
    """
    High-level manager for WebSocket channels
    Simplifies subscription to common channels
    """
    
    def __init__(self, ws_client: WebSocketClient):
        self.ws = ws_client
    
    async def subscribe_flow_alerts(self, handler: Callable):
        """Subscribe to real-time flow alerts"""
        await self.ws.subscribe('flow-alerts', handler)
    
    async def subscribe_price(self, ticker: str, handler: Callable):
        """Subscribe to live price updates for ticker"""
        await self.ws.subscribe(f'price:{ticker}', handler)
    
    async def subscribe_gex(self, ticker: str, handler: Callable):
        """Subscribe to gamma exposure updates for ticker"""
        await self.ws.subscribe(f'gex:{ticker}', handler)
    
    async def subscribe_gex_strike(self, ticker: str, handler: Callable):
        """Subscribe to GEX by strike for ticker"""
        await self.ws.subscribe(f'gex_strike:{ticker}', handler)
    
    async def subscribe_gex_strike_expiry(self, ticker: str, handler: Callable):
        """Subscribe to GEX by strike and expiry for ticker"""
        await self.ws.subscribe(f'gex_strike_expiry:{ticker}', handler)
    
    async def subscribe_lit_trades(self, handler: Callable):
        """Subscribe to exchange-based trades"""
        await self.ws.subscribe('lit_trades', handler)
    
    async def subscribe_off_lit_trades(self, handler: Callable):
        """Subscribe to dark pool trades"""
        await self.ws.subscribe('off_lit_trades', handler)
    
    async def subscribe_mode1_spy(
        self,
        price_handler: Optional[Callable] = None,
        gex_handler: Optional[Callable] = None,
        flow_handler: Optional[Callable] = None
    ):
        """
        Subscribe to all Mode 1 (Intraday SPY) channels
        
        Args:
            price_handler: Handler for SPY price updates
            gex_handler: Handler for SPY GEX updates
            flow_handler: Handler for flow alerts
        """
        ticker = 'SPY'
        
        if price_handler:
            await self.subscribe_price(ticker, price_handler)
        
        if gex_handler:
            await self.subscribe_gex(ticker, gex_handler)
            await self.subscribe_gex_strike(ticker, gex_handler)
        
        if flow_handler:
            await self.subscribe_flow_alerts(flow_handler)
        
        logger.info(f"✅ Subscribed to Mode 1 channels for {ticker}")


if __name__ == '__main__':
    # Test WebSocket client
    async def test():
        ws = WebSocketClient()
        manager = ChannelManager(ws)
        
        # Test handlers
        async def on_flow_alert(msg):
            print(f"📊 Flow Alert: {msg}")
        
        async def on_price(msg):
            print(f"💰 Price Update: {msg}")
        
        async def on_gex(msg):
            print(f"⚡ GEX Update: {msg}")
        
        try:
            # Subscribe to channels
            await manager.subscribe_mode1_spy(
                price_handler=on_price,
                gex_handler=on_gex,
                flow_handler=on_flow_alert
            )
            
            # Start receiving (run for 30 seconds)
            await asyncio.wait_for(ws.start(), timeout=30.0)
        
        except asyncio.TimeoutError:
            logger.info("Test completed")
            ws.log_stats()
        
        finally:
            await ws.disconnect()
    
    asyncio.run(test())
