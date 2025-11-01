"""
Unusual Whales API Client
Main client for interacting with the UW API with rate limiting, retries, and caching
"""
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from loguru import logger
import backoff
from enum import Enum

from .endpoints import UnusualWhalesEndpoints, Endpoint
from .rate_limiter import get_rate_limiter, AdaptiveRateLimiter
from config import get_settings


class APIError(Exception):
    """Base exception for API errors"""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded"""
    pass


class AuthenticationError(APIError):
    """Authentication failed"""
    pass


class NotFoundError(APIError):
    """Resource not found"""
    pass


class UnusualWhalesClient:
    """
    Async client for Unusual Whales API
    
    Features:
    - Automatic rate limiting
    - Exponential backoff on failures
    - Response caching
    - Request/response logging
    - Connection pooling
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        rate_limiter: Optional[AdaptiveRateLimiter] = None,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Initialize API client
        
        Args:
            api_key: UW API key (will use settings if not provided)
            base_url: API base URL (will use settings if not provided)
            rate_limiter: Custom rate limiter instance
            session: Existing aiohttp session (creates new if not provided)
        """
        self.settings = get_settings()
        self.api_key = api_key or self.settings.uw_api_key
        self.base_url = (base_url or self.settings.uw_base_url).rstrip('/')
        self.rate_limiter = rate_limiter or get_rate_limiter()
        self._session = session
        self._own_session = session is None
        
        # Cache configuration
        self.cache_enabled = self.settings.cache_enabled
        self.cache_ttl = self.settings.cache_ttl
        self._cache: Dict[str, tuple[Any, float]] = {}
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'rate_limit_errors': 0
        }
        
        logger.info(f"UW API Client initialized: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_default_headers()
            )
    
    async def close(self):
        """Close aiohttp session"""
        if self._session and self._own_session:
            await self._session.close()
            self._session = None
            logger.info("API client session closed")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default request headers"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'UW-Scanner/1.0'
        }
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from URL and params"""
        if params:
            param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{url}?{param_str}"
        return url
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if not self.cache_enabled:
            return None
        
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            age = asyncio.get_event_loop().time() - timestamp
            
            if age < self.cache_ttl:
                self.stats['cache_hits'] += 1
                logger.debug(f"Cache hit: {cache_key} (age: {age:.1f}s)")
                return data
            else:
                # Expired
                del self._cache[cache_key]
        
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Store data in cache"""
        if self.cache_enabled:
            self._cache[cache_key] = (data, asyncio.get_event_loop().time())
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=30
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retries and rate limiting
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            data: Request body data
            use_cache: Whether to use cache for this request
        
        Returns:
            Response JSON data
        
        Raises:
            APIError: On API errors
        """
        await self._ensure_session()
        
        # Check cache for GET requests
        if method == 'GET' and use_cache:
            cache_key = self._get_cache_key(url, params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Make request
        self.stats['total_requests'] += 1
        
        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=data
            ) as response:
                # Check rate limit headers
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = int(response.headers['X-RateLimit-Remaining'])
                    logger.debug(f"Rate limit remaining: {remaining}")
                
                # Handle different status codes
                if response.status == 200:
                    result = await response.json()
                    self.stats['successful_requests'] += 1
                    
                    # Update rate limiter on success
                    if isinstance(self.rate_limiter, AdaptiveRateLimiter):
                        await self.rate_limiter.report_success()
                    
                    # Cache result
                    if method == 'GET' and use_cache:
                        self._set_cache(cache_key, result)
                    
                    return result
                
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                
                elif response.status == 404:
                    raise NotFoundError(f"Resource not found: {url}")
                
                elif response.status == 429:
                    # Rate limited
                    self.stats['rate_limit_errors'] += 1
                    retry_after = response.headers.get('Retry-After')
                    
                    if isinstance(self.rate_limiter, AdaptiveRateLimiter):
                        await self.rate_limiter.report_rate_limit_error(
                            int(retry_after) if retry_after else None
                        )
                    
                    raise RateLimitError(f"Rate limit exceeded. Retry after: {retry_after}")
                
                else:
                    self.stats['failed_requests'] += 1
                    error_text = await response.text()
                    
                    if isinstance(self.rate_limiter, AdaptiveRateLimiter):
                        await self.rate_limiter.report_error(response.status)
                    
                    raise APIError(
                        f"API error {response.status}: {error_text}"
                    )
        
        except aiohttp.ClientError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Request failed: {e}")
            raise APIError(f"Request failed: {e}")
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Make GET request
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            use_cache: Whether to use cache
        
        Returns:
            Response data
        """
        url = f"{self.base_url}{endpoint}"
        return await self._make_request('GET', url, params=params, use_cache=use_cache)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make POST request"""
        url = f"{self.base_url}{endpoint}"
        return await self._make_request('POST', url, params=params, data=data, use_cache=False)
    
    # ========================================================================
    # HIGH-LEVEL API METHODS - Mode 1: Intraday SPY
    # ========================================================================
    
    async def get_flow_alerts(
        self,
        ticker: Optional[str] = None,
        min_premium: Optional[float] = None,
        older_than: Optional[str] = None,
        newer_than: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get options flow alerts"""
        params = {'limit': limit}
        if ticker:
            params['ticker'] = ticker
        if min_premium:
            params['min_premium'] = min_premium
        if older_than:
            params['older_than'] = older_than
        if newer_than:
            params['newer_than'] = newer_than
        
        return await self.get('/api/option-trades/flow-alerts', params=params)
    
    async def get_spot_exposures(
        self,
        ticker: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get spot GEX exposures for ticker"""
        params = {}
        if date:
            params['date'] = date
        
        return await self.get(f'/api/stock/{ticker}/spot-exposures', params=params)
    
    async def get_spot_exposures_by_strike(
        self,
        ticker: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get spot GEX exposures by strike"""
        params = {}
        if date:
            params['date'] = date
        
        return await self.get(f'/api/stock/{ticker}/spot-exposures/strike', params=params)
    
    async def get_net_prem_ticks(
        self,
        ticker: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get net premium ticks for ticker"""
        params = {}
        if date:
            params['date'] = date
        
        return await self.get(f'/api/stock/{ticker}/net-prem-ticks', params=params)
    
    async def get_flow_per_strike_intraday(
        self,
        ticker: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get intraday flow per strike"""
        params = {}
        if date:
            params['date'] = date
        
        return await self.get(f'/api/stock/{ticker}/flow-per-strike-intraday', params=params)
    
    async def get_dark_pool(
        self,
        ticker: str,
        older_than: Optional[str] = None,
        newer_than: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get dark pool data for ticker"""
        params = {'limit': limit}
        if older_than:
            params['older_than'] = older_than
        if newer_than:
            params['newer_than'] = newer_than
        
        return await self.get(f'/api/darkpool/{ticker}', params=params)
    
    async def get_market_top_net_impact(
        self,
        date: Optional[str] = None,
        limit: int = 20,
        issue_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get top tickers by net premium impact"""
        params = {'limit': limit}
        if date:
            params['date'] = date
        if issue_types:
            params['issue_types[]'] = issue_types
        
        return await self.get('/api/market/top-net-impact', params=params)
    
    # ========================================================================
    # Mode 2: Swing Trading (30-45 DTE)
    # ========================================================================
    
    async def get_stock_greeks(self, ticker: str) -> Dict[str, Any]:
        """Get Greek values for ticker"""
        return await self.get(f'/api/stock/{ticker}/greeks')
    
    async def get_greek_exposure_strike(
        self,
        ticker: str,
        expiry: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Greek exposure by strike"""
        params = {}
        if expiry:
            params['expiry'] = expiry
        
        return await self.get(f'/api/stock/{ticker}/greek-exposure/strike', params=params)
    
    async def get_oi_per_strike(self, ticker: str) -> Dict[str, Any]:
        """Get open interest per strike"""
        return await self.get(f'/api/stock/{ticker}/oi-per-strike')
    
    async def get_oi_per_expiry(self, ticker: str) -> Dict[str, Any]:
        """Get open interest per expiry"""
        return await self.get(f'/api/stock/{ticker}/oi-per-expiry')
    
    async def get_realized_volatility(self, ticker: str) -> Dict[str, Any]:
        """Get realized volatility"""
        return await self.get(f'/api/stock/{ticker}/volatility/realized')
    
    async def get_market_correlations(
        self,
        tickers: List[str],
        interval: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get correlation matrix for tickers"""
        params = {'tickers': ','.join(tickers)}
        if interval:
            params['interval'] = interval
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return await self.get('/api/market/correlations', params=params)
    
    # ========================================================================
    # Mode 3: Long-Term Investment
    # ========================================================================
    
    async def get_institution_latest_filings(
        self,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get latest institutional filings"""
        params = {'limit': limit}
        return await self.get('/api/institution/latest_filings', params=params)
    
    async def get_institution_ownership(
        self,
        ticker: str
    ) -> Dict[str, Any]:
        """Get institutional ownership for ticker"""
        return await self.get(f'/api/institution/{ticker}/ownership')
    
    async def get_institution_holdings(
        self,
        name: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get holdings for specific institution"""
        params = {'limit': limit}
        return await self.get(f'/api/institution/{name}/holdings', params=params)
    
    async def get_congress_recent_trades(
        self,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get recent Congressional trades"""
        params = {'limit': limit}
        return await self.get('/api/congress/recent-trades', params=params)
    
    async def get_shorts_data(self, ticker: str) -> Dict[str, Any]:
        """Get short interest data"""
        return await self.get(f'/api/shorts/{ticker}/data')
    
    async def get_shorts_interest_float(self, ticker: str) -> Dict[str, Any]:
        """Get short interest as % of float"""
        return await self.get(f'/api/shorts/{ticker}/interest-float')
    
    async def get_seasonality_ticker_monthly(
        self,
        ticker: str
    ) -> Dict[str, Any]:
        """Get seasonality data for ticker"""
        return await self.get(f'/api/seasonality/{ticker}/monthly')
    
    async def get_news_headlines(
        self,
        ticker: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get news headlines"""
        params = {'limit': limit}
        if ticker:
            params['ticker'] = ticker
        
        return await self.get('/api/news/headlines', params=params)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        rate_limiter_stats = self.rate_limiter.get_stats()
        
        return {
            **self.stats,
            'rate_limiter': rate_limiter_stats,
            'cache_size': len(self._cache)
        }
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info(f"API Client Stats: {stats}")


if __name__ == '__main__':
    # Test client
    async def test():
        async with UnusualWhalesClient() as client:
            try:
                # Test connection
                logger.info("Testing API connection...")
                
                # Get SPY flow
                flow = await client.get_flow_alerts(ticker='SPY', limit=5)
                logger.info(f"✅ Flow alerts retrieved: {len(flow.get('data', []))} items")
                
                # Get SPY GEX
                gex = await client.get_spot_exposures('SPY')
                logger.info(f"✅ GEX data retrieved")
                
                # Stats
                client.log_stats()
                
            except Exception as e:
                logger.error(f"❌ Test failed: {e}")
    
    asyncio.run(test())
