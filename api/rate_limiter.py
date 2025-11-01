"""
Rate Limiter for API requests
Implements token bucket algorithm with async support
"""
import asyncio
import time
from typing import Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with burst support.
    
    Args:
        rate: Number of requests allowed per minute
        burst: Maximum burst capacity
    """
    
    def __init__(self, rate: int = 100, burst: int = 20):
        self.rate = rate  # requests per minute
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        self.request_times = deque(maxlen=rate)
        
        # Calculate token refill rate (tokens per second)
        self.refill_rate = rate / 60.0
        
        logger.info(f"RateLimiter initialized: {rate} req/min, burst={burst}")
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens for making a request.
        Blocks if insufficient tokens available.
        
        Args:
            tokens: Number of tokens to acquire (default 1)
            
        Returns:
            True when tokens acquired
        """
        async with self.lock:
            while True:
                now = time.time()
                
                # Refill tokens based on time elapsed
                time_passed = now - self.last_update
                self.tokens = min(
                    self.burst,
                    self.tokens + (time_passed * self.refill_rate)
                )
                self.last_update = now
                
                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.request_times.append(now)
                    return True
                
                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.refill_rate
                
                logger.debug(f"Rate limit reached. Waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    async def check_availability(self) -> tuple[bool, float]:
        """
        Check if tokens are available without blocking.
        
        Returns:
            Tuple of (available: bool, wait_time: float)
        """
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            current_tokens = min(
                self.burst,
                self.tokens + (time_passed * self.refill_rate)
            )
            
            if current_tokens >= 1:
                return True, 0.0
            else:
                tokens_needed = 1 - current_tokens
                wait_time = tokens_needed / self.refill_rate
                return False, wait_time
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        now = time.time()
        recent_requests = sum(1 for t in self.request_times if now - t < 60)
        
        return {
            'current_tokens': self.tokens,
            'max_tokens': self.burst,
            'requests_last_minute': recent_requests,
            'rate_limit': self.rate,
            'utilization_pct': (recent_requests / self.rate) * 100
        }
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        await self.acquire(1)


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts to API response headers.
    Monitors X-RateLimit headers and adjusts accordingly.
    """
    
    def __init__(self, rate: int = 100, burst: int = 20):
        super().__init__(rate, burst)
        self.server_limit: Optional[int] = None
        self.server_remaining: Optional[int] = None
        self.server_reset: Optional[float] = None
    
    def update_from_headers(self, headers: dict):
        """
        Update rate limits based on API response headers.
        
        Args:
            headers: Response headers from API
        """
        try:
            if 'X-RateLimit-Limit' in headers:
                self.server_limit = int(headers['X-RateLimit-Limit'])
            
            if 'X-RateLimit-Remaining' in headers:
                self.server_remaining = int(headers['X-RateLimit-Remaining'])
            
            if 'X-RateLimit-Reset' in headers:
                self.server_reset = float(headers['X-RateLimit-Reset'])
            
            # Log if we're close to limit
            if self.server_remaining is not None and self.server_remaining < 10:
                logger.warning(
                    f"Rate limit warning: {self.server_remaining} requests remaining"
                )
        except (ValueError, KeyError) as e:
            logger.debug(f"Could not parse rate limit headers: {e}")
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire with server-side rate limit awareness."""
        # If we know server limits, check them first
        if self.server_remaining is not None and self.server_remaining < 1:
            if self.server_reset:
                wait_time = max(0, self.server_reset - time.time())
                logger.warning(f"Server rate limit reached. Waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        return await super().acquire(tokens)
