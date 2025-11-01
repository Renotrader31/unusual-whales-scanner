"""API module for Unusual Whales integration"""
from .client import UnusualWhalesClient, APIError, RateLimitError
from .endpoints import UnusualWhalesEndpoints, WebSocketChannels
from .rate_limiter import RateLimiter, AdaptiveRateLimiter, get_rate_limiter

__all__ = [
    'UnusualWhalesClient',
    'APIError',
    'RateLimitError',
    'UnusualWhalesEndpoints',
    'WebSocketChannels',
    'RateLimiter',
    'AdaptiveRateLimiter',
    'get_rate_limiter'
]
