import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any

from ..config import settings
from ..models.schemas import (
    HealthCheck, AgentMessage, AgentResponse, PricingRequest, PricingResponse,
    AgentType, MessagePriority
)
from ..agents import ava, sophia, keith, maya
from ..core import pricing_engine
from ..services.discord_service import discord_service
import structlog

logger = structlog.get_logger()

# Agent registry
agent_registry = {
    AgentType.AVA: ava,
    AgentType.SOPHIA: sophia,
    AgentType.KEITH: keith,
    AgentType.MAYA: maya,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Grime Guardians Agentic Suite")
    
    # Start all agents
    for agent_type, agent in agent_registry.items():
        await agent.start()
        logger.info(f"Started agent {agent_type.value}")
    
    # Register agents with Ava for coordination
    for agent_type, agent in agent_registry.items():
        if agent_type != AgentType.AVA:
            ava.register_agent(agent_type, agent)
    
    # Start Discord service
    try:
        await discord_service.start()
        logger.info("Started Discord service")
    except Exception as e:
        logger.error(f"Failed to start Discord service: {e}")
        # Continue without Discord if it fails
    
    yield
    
    # Shutdown
    logger.info("Shutting down Grime Guardians Agentic Suite")
    
    # Stop Discord service
    try:
        await discord_service.stop()
        logger.info("Stopped Discord service")
    except Exception as e:
        logger.error(f"Error stopping Discord service: {e}")
    
    # Stop all agents
    for agent_type, agent in agent_registry.items():
        await agent.stop()
        logger.info(f"Stopped agent {agent_type.value}")


# Create FastAPI application
app = FastAPI(
    title="Grime Guardians Agentic Suite",
    description="8-Agent system for premium cleaning service automation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with system information."""
    return {
        "service": "Grime Guardians Agentic Suite",
        "version": "1.0.0",
        "status": "operational",
        "agents": list(agent_registry.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Comprehensive health check."""
    try:
        # Check agent status
        agents_status = {}
        for agent_type, agent in agent_registry.items():
            try:
                is_healthy = await agent.health_check()
                agents_status[agent_type.value] = "healthy" if is_healthy else "unhealthy"
            except Exception as e:
                agents_status[agent_type.value] = f"error: {str(e)}"
        
        # Check integrations
        integrations_status = {
            "openai": "connected",
            "discord": "connected" if discord_service.is_running() else "disconnected",
            "notion": "connected",
            "gohighlevel": "connected"
        }
        
        return HealthCheck(
            status="healthy",
            agents_status=agents_status,
            integrations_status=integrations_status,
            database_status="connected",
            uptime_seconds=0  # Calculate actual uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/pricing/calculate", response_model=PricingResponse)
async def calculate_pricing(request: PricingRequest):
    """Calculate pricing for cleaning services."""
    try:
        logger.info("Pricing calculation requested", service_type=request.service_type.value)
        
        # Validate request
        pricing_engine.validate_pricing_request(request)
        
        # Calculate pricing
        quote = pricing_engine.calculate_service_price(
            request.service_type,
            request.rooms,
            request.full_baths,
            request.half_baths,
            request.square_footage,
            request.add_ons,
            request.modifiers
        )
        
        return quote
        
    except Exception as e:
        logger.error(f"Pricing calculation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/agents/{agent_id}/message", response_model=Dict[str, Any])
async def send_agent_message(agent_id: str, message: AgentMessage, background_tasks: BackgroundTasks):
    """Send message to specific agent."""
    try:
        # Validate agent ID
        agent_type = AgentType(agent_id)
        if agent_type not in agent_registry:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent = agent_registry[agent_type]
        
        # Send message to agent
        correlation_id = await agent.send_message(message)
        
        logger.info(
            f"Message sent to {agent_id}",
            correlation_id=correlation_id,
            message_type=message.message_type
        )
        
        return {
            "status": "queued",
            "agent_id": agent_id,
            "correlation_id": correlation_id,
            "message_type": message.message_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent ID: {agent_id}")
    except Exception as e:
        logger.error(f"Error sending message to {agent_id}", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get status of specific agent."""
    try:
        agent_type = AgentType(agent_id)
        if agent_type not in agent_registry:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        agent = agent_registry[agent_type]
        status = agent.get_status()
        
        return status
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent ID: {agent_id}")
    except Exception as e:
        logger.error(f"Error getting agent status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/status")
async def get_all_agents_status():
    """Get status of all agents."""
    try:
        agents_status = {}
        for agent_type, agent in agent_registry.items():
            agents_status[agent_type.value] = agent.get_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": agents_status
        }
        
    except Exception as e:
        logger.error(f"Error getting agents status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/discord")
async def discord_webhook(payload: Dict[str, Any]):
    """Handle Discord webhook events."""
    try:
        logger.info("Discord webhook received", payload_type=payload.get("type"))
        
        # Route Discord events to appropriate agents
        if "checkin" in payload.get("content", "").lower():
            # Route to Keith for check-in processing
            message = AgentMessage(
                agent_id=AgentType.KEITH,
                message_type="discord_checkin",
                content=payload.get("content", ""),
                priority=MessagePriority.HIGH,
                metadata=payload
            )
            await keith.send_message(message)
        
        elif "booking" in payload.get("content", "").lower():
            # Route to Sophia for booking inquiries
            message = AgentMessage(
                agent_id=AgentType.SOPHIA,
                message_type="discord_inquiry",
                content=payload.get("content", ""),
                priority=MessagePriority.MEDIUM,
                metadata=payload
            )
            await sophia.send_message(message)
        
        else:
            # Route to Ava for general coordination
            message = AgentMessage(
                agent_id=AgentType.AVA,
                message_type="discord_general",
                content=payload.get("content", ""),
                priority=MessagePriority.MEDIUM,
                metadata=payload
            )
            await ava.send_message(message)
        
        return {"status": "processed", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Discord webhook error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/gohighlevel")
async def gohighlevel_webhook(payload: Dict[str, Any]):
    """Handle GoHighLevel webhook events."""
    try:
        logger.info("GoHighLevel webhook received", event_type=payload.get("type"))
        
        # Route GHL events to Sophia for booking management
        message = AgentMessage(
            agent_id=AgentType.SOPHIA,
            message_type="ghl_event",
            content=f"GoHighLevel event: {payload.get('type', 'unknown')}",
            priority=MessagePriority.MEDIUM,
            metadata=payload
        )
        await sophia.send_message(message)
        
        return {"status": "processed", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"GoHighLevel webhook error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/discord/status")
async def discord_status():
    """Get Discord service status."""
    return {
        "running": discord_service.is_running(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/discord/message")
async def send_discord_message(payload: Dict[str, Any]):
    """Send message through Discord bot."""
    try:
        channel_id = payload.get("channel_id")
        content = payload.get("content")
        embed = payload.get("embed")
        
        if not channel_id:
            raise HTTPException(status_code=400, detail="channel_id is required")
        
        success = await discord_service.send_message(channel_id, content, embed)
        
        return {
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Discord message error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/discord/notify/checkin")
async def notify_checkin_required(payload: Dict[str, Any]):
    """Notify contractor that check-in is required."""
    try:
        contractor_name = payload.get("contractor_name")
        job_details = payload.get("job_details", {})
        
        if not contractor_name:
            raise HTTPException(status_code=400, detail="contractor_name is required")
        
        success = await discord_service.notify_checkin_required(contractor_name, job_details)
        
        return {
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Discord check-in notification error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )