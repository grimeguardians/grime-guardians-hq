"""
Agent Management Endpoints
API routes for managing and interacting with COO operational agents
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ...agents import get_agent_manager
from ...agents.models import MessageContext, AgentResponse

router = APIRouter()


class AgentStatusResponse(BaseModel):
    """Agent status response model."""
    agent_name: str
    status: str
    last_activity: str
    message_count: int = 0
    success_rate: float = 0.0


class SystemStatusResponse(BaseModel):
    """System-wide agent status response."""
    status: str
    timestamp: str
    active_agents: int
    total_agents: int
    agents: List[AgentStatusResponse]


class MessageRequest(BaseModel):
    """Message request for agent processing."""
    content: str = Field(..., description="Message content to process")
    sender_phone: Optional[str] = Field(None, description="Sender phone number")
    sender_name: Optional[str] = Field(None, description="Sender name")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class AgentMessageResponse(BaseModel):
    """Agent message processing response."""
    agent_name: str
    response: str
    confidence: float
    processing_time: float
    classification: Dict[str, Any]
    timestamp: str


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get overall agent system status."""
    try:
        agent_manager = get_agent_manager()
        if not agent_manager:
            raise HTTPException(
                status_code=503,
                detail="Agent system not initialized"
            )
        
        status = await agent_manager.get_system_status()
        
        # Convert to response format
        agent_statuses = []
        for agent_name, agent_info in status.get("agents", {}).items():
            agent_statuses.append(AgentStatusResponse(
                agent_name=agent_name,
                status=agent_info.get("status", "unknown"),
                last_activity=agent_info.get("last_activity", datetime.utcnow().isoformat()),
                message_count=agent_info.get("message_count", 0),
                success_rate=agent_info.get("success_rate", 0.0)
            ))
        
        return SystemStatusResponse(
            status=status.get("overall_status", "unknown"),
            timestamp=datetime.utcnow().isoformat(),
            active_agents=status.get("active_agents", 0),
            total_agents=status.get("total_agents", 0),
            agents=agent_statuses
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/{agent_name}/status", response_model=AgentStatusResponse)
async def get_agent_status(agent_name: str):
    """Get specific agent status."""
    try:
        agent_manager = get_agent_manager()
        if not agent_manager:
            raise HTTPException(
                status_code=503,
                detail="Agent system not initialized"
            )
        
        agent = agent_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found"
            )
        
        status = await agent.get_status()
        
        return AgentStatusResponse(
            agent_name=agent_name,
            status=status.get("status", "unknown"),
            last_activity=status.get("last_activity", datetime.utcnow().isoformat()),
            message_count=status.get("message_count", 0),
            success_rate=status.get("success_rate", 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/process", response_model=AgentMessageResponse)
async def process_message(
    message_request: MessageRequest,
    background_tasks: BackgroundTasks
):
    """Process message through agent system."""
    try:
        agent_manager = get_agent_manager()
        if not agent_manager:
            raise HTTPException(
                status_code=503,
                detail="Agent system not initialized"
            )
        
        # Create message context
        context = MessageContext(
            content=message_request.content,
            sender_phone=message_request.sender_phone,
            sender_name=message_request.sender_name,
            **message_request.context
        )
        
        start_time = datetime.utcnow()
        
        # Process message through orchestrator
        response = await agent_manager.process_message(context)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AgentMessageResponse(
            agent_name=response.agent_name,
            response=response.response,
            confidence=response.confidence,
            processing_time=processing_time,
            classification=response.metadata.get("classification", {}),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/{agent_name}/message", response_model=AgentMessageResponse)
async def send_message_to_agent(
    agent_name: str,
    message_request: MessageRequest,
    background_tasks: BackgroundTasks
):
    """Send message directly to specific agent."""
    try:
        agent_manager = get_agent_manager()
        if not agent_manager:
            raise HTTPException(
                status_code=503,
                detail="Agent system not initialized"
            )
        
        agent = agent_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found"
            )
        
        # Create message context
        context = MessageContext(
            content=message_request.content,
            sender_phone=message_request.sender_phone,
            sender_name=message_request.sender_name,
            **message_request.context
        )
        
        start_time = datetime.utcnow()
        
        # Send message directly to agent
        response = await agent.process_message(context)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AgentMessageResponse(
            agent_name=agent_name,
            response=response.response,
            confidence=response.confidence,
            processing_time=processing_time,
            classification=response.metadata.get("classification", {}),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message to agent: {str(e)}"
        )


@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all available agents."""
    try:
        agent_manager = get_agent_manager()
        if not agent_manager:
            raise HTTPException(
                status_code=503,
                detail="Agent system not initialized"
            )
        
        agents = []
        for agent_name in agent_manager.get_agent_names():
            agent = agent_manager.get_agent(agent_name)
            if agent:
                agents.append({
                    "name": agent_name,
                    "description": getattr(agent, "description", "COO operational agent"),
                    "capabilities": getattr(agent, "capabilities", []),
                    "specialization": getattr(agent, "specialization", "operations")
                })
        
        return agents
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agents: {str(e)}"
        )