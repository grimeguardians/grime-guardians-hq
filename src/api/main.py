"""
Grime Guardians Agentic Suite - FastAPI Application
Main API application with comprehensive endpoints for COO operations
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config.settings import get_settings
from ..integrations import get_integration_manager
from ..agents import get_agent_manager, initialize_agent_system
from .middleware.auth import AuthMiddleware
from .middleware.rate_limiting import RateLimitingMiddleware
from .middleware.logging import LoggingMiddleware
from .routes import (
    agents,
    jobs,
    contractors,
    integrations,
    analytics,
    webhooks,
    health
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Global managers
integration_manager = None
agent_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("🚀 Starting Grime Guardians Agentic Suite...")
    
    global integration_manager, agent_manager
    
    try:
        # Initialize integration manager
        integration_manager = get_integration_manager()
        await integration_manager.initialize_all()
        
        # Initialize agent system
        agent_manager = await initialize_agent_system()
        
        # Store in app state
        app.state.integration_manager = integration_manager
        app.state.agent_manager = agent_manager
        
        logger.info("✅ All systems initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Grime Guardians Agentic Suite...")
    
    try:
        if integration_manager:
            await integration_manager.shutdown_all()
        
        logger.info("✅ Graceful shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="Grime Guardians Agentic Suite",
    description="Comprehensive cleaning operations management with AI agents",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Security
security = HTTPBearer()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.grimeguardians.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.grimeguardians.com"]
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(AuthMiddleware)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with proper logging."""
    logger.error(f"Unhandled exception: {exc} - {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "service": "Grime Guardians Agentic Suite",
        "version": "1.0.0",
        "status": "operational",
        "mission": "We clean like it's our name on the lease",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "agents": "/api/v1/agents",
            "jobs": "/api/v1/jobs",
            "contractors": "/api/v1/contractors",
            "integrations": "/api/v1/integrations",
            "analytics": "/api/v1/analytics",
            "webhooks": "/api/v1/webhooks"
        }
    }

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(contractors.router, prefix="/api/v1/contractors", tags=["Contractors"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

# Dependency providers
async def get_integration_manager():
    """Dependency to get integration manager."""
    return app.state.integration_manager

async def get_agent_manager():
    """Dependency to get agent manager."""
    return app.state.agent_manager

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time agent updates."""
    await websocket.accept()
    
    try:
        while True:
            # In production, this would stream real-time agent status
            # For now, send periodic status updates
            await asyncio.sleep(30)
            
            if app.state.agent_manager:
                status = await app.state.agent_manager.get_system_status()
                await websocket.send_json({
                    "type": "agent_status",
                    "data": status,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Development server
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )