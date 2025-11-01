"""
Mode 2: Swing Trading Scanner (30-45 DTE)
Hunts for medium-term opportunities with technical + fundamental confluence
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from loguru import logger

from .base_scanner import BaseScanner
from core.scoring import ScoringEngine


class SwingTradingScanner(BaseScanner):
    """
    Swing Trading Scanner - Mode 2
    
    Target: 30-45 DTE options with multi-day holding periods
    Focus: Technical setups + institutional activity + IV patterns
    
    Key Strategies:
    1. IV Rank compression/expansion plays
    2. Institutional flow (13F filings)
    3. Earnings run-ups (2-4 weeks before)
    4. Sector rotation momentum
    5. Volume breakouts
    6. Options OI build-up
    """
    
    def __init__(self, config, api_client, db_manager=None, cache_manager=None):
        super().__init__(
            mode=2,
            name="Swing Trading",
            config=config,
            api_client=api_client,
            db_manager=db_manager,
            cache_manager=cache_manager
        )
        
        self.scorer = ScoringEngine()
        
        # Swing trading specific settings
        self.target_dte_min = 30
        self.target_dte_max = 45
        self.min_market_cap = 5_000_000_000  # $5B+ companies
        self.max_tickers_per_scan = 50  # Scan top 50 most active
        
        # Watchlist - can be customized
        self.core_watchlist = [
            # Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "NFLX",
            # Finance
            "JPM", "BAC", "GS", "MS", "C", "WFC",
            # Healthcare
            "UNH", "JNJ", "PFE", "ABBV", "MRK",
            # Consumer
            "WMT", "HD", "MCD", "NKE", "SBUX",
            # Energy
            "XOM", "CVX", "COP",
            # Industrial
            "BA", "CAT", "GE",
            # ETFs
            "SPY", "QQQ", "IWM", "DIA"
        ]
        
        logger.info(f"Mode 2 Scanner initialized - Watchlist: {len(self.core_watchlist)} tickers")
    
    async def scan(self) -> Dict:
        """Execute swing trading scan across watchlist"""
        scan_start = datetime.now()
        logger.info(f"Starting Mode 2 scan at {scan_start.strftime('%H:%M:%S')}")
        
        results = {
            'timestamp': scan_start.isoformat(),
            'mode': 2,
            'tickers_scanned': 0,
            'signals_found': 0,
            'top_signals': [],
            'analysis': {}
        }
        
        try:
            # Get market overview
            market_tide = await self._fetch_market_tide()
            results['market_sentiment'] = market_tide
            
            # Scan each ticker
            signals = []
            
            for ticker in self.core_watchlist:
                try:
                    logger.debug(f"Scanning {ticker}...")
                    signal = await self._analyze_ticker(ticker)
                    
                    if signal and signal['score'] >= 6.5:  # Higher threshold for swing trades
                        signals.append(signal)
                        results['signals_found'] += 1
                    
                    results['tickers_scanned'] += 1
                    
                    # Rate limiting - be nice to API
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"Error scanning {ticker}: {e}")
                    continue
            
            # Sort signals by score
            signals.sort(key=lambda x: x['score'], reverse=True)
            results['top_signals'] = signals[:10]  # Top 10 signals
            
            # Generate alerts for high-confidence signals
            for signal in results['top_signals']:
                if signal['score'] >= 7.5:
                    await self._generate_alert(signal)
            
            scan_duration = (datetime.now() - scan_start).total_seconds()
            results['scan_duration_seconds'] = scan_duration
            
            logger.info(f"Mode 2 scan complete: {results['signals_found']} signals in {scan_duration:.1f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Mode 2 scan failed: {e}")
            raise
    
    async def _analyze_ticker(self, ticker: str) -> Optional[Dict]:
        """Deep analysis of a single ticker for swing opportunities"""
        try:
            # Fetch all data in parallel
            stock_state, iv_rank, flow_data, oi_data, institutional = await asyncio.gather(
                self._fetch_stock_state(ticker),
                self._fetch_iv_rank(ticker),
                self._fetch_flow_summary(ticker),
                self._fetch_oi_analysis(ticker),
                self._fetch_institutional_activity(ticker),
                return_exceptions=True
            )
            
            # Handle exceptions
            for data in [stock_state, iv_rank, flow_data, oi_data, institutional]:
                if isinstance(data, Exception):
                    logger.debug(f"Data fetch error for {ticker}: {data}")
            
            if not stock_state or isinstance(stock_state, Exception):
                return None
            
            # Extract key metrics
            price = self._extract_price(stock_state)
            volume = self._extract_volume(stock_state)
            
            if not price or price == 0:
                return None
            
            # Score components
            scores = {}
            
            # 1. IV Rank Score
            scores['iv_rank'] = self._score_iv_rank(iv_rank) if not isinstance(iv_rank, Exception) else 5.0
            
            # 2. Flow Score (institutional buying/selling)
            scores['flow'] = self._score_swing_flow(flow_data) if not isinstance(flow_data, Exception) else 5.0
            
            # 3. Open Interest Score (positioning)
            scores['oi'] = self._score_oi_buildup(oi_data) if not isinstance(oi_data, Exception) else 5.0
            
            # 4. Institutional Score
            scores['institutional'] = self._score_institutional(institutional) if not isinstance(institutional, Exception) else 5.0
            
            # 5. Earnings Catalyst Score
            scores['earnings'] = await self._score_earnings_catalyst(ticker, price)
            
            # Calculate composite score
            weights = {
                'iv_rank': 0.25,
                'flow': 0.25,
                'oi': 0.20,
                'institutional': 0.20,
                'earnings': 0.10
            }
            
            composite_score = sum(scores[k] * weights[k] for k in scores)
            
            # Determine trade direction
            direction = self._determine_direction(flow_data, oi_data)
            
            # Build signal
            signal = {
                'ticker': ticker,
                'price': price,
                'volume': volume,
                'score': round(composite_score, 2),
                'scores': scores,
                'direction': direction,
                'strategy': self._recommend_strategy(scores, direction),
                'target_dte': f"{self.target_dte_min}-{self.target_dte_max}",
                'timestamp': datetime.now().isoformat(),
                'confidence': self._calculate_confidence(scores)
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return None
    
    async def _fetch_market_tide(self) -> Dict:
        """Get overall market sentiment"""
        try:
            data = await self.api_client.get_market_tide()
            if data and 'data' in data:
                info = data['data']
                return {
                    'sentiment': info.get('sentiment', 'neutral'),
                    'bullish_premium': float(info.get('bullish_premium', 0)),
                    'bearish_premium': float(info.get('bearish_premium', 0)),
                    'net_premium': float(info.get('net_premium', 0))
                }
        except Exception as e:
            logger.debug(f"Market tide fetch error: {e}")
        
        return {'sentiment': 'neutral', 'net_premium': 0}
    
    async def _fetch_stock_state(self, ticker: str) -> Optional[Dict]:
        """Fetch current stock state"""
        try:
            return await self.api_client.get_stock_state(ticker)
        except Exception as e:
            logger.debug(f"Stock state error for {ticker}: {e}")
            return None
    
    async def _fetch_iv_rank(self, ticker: str) -> Optional[Dict]:
        """Fetch IV rank data"""
        try:
            return await self.api_client.get_iv_rank(ticker)
        except Exception as e:
            logger.debug(f"IV rank error for {ticker}: {e}")
            return None
    
    async def _fetch_flow_summary(self, ticker: str) -> Optional[Dict]:
        """Fetch options flow summary"""
        try:
            # Get last 7 days of flow
            return await self.api_client.get_net_prem(ticker)
        except Exception as e:
            logger.debug(f"Flow summary error for {ticker}: {e}")
            return None
    
    async def _fetch_oi_analysis(self, ticker: str) -> Optional[Dict]:
        """Fetch open interest analysis"""
        try:
            return await self.api_client.get_oi_change(ticker)
        except Exception as e:
            logger.debug(f"OI analysis error for {ticker}: {e}")
            return None
    
    async def _fetch_institutional_activity(self, ticker: str) -> Optional[Dict]:
        """Fetch institutional activity"""
        try:
            return await self.api_client.get_institutional_activity(ticker)
        except Exception as e:
            logger.debug(f"Institutional error for {ticker}: {e}")
            return None
    
    def _extract_price(self, stock_state: Dict) -> float:
        """Extract price from stock state"""
        try:
            if stock_state and 'data' in stock_state:
                data = stock_state['data']
                return float(data.get('close', data.get('price', 0)))
        except:
            pass
        return 0
    
    def _extract_volume(self, stock_state: Dict) -> int:
        """Extract volume from stock state"""
        try:
            if stock_state and 'data' in stock_state:
                return int(stock_state['data'].get('volume', 0))
        except:
            pass
        return 0
    
    def _score_iv_rank(self, iv_data: Dict) -> float:
        """Score based on IV rank - looking for extremes"""
        try:
            if not iv_data or 'data' not in iv_data:
                return 5.0
            
            iv_rank = float(iv_data['data'].get('iv_rank', 0.5))
            
            # High IV rank (>70%) = good for selling premium
            # Low IV rank (<30%) = good for buying premium
            if iv_rank > 0.7:
                return 8.0 + (iv_rank - 0.7) * 6.67  # Scale to 10
            elif iv_rank < 0.3:
                return 8.0 + (0.3 - iv_rank) * 6.67
            else:
                return 5.0  # Neutral
                
        except Exception as e:
            logger.debug(f"IV rank scoring error: {e}")
            return 5.0
    
    def _score_swing_flow(self, flow_data: Dict) -> float:
        """Score options flow for swing trading"""
        try:
            if not flow_data or 'data' not in flow_data:
                return 5.0
            
            data = flow_data['data']
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            call_prem = float(data.get('call_premium', 0))
            put_prem = float(data.get('put_premium', 0))
            
            total = call_prem + put_prem
            if total == 0:
                return 5.0
            
            ratio = call_prem / total
            
            # Strong directional flow scores higher
            if ratio > 0.65 or ratio < 0.35:
                return 8.0
            elif ratio > 0.55 or ratio < 0.45:
                return 6.5
            else:
                return 5.0
                
        except Exception as e:
            logger.debug(f"Flow scoring error: {e}")
            return 5.0
    
    def _score_oi_buildup(self, oi_data: Dict) -> float:
        """Score based on open interest changes"""
        try:
            if not oi_data or 'data' not in oi_data:
                return 5.0
            
            # Look for significant OI increases
            data = oi_data['data']
            if isinstance(data, list) and len(data) > 0:
                # Check for OI increases over last few days
                oi_increases = sum(1 for d in data if d.get('oi_change', 0) > 0)
                
                if oi_increases > len(data) * 0.7:  # 70%+ days with OI increase
                    return 8.5
                elif oi_increases > len(data) * 0.5:
                    return 7.0
                else:
                    return 5.0
            
            return 5.0
            
        except Exception as e:
            logger.debug(f"OI scoring error: {e}")
            return 5.0
    
    def _score_institutional(self, inst_data: Dict) -> float:
        """Score institutional activity"""
        try:
            if not inst_data or 'data' not in inst_data:
                return 5.0
            
            # Look for buying or selling activity
            data = inst_data['data']
            if isinstance(data, list) and len(data) > 0:
                recent = data[:5]  # Last 5 institutional moves
                
                buying = sum(1 for d in recent if d.get('action') == 'buy')
                selling = sum(1 for d in recent if d.get('action') == 'sell')
                
                if buying > selling * 2:  # Strong buying
                    return 8.0
                elif selling > buying * 2:  # Strong selling
                    return 7.5  # Contrarian opportunity
                else:
                    return 5.0
            
            return 5.0
            
        except Exception as e:
            logger.debug(f"Institutional scoring error: {e}")
            return 5.0
    
    async def _score_earnings_catalyst(self, ticker: str, price: float) -> float:
        """Score based on upcoming earnings"""
        try:
            earnings = await self.api_client.get_earnings_calendar(ticker)
            
            if earnings and 'data' in earnings:
                # Check if earnings in next 2-4 weeks
                next_earnings = earnings['data'].get('next_earnings_date')
                if next_earnings:
                    days_until = (datetime.fromisoformat(next_earnings) - datetime.now()).days
                    
                    if 14 <= days_until <= 28:  # Sweet spot for earnings run-up
                        return 8.0
                    elif 7 <= days_until <= 35:
                        return 6.5
            
            return 5.0
            
        except Exception as e:
            logger.debug(f"Earnings scoring error: {e}")
            return 5.0
    
    def _determine_direction(self, flow_data: Dict, oi_data: Dict) -> str:
        """Determine bullish/bearish direction"""
        try:
            # Analyze flow
            if flow_data and 'data' in flow_data:
                data = flow_data['data']
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                
                call_prem = float(data.get('call_premium', 0))
                put_prem = float(data.get('put_premium', 0))
                
                total = call_prem + put_prem
                if total > 0:
                    ratio = call_prem / total
                    
                    if ratio > 0.6:
                        return "BULLISH"
                    elif ratio < 0.4:
                        return "BEARISH"
            
            return "NEUTRAL"
            
        except:
            return "NEUTRAL"
    
    def _recommend_strategy(self, scores: Dict, direction: str) -> str:
        """Recommend specific options strategy"""
        iv_score = scores.get('iv_rank', 5.0)
        
        if iv_score > 7.5:  # High IV
            if direction == "BULLISH":
                return "Bull Put Spread (sell premium)"
            elif direction == "BEARISH":
                return "Bear Call Spread (sell premium)"
            else:
                return "Iron Condor (sell premium)"
        else:  # Low/Normal IV
            if direction == "BULLISH":
                return "Call Debit Spread (buy premium)"
            elif direction == "BEARISH":
                return "Put Debit Spread (buy premium)"
            else:
                return "Wait for setup"
        
        return "Directional play"
    
    def _calculate_confidence(self, scores: Dict) -> str:
        """Calculate confidence level"""
        avg_score = sum(scores.values()) / len(scores)
        std_dev = (sum((s - avg_score) ** 2 for s in scores.values()) / len(scores)) ** 0.5
        
        # Low std dev = high agreement = high confidence
        if std_dev < 1.0 and avg_score >= 7.0:
            return "HIGH"
        elif std_dev < 1.5 and avg_score >= 6.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _generate_alert(self, signal: Dict):
        """Generate alert for high-confidence signal"""
        alert = {
            'mode': 2,
            'ticker': signal['ticker'],
            'score': signal['score'],
            'direction': signal['direction'],
            'strategy': signal['strategy'],
            'price': signal['price'],
            'confidence': signal['confidence'],
            'timestamp': datetime.now().isoformat(),
            'priority': 8 if signal['score'] >= 8.0 else 7
        }
        
        # Store in database if available
        if self.db_manager:
            try:
                await self.db_manager.store_alert(alert)
            except Exception as e:
                logger.error(f"Failed to store alert: {e}")
        
        logger.info(f"🚨 SWING SIGNAL: {signal['ticker']} - {signal['direction']} - Score: {signal['score']}")
