"""
Logging Middleware
Request/response logging for API monitoring and debugging
"""

import time
import logging
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for API requests and responses."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.skip_paths = {
            "/health",
            "/health/basic",
            "/",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response details."""
        start_time = time.time()
        
        # Skip logging for health checks and static files
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Log request
        logger.info(
            f"🔍 {request.method} {request.url.path} - "
            f"Client: {request.client.host} - "
            f"User-Agent: {request.headers.get('user-agent', 'Unknown')[:50]}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logger.info(
                f"{status_emoji} {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Add response time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"💥 {request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            raise