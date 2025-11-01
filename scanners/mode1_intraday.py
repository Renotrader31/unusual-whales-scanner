"""
Mode 1: Intraday SPY Scalper
Real-time scanner for 0-2 DTE quick wins on SPY

Features:
- GEX pivot detection (gamma walls)
- Flow pressure monitoring
- 0DTE opportunity scanner
- Dark pool level tracking
- Real-time alerts
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict

from .base_scanner import BaseScanner
from database import (
    ScannerMode, AlertType, OptionsFlow, GammaExposure, 
    DarkPoolTrade, FlowDirection
)
from sqlalchemy import select, and_, desc


class IntradaySPYScanner(BaseScanner):
    """
    Intraday SPY Scanner - Mode 1
    
    Scans for:
    1. GEX pivots (positive/negative gamma walls)
    2. Flow pressure (aggressive call/put buying)
    3. 0DTE opportunities
    4. Dark pool accumulation levels
    """
    
    def __init__(self, ticker: str = 'SPY'):
        super().__init__(
            mode=ScannerMode.MODE_1_INTRADAY,
            ticker=ticker,
            name=f"Intraday_{ticker}_Scanner"
        )
        
        # Scanner configuration
        self.gex_threshold = self.settings.mode_1_gex_threshold
        self.refresh_interval = self.settings.mode_1_refresh_interval
        
        # State tracking
        self.current_gex_data = None
        self.current_flow_data = []
        self.current_dark_pool_data = []
        self.spot_price = None
        
        logger.info(f"Intraday scanner initialized for {ticker}")
    
    async def on_initialize(self):
        """Initialize scanner-specific resources"""
        logger.info("Loading initial data...")
        
        # Warm up cache with initial data
        await self._fetch_initial_data()
    
    async def _fetch_initial_data(self):
        """Fetch initial market data"""
        try:
            # Get current state
            state = await self.api_client.get(f'/api/stock/{self.ticker}/stock-state')
            self.spot_price = state.get('price')
            
            logger.info(f"📊 {self.ticker} current price: ${self.spot_price:.2f}")
        except Exception as e:
            logger.warning(f"Could not fetch initial data: {e}")
    
    async def scan(self) -> Dict[str, Any]:
        """
        Main scan logic for intraday SPY
        
        Returns:
            Scan results with alerts
        """
        results = {
            'tickers_scanned': 1,
            'alerts_generated': 0,
            'signals': []
        }
        
        logger.info(f"🔍 Scanning {self.ticker}...")
        
        # Fetch all data in parallel
        gex_data, flow_data, dark_pool_data, net_prem_data = await asyncio.gather(
            self._fetch_gex_data(),
            self._fetch_flow_data(),
            self._fetch_dark_pool_data(),
            self._fetch_net_premium_data(),
            return_exceptions=True
        )
        
        # Update state
        if not isinstance(gex_data, Exception):
            self.current_gex_data = gex_data
        if not isinstance(flow_data, Exception):
            self.current_flow_data = flow_data
        if not isinstance(dark_pool_data, Exception):
            self.current_dark_pool_data = dark_pool_data
        
        # Run analysis
        signals = []
        
        # 1. GEX Analysis
        gex_signals = await self._analyze_gex()
        signals.extend(gex_signals)
        
        # 2. Flow Analysis
        flow_signals = await self._analyze_flow()
        signals.extend(flow_signals)
        
        # 3. 0DTE Analysis
        zero_dte_signals = await self._analyze_zero_dte()
        signals.extend(zero_dte_signals)
        
        # 4. Dark Pool Analysis
        dark_pool_signals = await self._analyze_dark_pool()
        signals.extend(dark_pool_signals)
        
        # Generate alerts for high-priority signals
        for signal in signals:
            if signal['priority'] >= 7:  # Only alert on high priority
                await self.create_alert(
                    alert_type=signal['type'],
                    ticker=self.ticker,
                    title=signal['title'],
                    description=signal['description'],
                    priority=signal['priority'],
                    composite_score=signal.get('score'),
                    related_data=signal
                )
                results['alerts_generated'] += 1
        
        results['signals'] = signals
        
        return results
    
    async def _fetch_gex_data(self) -> Dict[str, Any]:
        """Fetch gamma exposure data"""
        try:
            gex = await self.api_client.get_spot_exposures(self.ticker)
            gex_by_strike = await self.api_client.get_spot_exposures_by_strike(self.ticker)
            
            return {
                'summary': gex,
                'by_strike': gex_by_strike
            }
        except Exception as e:
            logger.error(f"Error fetching GEX: {e}")
            raise
    
    async def _fetch_flow_data(self) -> List[Dict]:
        """Fetch recent flow data"""
        try:
            # Get flow alerts
            flow = await self.api_client.get_flow_alerts(
                ticker=self.ticker,
                limit=100
            )
            
            return flow.get('data', [])
        except Exception as e:
            logger.error(f"Error fetching flow: {e}")
            raise
    
    async def _fetch_dark_pool_data(self) -> List[Dict]:
        """Fetch dark pool data"""
        try:
            dark_pool = await self.api_client.get_dark_pool(
                self.ticker,
                limit=100
            )
            
            return dark_pool.get('data', [])
        except Exception as e:
            logger.error(f"Error fetching dark pool: {e}")
            raise
    
    async def _fetch_net_premium_data(self) -> Dict[str, Any]:
        """Fetch net premium ticks"""
        try:
            net_prem = await self.api_client.get_net_prem_ticks(self.ticker)
            return net_prem
        except Exception as e:
            logger.error(f"Error fetching net premium: {e}")
            raise
    
    # ========================================================================
    # ANALYSIS METHODS
    # ========================================================================
    
    async def _analyze_gex(self) -> List[Dict]:
        """
        Analyze GEX data for pivot points
        
        Finds:
        - Positive GEX walls (resistance - dealers sell to hedge)
        - Negative GEX walls (support - dealers amplify moves)
        - Zero GEX levels (high volatility zones)
        """
        signals = []
        
        if not self.current_gex_data:
            return signals
        
        try:
            strikes_data = self.current_gex_data.get('by_strike', {}).get('data', [])
            
            if not strikes_data:
                return signals
            
            # Find significant GEX levels
            for strike_info in strikes_data:
                strike = strike_info.get('strike')
                total_gex = strike_info.get('total_gex', 0)
                call_gex = strike_info.get('call_gex', 0)
                put_gex = strike_info.get('put_gex', 0)
                
                if abs(total_gex) < self.gex_threshold:
                    continue
                
                # Calculate distance from spot
                if self.spot_price:
                    distance_pct = ((strike - self.spot_price) / self.spot_price) * 100
                else:
                    distance_pct = 0
                
                # Positive GEX = Resistance (price magnet/ceiling)
                if total_gex > self.gex_threshold:
                    if abs(distance_pct) < 2:  # Within 2% of spot
                        signals.append({
                            'type': AlertType.GEX_PIVOT,
                            'title': f'🔴 GEX Resistance Wall at ${strike:.0f}',
                            'description': (
                                f'Massive positive GEX ({total_gex:,.0f}) at ${strike:.0f}. '
                                f'Currently {distance_pct:+.2f}% from spot (${self.spot_price:.2f}). '
                                f'Dealers will sell to hedge, creating resistance. Price likely to pin here.'
                            ),
                            'priority': 8 if abs(distance_pct) < 1 else 7,
                            'score': min(10, abs(total_gex) / self.gex_threshold),
                            'strike': strike,
                            'gex': total_gex,
                            'distance_pct': distance_pct,
                            'signal_type': 'resistance'
                        })
                
                # Negative GEX = Support/Amplification
                elif total_gex < -self.gex_threshold:
                    if abs(distance_pct) < 3:  # Within 3% of spot
                        signals.append({
                            'type': AlertType.GEX_PIVOT,
                            'title': f'🟢 Negative GEX Zone at ${strike:.0f}',
                            'description': (
                                f'Negative GEX ({total_gex:,.0f}) at ${strike:.0f}. '
                                f'Currently {distance_pct:+.2f}% from spot (${self.spot_price:.2f}). '
                                f'Dealers will amplify moves - expect high volatility if price reaches this level!'
                            ),
                            'priority': 9 if abs(distance_pct) < 1.5 else 7,
                            'score': min(10, abs(total_gex) / self.gex_threshold),
                            'strike': strike,
                            'gex': total_gex,
                            'distance_pct': distance_pct,
                            'signal_type': 'amplification'
                        })
            
            logger.info(f"✅ GEX Analysis: Found {len(signals)} pivot signals")
        
        except Exception as e:
            logger.error(f"GEX analysis error: {e}")
        
        return signals
    
    async def _analyze_flow(self) -> List[Dict]:
        """
        Analyze options flow for pressure signals
        
        Detects:
        - Aggressive call/put buying
        - Large premium orders
        - Unusual volume
        - Directional pressure
        """
        signals = []
        
        if not self.current_flow_data:
            return signals
        
        try:
            # Aggregate flow by direction
            call_premium = sum(
                f.get('premium', 0) 
                for f in self.current_flow_data 
                if f.get('option_type') == 'CALL'
            )
            
            put_premium = sum(
                f.get('premium', 0) 
                for f in self.current_flow_data 
                if f.get('option_type') == 'PUT'
            )
            
            total_premium = call_premium + put_premium
            
            if total_premium == 0:
                return signals
            
            # Calculate call/put ratio
            cp_ratio = call_premium / put_premium if put_premium > 0 else 999
            
            # Detect strong directional pressure
            if cp_ratio > 3:  # Strong call buying
                signals.append({
                    'type': AlertType.FLOW_ALERT,
                    'title': f'🔥 Heavy Call Buying on {self.ticker}',
                    'description': (
                        f'Strong bullish flow detected! '
                        f'Call premium: ${call_premium:,.0f}, Put premium: ${put_premium:,.0f}. '
                        f'Call/Put Ratio: {cp_ratio:.2f}x. '
                        f'Total flows: {len(self.current_flow_data)}'
                    ),
                    'priority': 8,
                    'score': min(10, cp_ratio / 2),
                    'call_premium': call_premium,
                    'put_premium': put_premium,
                    'cp_ratio': cp_ratio,
                    'signal_type': 'bullish_flow'
                })
            
            elif cp_ratio < 0.33:  # Strong put buying
                signals.append({
                    'type': AlertType.FLOW_ALERT,
                    'title': f'⚠️ Heavy Put Buying on {self.ticker}',
                    'description': (
                        f'Strong bearish flow detected! '
                        f'Put premium: ${put_premium:,.0f}, Call premium: ${call_premium:,.0f}. '
                        f'Put/Call Ratio: {1/cp_ratio:.2f}x. '
                        f'Total flows: {len(self.current_flow_data)}'
                    ),
                    'priority': 8,
                    'score': min(10, (1/cp_ratio) / 2) if cp_ratio > 0 else 10,
                    'call_premium': call_premium,
                    'put_premium': put_premium,
                    'cp_ratio': cp_ratio,
                    'signal_type': 'bearish_flow'
                })
            
            # Find individual large trades
            for flow in self.current_flow_data:
                premium = flow.get('premium', 0)
                
                if premium > 500000:  # >$500k trades
                    signals.append({
                        'type': AlertType.FLOW_ALERT,
                        'title': f'💰 Large {flow.get("option_type")} Order: ${premium:,.0f}',
                        'description': (
                            f'Massive {flow.get("option_type")} order detected: '
                            f'${flow.get("strike"):.0f} strike, '
                            f'${premium:,.0f} premium, '
                            f'{flow.get("volume", 0)} contracts'
                        ),
                        'priority': 9 if premium > 1000000 else 7,
                        'score': min(10, premium / 100000),
                        **flow,
                        'signal_type': 'large_order'
                    })
            
            logger.info(f"✅ Flow Analysis: Found {len(signals)} flow signals")
        
        except Exception as e:
            logger.error(f"Flow analysis error: {e}")
        
        return signals
    
    async def _analyze_zero_dte(self) -> List[Dict]:
        """
        Analyze 0DTE opportunities
        
        Looks for:
        - High volume 0DTE options
        - Unusual activity on same-day expiry
        - Gamma squeeze setups
        """
        signals = []
        
        if not self.current_flow_data:
            return signals
        
        try:
            today = datetime.now().date()
            
            # Filter 0DTE flows
            zero_dte_flows = [
                f for f in self.current_flow_data
                if f.get('expiry') and 
                datetime.fromisoformat(f['expiry'].replace('Z', '+00:00')).date() == today
            ]
            
            if not zero_dte_flows:
                return signals
            
            # Aggregate by strike
            strike_volume = defaultdict(lambda: {'call_volume': 0, 'put_volume': 0, 'premium': 0})
            
            for flow in zero_dte_flows:
                strike = flow.get('strike')
                volume = flow.get('volume', 0)
                premium = flow.get('premium', 0)
                option_type = flow.get('option_type')
                
                if option_type == 'CALL':
                    strike_volume[strike]['call_volume'] += volume
                else:
                    strike_volume[strike]['put_volume'] += volume
                
                strike_volume[strike]['premium'] += premium
            
            # Find interesting 0DTE setups
            for strike, data in strike_volume.items():
                total_volume = data['call_volume'] + data['put_volume']
                
                if total_volume > 1000:  # High volume threshold
                    # Potential gamma squeeze if calls dominate
                    if data['call_volume'] > data['put_volume'] * 2:
                        distance_pct = ((strike - self.spot_price) / self.spot_price) * 100 if self.spot_price else 0
                        
                        signals.append({
                            'type': AlertType.FLOW_ALERT,
                            'title': f'⚡ 0DTE Gamma Setup at ${strike:.0f}',
                            'description': (
                                f'Heavy 0DTE call buying at ${strike:.0f} strike. '
                                f'Call volume: {data["call_volume"]:,}, Put volume: {data["put_volume"]:,}. '
                                f'Premium: ${data["premium"]:,.0f}. '
                                f'Strike is {distance_pct:+.2f}% from spot. '
                                f'Potential gamma squeeze if price approaches!'
                            ),
                            'priority': 8 if abs(distance_pct) < 1 else 7,
                            'score': min(10, total_volume / 200),
                            'strike': strike,
                            'call_volume': data['call_volume'],
                            'put_volume': data['put_volume'],
                            'premium': data['premium'],
                            'distance_pct': distance_pct,
                            'signal_type': '0dte_gamma'
                        })
            
            logger.info(f"✅ 0DTE Analysis: Found {len(signals)} opportunities")
        
        except Exception as e:
            logger.error(f"0DTE analysis error: {e}")
        
        return signals
    
    async def _analyze_dark_pool(self) -> List[Dict]:
        """
        Analyze dark pool data for institutional levels
        
        Finds:
        - Price levels with repeated large blocks
        - Accumulation/distribution zones
        - Support/resistance from institutional activity
        """
        signals = []
        
        if not self.current_dark_pool_data:
            return signals
        
        try:
            # Group by price level (rounded to nearest dollar)
            price_levels = defaultdict(lambda: {'trades': 0, 'volume': 0, 'value': 0})
            
            for trade in self.current_dark_pool_data:
                price = trade.get('price', 0)
                size = trade.get('size', 0)
                
                # Round to nearest $0.50
                price_level = round(price * 2) / 2
                
                price_levels[price_level]['trades'] += 1
                price_levels[price_level]['volume'] += size
                price_levels[price_level]['value'] += price * size
            
            # Find significant levels
            for price_level, data in price_levels.items():
                if data['trades'] >= 5 and data['value'] > 1000000:  # Multiple large trades
                    distance_pct = ((price_level - self.spot_price) / self.spot_price) * 100 if self.spot_price else 0
                    
                    if abs(distance_pct) < 2:  # Within 2% of spot
                        signals.append({
                            'type': AlertType.DARK_POOL,
                            'title': f'🏦 Dark Pool Level at ${price_level:.2f}',
                            'description': (
                                f'Significant dark pool activity at ${price_level:.2f}. '
                                f'{data["trades"]} trades, {data["volume"]:,} shares, '
                                f'${data["value"]:,.0f} total value. '
                                f'Level is {distance_pct:+.2f}% from spot. '
                                f'Institutional support/resistance likely here.'
                            ),
                            'priority': 8 if abs(distance_pct) < 1 else 7,
                            'score': min(10, data['trades']),
                            'price_level': price_level,
                            'trades': data['trades'],
                            'volume': data['volume'],
                            'value': data['value'],
                            'distance_pct': distance_pct,
                            'signal_type': 'dark_pool_level'
                        })
            
            logger.info(f"✅ Dark Pool Analysis: Found {len(signals)} levels")
        
        except Exception as e:
            logger.error(f"Dark pool analysis error: {e}")
        
        return signals
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current scanner summary"""
        return {
            **self.get_stats(),
            'spot_price': self.spot_price,
            'gex_data_available': bool(self.current_gex_data),
            'flow_count': len(self.current_flow_data),
            'dark_pool_count': len(self.current_dark_pool_data)
        }


if __name__ == '__main__':
    # Test the scanner
    async def test():
        scanner = IntradaySPYScanner(ticker='SPY')
        
        # Run single scan
        await scanner.start()
        
        # Print summary
        summary = scanner.get_summary()
        logger.info(f"Scanner Summary: {summary}")
    
    asyncio.run(test())
