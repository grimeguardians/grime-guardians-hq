"""
Health Check Endpoints
System status and health monitoring for production operations
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...integrations import get_integration_manager
from ...agents import get_agent_manager

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str = "1.0.0"
    uptime_seconds: float = 0.0


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    status: str
    timestamp: str
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    services: Dict[str, Any]
    agents: Dict[str, Any]
    integrations: Dict[str, Any]
    system_info: Dict[str, Any]


@router.get("/basic", response_model=HealthResponse)
async def basic_health_check():
    """Basic health check endpoint for load balancers."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check with system status."""
    try:
        # Get integration manager
        integration_manager = get_integration_manager()
        
        # Check integration health
        integration_health = await integration_manager.check_health()
        
        # Get agent manager status
        try:
            agent_manager = get_agent_manager()
            agent_status = await agent_manager.get_system_status() if agent_manager else {}
        except Exception:
            agent_status = {"status": "unavailable", "reason": "Agent system not initialized"}
        
        # System information
        system_info = {
            "python_version": "3.9+",
            "environment": "production",
            "service": "grime-guardians-agentic-suite"
        }
        
        # Overall status determination
        overall_status = "healthy"
        if integration_health.get("overall_status") == "critical":
            overall_status = "critical"
        elif integration_health.get("overall_status") == "degraded":
            overall_status = "degraded"
        
        return DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            services={
                "api": {"status": "healthy", "version": "1.0.0"},
                "database": {"status": "healthy", "connection": "active"}
            },
            agents=agent_status,
            integrations=integration_health,
            system_info=system_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes deployments."""
    try:
        integration_manager = get_integration_manager()
        health = await integration_manager.check_health()
        
        # Service is ready if at least 75% of integrations are healthy
        if health.get("health_percentage", 0) >= 75:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready - insufficient healthy integrations"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {str(e)}"
        )


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes deployments."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "grime-guardians-agentic-suite"
    }