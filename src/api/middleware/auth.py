"""
Authentication Middleware
JWT token validation and API key authentication
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from ...config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API requests."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.exempt_paths = {
            "/",
            "/health",
            "/health/basic",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/webhooks/gohighlevel",  # Webhooks need special handling
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process authentication for each request."""
        
        # Skip authentication for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip authentication in test mode
        if settings.test_mode:
            return await call_next(request)
        
        try:
            # Check for API key in headers
            api_key = request.headers.get("X-API-Key")
            if api_key:
                if self._validate_api_key(api_key):
                    request.state.auth_type = "api_key"
                    request.state.authenticated = True
                    return await call_next(request)
            
            # Check for JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                if self._validate_jwt_token(token):
                    request.state.auth_type = "jwt"
                    request.state.authenticated = True
                    return await call_next(request)
            
            # No valid authentication found
            logger.warning(f"Unauthorized access attempt: {request.url.path} from {request.client.host}")
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=500, detail="Authentication service error")
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        # In production, this would check against a database
        # For now, use a simple check against the secret key
        expected_key = f"gg_{settings.secret_key[:16]}"
        return api_key == expected_key
    
    def _validate_jwt_token(self, token: str) -> bool:
        """Validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"]
            )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                return False
            
            # Check issuer
            iss = payload.get("iss")
            if iss != "grime-guardians-agentic-suite":
                return False
            
            return True
            
        except jwt.InvalidTokenError:
            return False
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return False


def create_jwt_token(user_id: str, expires_in_hours: int = 24) -> str:
    """Create JWT token for user."""
    payload = {
        "user_id": user_id,
        "iss": "grime-guardians-agentic-suite",
        "iat": datetime.utcnow().timestamp(),
        "exp": (datetime.utcnow().timestamp() + (expires_in_hours * 3600))
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_api_key() -> str:
    """Get the API key for client use."""
    return f"gg_{settings.secret_key[:16]}"