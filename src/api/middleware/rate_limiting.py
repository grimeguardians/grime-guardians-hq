"""
Rate Limiting Middleware
Protects API from abuse and ensures fair usage
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from ...config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, Dict] = defaultdict(lambda: {
            "requests": 0,
            "window_start": datetime.utcnow()
        })
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_old_clients())
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        now = datetime.utcnow()
        client_data = self.clients[client_id]
        
        # Reset window if expired
        if now - client_data["window_start"] >= timedelta(seconds=self.window_seconds):
            client_data["requests"] = 0
            client_data["window_start"] = now
        
        # Check if under limit
        if client_data["requests"] < self.max_requests:
            client_data["requests"] += 1
            return True
        
        return False
    
    def get_reset_time(self, client_id: str) -> datetime:
        """Get time when rate limit resets for client."""
        client_data = self.clients[client_id]
        return client_data["window_start"] + timedelta(seconds=self.window_seconds)
    
    async def _cleanup_old_clients(self):
        """Periodically clean up old client data."""
        while True:
            await asyncio.sleep(300)  # Clean up every 5 minutes
            
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_seconds * 2)
            
            clients_to_remove = []
            for client_id, data in self.clients.items():
                if data["window_start"] < cutoff:
                    clients_to_remove.append(client_id)
            
            for client_id in clients_to_remove:
                del self.clients[client_id]


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for API endpoints."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        
        # Different rate limits for different endpoint types
        self.limiters = {
            "default": RateLimiter(
                max_requests=settings.rate_limit_requests,
                window_seconds=settings.rate_limit_window
            ),
            "webhooks": RateLimiter(
                max_requests=1000,  # Higher limit for webhooks
                window_seconds=60
            ),
            "agents": RateLimiter(
                max_requests=50,  # Lower limit for agent operations
                window_seconds=60
            ),
            "analytics": RateLimiter(
                max_requests=20,  # Lower limit for analytics
                window_seconds=60
            )
        }
        
        self.exempt_paths = {
            "/",
            "/health",
            "/health/basic"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""
        
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip rate limiting in test mode
        if settings.test_mode:
            return await call_next(request)
        
        try:
            # Determine client identifier
            client_id = self._get_client_id(request)
            
            # Determine appropriate rate limiter
            limiter = self._get_limiter_for_path(request.url.path)
            
            # Check rate limit
            if not limiter.is_allowed(client_id):
                reset_time = limiter.get_reset_time(client_id)
                
                logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
                
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(int((reset_time - datetime.utcnow()).total_seconds())),
                        "X-RateLimit-Limit": str(limiter.max_requests),
                        "X-RateLimit-Window": str(limiter.window_seconds),
                        "X-RateLimit-Reset": reset_time.isoformat()
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
            response.headers["X-RateLimit-Window"] = str(limiter.window_seconds)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, limiter.max_requests - limiter.clients[client_id]["requests"])
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue with request if rate limiting fails
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Use API key if available
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key_{api_key[:8]}"
        
        # Use JWT subject if available
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return f"jwt_user_{auth_header[7:15]}"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip_{client_ip}"
    
    def _get_limiter_for_path(self, path: str) -> RateLimiter:
        """Get appropriate rate limiter for request path."""
        if "/webhooks/" in path:
            return self.limiters["webhooks"]
        elif "/agents/" in path:
            return self.limiters["agents"]
        elif "/analytics/" in path:
            return self.limiters["analytics"]
        else:
            return self.limiters["default"]