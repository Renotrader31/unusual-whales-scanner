"""
Mode 3: Long-Term Investment Scanner
Identifies high-conviction long-term plays using fundamental + insider signals
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from .base_scanner import BaseScanner
from core.scoring import ScoringEngine


class LongTermScanner(BaseScanner):
    """
    Long-Term Investment Scanner - Mode 3
    
    Target: Multi-month to multi-year holdings
    Focus: Fundamental catalysts + insider activity + macro trends
    
    Key Strategies:
    1. Congress trading (following the smart money)
    2. Institutional accumulation (13F filings)
    3. Insider buying clusters
    4. Sector rotation (seasonality)
    5. Short squeeze candidates
    6. Undervalued with catalysts
    """
    
    def __init__(self, config, api_client, db_manager=None, cache_manager=None):
        super().__init__(
            mode=3,
            name="Long-Term Investment",
            config=config,
            api_client=api_client,
            db_manager=db_manager,
            cache_manager=cache_manager
        )
        
        self.scorer = ScoringEngine()
        
        # Long-term specific settings
        self.min_market_cap = 1_000_000_000  # $1B+ for stability
        self.lookback_days = 90  # 3 months of data
        
        # Universe: S&P 500 + high-growth sectors
        self.universe = self._build_universe()
        
        logger.info(f"Mode 3 Scanner initialized - Universe: {len(self.universe)} tickers")
    
    def _build_universe(self) -> List[str]:
        """Build scanning universe"""
        # Core holdings - blue chips + growth
        core = [
            # Mega Cap Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
            # AI/Cloud
            "AMD", "AVGO", "CRM", "ORCL", "ADBE", "NOW",
            # Semiconductors
            "TSM", "ASML", "INTC", "QCOM", "MU",
            # Finance
            "JPM", "BAC", "V", "MA", "GS", "BRK.B",
            # Healthcare/Biotech
            "UNH", "JNJ", "LLY", "ABBV", "TMO", "GILD",
            # Consumer
            "WMT", "COST", "HD", "MCD", "DIS", "NFLX",
            # Energy
            "XOM", "CVX", "COP", "SLB",
            # Industrial
            "BA", "CAT", "GE", "RTX",
            # Emerging Tech
            "PLTR", "COIN", "SHOP", "SQ", "HOOD",
            # ETFs for sector plays
            "SPY", "QQQ", "IWM", "XLF", "XLE", "XLK", "XLV"
        ]
        
        return core
    
    async def scan(self) -> Dict:
        """Execute long-term investment scan"""
        scan_start = datetime.now()
        logger.info(f"Starting Mode 3 scan at {scan_start.strftime('%H:%M:%S')}")
        
        results = {
            'timestamp': scan_start.isoformat(),
            'mode': 3,
            'tickers_scanned': 0,
            'signals_found': 0,
            'top_picks': [],
            'congress_activity': [],
            'short_squeeze_candidates': [],
            'sector_momentum': {}
        }
        
        try:
            # Fetch macro data
            congress_trades = await self._fetch_recent_congress_trades()
            results['congress_activity'] = congress_trades[:10]
            
            # Scan tickers
            signals = []
            
            for ticker in self.universe:
                try:
                    logger.debug(f"Analyzing {ticker}...")
                    signal = await self._analyze_longterm(ticker)
                    
                    if signal and signal['score'] >= 7.0:  # High bar for long-term plays
                        signals.append(signal)
                        results['signals_found'] += 1
                    
                    results['tickers_scanned'] += 1
                    
                    # Rate limiting
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    logger.error(f"Error scanning {ticker}: {e}")
                    continue
            
            # Sort by conviction score
            signals.sort(key=lambda x: x['score'], reverse=True)
            results['top_picks'] = signals[:15]  # Top 15 long-term plays
            
            # Find short squeeze candidates
            results['short_squeeze_candidates'] = await self._find_short_squeeze_candidates()
            
            # Analyze sector momentum
            results['sector_momentum'] = await self._analyze_sector_momentum()
            
            # Generate high-conviction alerts
            for signal in results['top_picks'][:5]:  # Top 5 only
                if signal['score'] >= 8.0:
                    await self._generate_alert(signal)
            
            scan_duration = (datetime.now() - scan_start).total_seconds()
            results['scan_duration_seconds'] = scan_duration
            
            logger.info(f"Mode 3 scan complete: {results['signals_found']} signals in {scan_duration:.1f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Mode 3 scan failed: {e}")
            raise
    
    async def _analyze_longterm(self, ticker: str) -> Optional[Dict]:
        """Comprehensive long-term analysis"""
        try:
            # Fetch all relevant data
            stock_state, congress, institutional, shorts, seasonality = await asyncio.gather(
                self._fetch_stock_state(ticker),
                self._fetch_congress_trades(ticker),
                self._fetch_institutional_changes(ticker),
                self._fetch_short_interest(ticker),
                self._fetch_seasonality(ticker),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(stock_state, Exception) or not stock_state:
                return None
            
            price = self._extract_price(stock_state)
            if not price or price == 0:
                return None
            
            # Score each component
            scores = {}
            
            # 1. Congress Trading Score (follow the smart money)
            scores['congress'] = self._score_congress_activity(congress) if not isinstance(congress, Exception) else 5.0
            
            # 2. Institutional Score (smart money accumulation)
            scores['institutional'] = self._score_institutional_changes(institutional) if not isinstance(institutional, Exception) else 5.0
            
            # 3. Short Interest Score (squeeze potential)
            scores['short_interest'] = self._score_short_squeeze(shorts) if not isinstance(shorts, Exception) else 5.0
            
            # 4. Seasonality Score (historical patterns)
            scores['seasonality'] = self._score_seasonality(seasonality) if not isinstance(seasonality, Exception) else 5.0
            
            # 5. Technical Score (longer-term trend)
            scores['technical'] = await self._score_longterm_technical(ticker, price)
            
            # Calculate conviction score (weighted)
            weights = {
                'congress': 0.30,        # Highest weight - they have insider info
                'institutional': 0.25,   # Big money moves
                'short_interest': 0.15,  # Squeeze potential
                'seasonality': 0.15,     # Historical edge
                'technical': 0.15        # Trend confirmation
            }
            
            conviction_score = sum(scores[k] * weights[k] for k in scores)
            
            # Determine investment thesis
            thesis = self._build_thesis(scores, congress, institutional, shorts)
            
            signal = {
                'ticker': ticker,
                'price': price,
                'score': round(conviction_score, 2),
                'scores': scores,
                'thesis': thesis,
                'catalysts': self._identify_catalysts(congress, institutional, shorts, seasonality),
                'risk_factors': self._identify_risks(shorts, scores),
                'timestamp': datetime.now().isoformat(),
                'time_horizon': '3-12 months',
                'conviction': self._calculate_conviction(scores)
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return None
    
    async def _fetch_recent_congress_trades(self) -> List[Dict]:
        """Fetch recent congress trading activity"""
        try:
            data = await self.api_client.get_congress_trades(limit=50)
            
            if data and 'data' in data:
                trades = []
                for trade in data['data'][:20]:
                    trades.append({
                        'ticker': trade.get('ticker'),
                        'representative': trade.get('representative'),
                        'transaction_type': trade.get('type'),
                        'amount': trade.get('amount'),
                        'date': trade.get('disclosure_date')
                    })
                return trades
            
        except Exception as e:
            logger.debug(f"Congress trades fetch error: {e}")
        
        return []
    
    async def _fetch_stock_state(self, ticker: str) -> Optional[Dict]:
        """Fetch stock state"""
        try:
            return await self.api_client.get_stock_state(ticker)
        except Exception as e:
            logger.debug(f"Stock state error for {ticker}: {e}")
            return None
    
    async def _fetch_congress_trades(self, ticker: str) -> Optional[Dict]:
        """Fetch congress trades for specific ticker"""
        try:
            return await self.api_client.get_congress_trades(ticker=ticker, limit=20)
        except Exception as e:
            logger.debug(f"Congress trades error for {ticker}: {e}")
            return None
    
    async def _fetch_institutional_changes(self, ticker: str) -> Optional[Dict]:
        """Fetch institutional holdings changes"""
        try:
            return await self.api_client.get_institutional_ownership(ticker)
        except Exception as e:
            logger.debug(f"Institutional error for {ticker}: {e}")
            return None
    
    async def _fetch_short_interest(self, ticker: str) -> Optional[Dict]:
        """Fetch short interest data"""
        try:
            return await self.api_client.get_short_volume(ticker)
        except Exception as e:
            logger.debug(f"Short interest error for {ticker}: {e}")
            return None
    
    async def _fetch_seasonality(self, ticker: str) -> Optional[Dict]:
        """Fetch seasonality patterns"""
        try:
            return await self.api_client.get_seasonality_monthly(ticker)
        except Exception as e:
            logger.debug(f"Seasonality error for {ticker}: {e}")
            return None
    
    def _extract_price(self, stock_state: Dict) -> float:
        """Extract current price"""
        try:
            if stock_state and 'data' in stock_state:
                data = stock_state['data']
                return float(data.get('close', data.get('price', 0)))
        except:
            pass
        return 0
    
    def _score_congress_activity(self, congress_data: Dict) -> float:
        """Score based on congress trading - they know things!"""
        try:
            if not congress_data or 'data' not in congress_data:
                return 5.0
            
            trades = congress_data['data']
            if not trades:
                return 5.0
            
            # Count buys vs sells in last 90 days
            recent_trades = trades[:10]  # Last 10 trades
            
            buys = sum(1 for t in recent_trades if t.get('type', '').lower() in ['purchase', 'buy'])
            sells = sum(1 for t in recent_trades if t.get('type', '').lower() in ['sale', 'sell'])
            
            # Heavy buying by congress = VERY bullish
            if buys >= 3 and sells == 0:
                return 10.0  # Maximum conviction
            elif buys > sells * 2:
                return 9.0
            elif buys > sells:
                return 7.5
            elif sells > buys * 2:
                return 3.0  # They're getting out!
            else:
                return 5.0
                
        except Exception as e:
            logger.debug(f"Congress scoring error: {e}")
            return 5.0
    
    def _score_institutional_changes(self, inst_data: Dict) -> float:
        """Score institutional buying/selling"""
        try:
            if not inst_data or 'data' not in inst_data:
                return 5.0
            
            data = inst_data['data']
            
            # Look for accumulation pattern
            if isinstance(data, dict):
                pct_change = float(data.get('pct_change', 0))
                
                # Significant institutional buying
                if pct_change > 10:
                    return 9.0
                elif pct_change > 5:
                    return 7.5
                elif pct_change > 0:
                    return 6.0
                elif pct_change < -10:
                    return 3.0  # They're dumping
                else:
                    return 5.0
            
            return 5.0
            
        except Exception as e:
            logger.debug(f"Institutional scoring error: {e}")
            return 5.0
    
    def _score_short_squeeze(self, short_data: Dict) -> float:
        """Score short squeeze potential"""
        try:
            if not short_data or 'data' not in short_data:
                return 5.0
            
            data = short_data['data']
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            short_ratio = float(data.get('short_volume_ratio', 0))
            days_to_cover = float(data.get('days_to_cover', 0))
            
            # High short interest + high days to cover = squeeze potential
            if short_ratio > 0.20 and days_to_cover > 5:
                return 9.0  # Prime squeeze candidate
            elif short_ratio > 0.15 and days_to_cover > 3:
                return 7.5
            elif short_ratio > 0.10:
                return 6.0
            else:
                return 5.0
                
        except Exception as e:
            logger.debug(f"Short squeeze scoring error: {e}")
            return 5.0
    
    def _score_seasonality(self, season_data: Dict) -> float:
        """Score based on seasonal patterns"""
        try:
            if not season_data or 'data' not in season_data:
                return 5.0
            
            current_month = datetime.now().month
            
            data = season_data['data']
            if isinstance(data, list):
                # Find current month's performance
                for month_data in data:
                    month_num = month_data.get('month')
                    if month_num == current_month:
                        avg_return = float(month_data.get('avg_return', 0))
                        win_rate = float(month_data.get('win_rate', 0.5))
                        
                        # Strong seasonal tailwind
                        if avg_return > 3 and win_rate > 0.6:
                            return 8.5
                        elif avg_return > 1 and win_rate > 0.55:
                            return 7.0
                        elif avg_return > 0:
                            return 6.0
                        else:
                            return 4.0
            
            return 5.0
            
        except Exception as e:
            logger.debug(f"Seasonality scoring error: {e}")
            return 5.0
    
    async def _score_longterm_technical(self, ticker: str, price: float) -> float:
        """Score long-term technical setup"""
        try:
            # Get longer-term price history
            hist = await self.api_client.get_historical_ohlc(ticker, days=180)
            
            if hist and 'data' in hist:
                prices = [float(d.get('close', 0)) for d in hist['data'] if d.get('close')]
                
                if len(prices) >= 50:
                    # Simple trend analysis
                    sma_50 = sum(prices[:50]) / 50
                    sma_200 = sum(prices) / len(prices) if len(prices) >= 200 else sma_50
                    
                    # Golden cross = bullish
                    if price > sma_50 > sma_200:
                        return 8.0
                    elif price > sma_50:
                        return 6.5
                    else:
                        return 4.0
            
            return 5.0
            
        except Exception as e:
            logger.debug(f"Technical scoring error: {e}")
            return 5.0
    
    def _build_thesis(self, scores: Dict, congress, institutional, shorts) -> str:
        """Build investment thesis"""
        themes = []
        
        if scores.get('congress', 0) >= 8:
            themes.append("Congress accumulation")
        if scores.get('institutional', 0) >= 8:
            themes.append("Institutional buying")
        if scores.get('short_interest', 0) >= 8:
            themes.append("Short squeeze setup")
        if scores.get('seasonality', 0) >= 7:
            themes.append("Seasonal tailwind")
        
        if themes:
            return " + ".join(themes)
        else:
            return "Multi-factor opportunity"
    
    def _identify_catalysts(self, congress, institutional, shorts, seasonality) -> List[str]:
        """Identify key catalysts"""
        catalysts = []
        
        if congress and 'data' in congress and len(congress['data']) > 0:
            catalysts.append("Recent congress buying")
        
        if institutional and 'data' in institutional:
            catalysts.append("Institutional accumulation")
        
        if shorts and 'data' in shorts:
            data = shorts['data']
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            short_ratio = float(data.get('short_volume_ratio', 0)) if isinstance(data, dict) else 0
            if short_ratio > 0.15:
                catalysts.append("High short interest (squeeze potential)")
        
        return catalysts[:3]  # Top 3
    
    def _identify_risks(self, shorts, scores: Dict) -> List[str]:
        """Identify risk factors"""
        risks = []
        
        # Low conviction in any area
        for key, score in scores.items():
            if score < 4.0:
                risks.append(f"Weak {key} signal")
        
        # Check if heavily shorted (could be for good reason)
        if shorts and 'data' in shorts:
            data = shorts['data']
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            short_ratio = float(data.get('short_volume_ratio', 0)) if isinstance(data, dict) else 0
            if short_ratio > 0.30:
                risks.append("Very high short interest (fundamental concerns?)")
        
        return risks[:2]  # Top 2
    
    def _calculate_conviction(self, scores: Dict) -> str:
        """Calculate overall conviction"""
        avg = sum(scores.values()) / len(scores)
        std = (sum((s - avg) ** 2 for s in scores.values()) / len(scores)) ** 0.5
        
        # High average + low variance = high conviction
        if avg >= 8.0 and std < 1.0:
            return "VERY HIGH"
        elif avg >= 7.5 and std < 1.5:
            return "HIGH"
        elif avg >= 7.0:
            return "MODERATE"
        else:
            return "LOW"
    
    async def _find_short_squeeze_candidates(self) -> List[Dict]:
        """Find potential short squeeze candidates"""
        candidates = []
        
        try:
            # This would scan for high short interest
            # Simplified for now
            high_short_tickers = ["GME", "AMC", "BBBY"]  # Placeholder
            
            for ticker in high_short_tickers[:5]:
                try:
                    short_data = await self.api_client.get_short_volume(ticker)
                    if short_data and 'data' in short_data:
                        candidates.append({
                            'ticker': ticker,
                            'short_data': short_data['data']
                        })
                except:
                    pass
            
        except Exception as e:
            logger.debug(f"Short squeeze scan error: {e}")
        
        return candidates
    
    async def _analyze_sector_momentum(self) -> Dict:
        """Analyze sector momentum"""
        try:
            sectors = {
                'Technology': ['XLK'],
                'Finance': ['XLF'],
                'Energy': ['XLE'],
                'Healthcare': ['XLV'],
                'Consumer': ['XLY']
            }
            
            momentum = {}
            
            for sector, etfs in sectors.items():
                # Simplified - would do deeper analysis
                momentum[sector] = {
                    'score': 5.0,  # Placeholder
                    'trend': 'neutral'
                }
            
            return momentum
            
        except Exception as e:
            logger.debug(f"Sector momentum error: {e}")
            return {}
    
    async def _generate_alert(self, signal: Dict):
        """Generate alert for high-conviction play"""
        alert = {
            'mode': 3,
            'ticker': signal['ticker'],
            'score': signal['score'],
            'thesis': signal['thesis'],
            'catalysts': signal['catalysts'],
            'conviction': signal['conviction'],
            'time_horizon': signal['time_horizon'],
            'timestamp': datetime.now().isoformat(),
            'priority': 9 if signal['score'] >= 8.5 else 8
        }
        
        if self.db_manager:
            try:
                await self.db_manager.store_alert(alert)
            except Exception as e:
                logger.error(f"Failed to store alert: {e}")
        
        logger.info(f"🎯 LONG-TERM PLAY: {signal['ticker']} - {signal['thesis']} - Score: {signal['score']}")
