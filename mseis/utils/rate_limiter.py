# utils/rate_limiter.py
import time
import asyncio
from functools import wraps
from typing import Callable, Dict, Optional
from collections import defaultdict, deque

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.buckets: Dict[str, deque] = defaultdict(deque)
        
    def _update_bucket(self, key: str):
        """Update the bucket by removing expired tokens"""
        now = time.time()
        bucket = self.buckets[key]
        
        # Remove expired tokens
        while bucket and bucket[0] <= now - self.period:
            bucket.popleft()
            
    def is_allowed(self, key: str = "default") -> bool:
        """Check if a request is allowed"""
        self._update_bucket(key)
        bucket = self.buckets[key]
        
        if len(bucket) < self.calls:
            bucket.append(time.time())
            return True
        return False
        
    def wait_time(self, key: str = "default") -> float:
        """Get the time to wait before next request"""
        self._update_bucket(key)
        bucket = self.buckets[key]
        
        if len(bucket) < self.calls:
            return 0.0
            
        # Time until the oldest token expires
        return self.period - (time.time() - bucket[0])

def rate_limit(calls: int, period: float, key_func: Callable = None):
    """Rate limiting decorator"""
    limiter = RateLimiter(calls, period)
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Determine rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = "default"
                
            # Check rate limit
            if not limiter.is_allowed(key):
                wait_time = limiter.wait_time(key)
                await asyncio.sleep(wait_time)
                
            return await func(*args, **kwargs)
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar logic for synchronous functions
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = "default"
                
            if not limiter.is_allowed(key):
                wait_time = limiter.wait_time(key)
                time.sleep(wait_time)
                
            return func(*args, **kwargs)
            
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator 