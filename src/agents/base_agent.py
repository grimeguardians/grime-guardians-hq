"""
Base Agent Framework following 12-factor methodology
Abstract base class for all Grime Guardians agents
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json

from openai import AsyncOpenAI
from pydantic import BaseModel

from ..models.schemas import AgentMessageSchema, AgentResponse, BusinessContext
from ..models.types import MessageType, AgentStatus
from ..core.message_classifier import MessageClassifier
from ..config.settings import get_settings, AGENT_CONFIG

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentTool(BaseModel):
    """Schema for agent tools following structured output pattern."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = []


class AgentState(BaseModel):
    """Agent state following stateless reducer pattern."""
    agent_id: str
    status: AgentStatus
    last_activity: datetime
    message_queue_size: int
    error_count: int
    success_count: int
    current_task: Optional[str] = None
    context: Dict[str, Any] = {}


class BaseAgent(ABC):
    """
    Abstract base class for all agents following 12-factor methodology.
    
    Key Principles:
    - Stateless reducer pattern
    - Structured tool outputs
    - Own your prompts
    - Natural language to tool calls
    """
    
    def __init__(self, agent_id: str, business_context: Optional[BusinessContext] = None):
        self.agent_id = agent_id
        self.config = AGENT_CONFIG[agent_id]
        self.status = AgentStatus.ACTIVE
        
        # AI client
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        
        # Message handling
        self.message_queue = asyncio.Queue()
        self.message_classifier = MessageClassifier()
        
        # Business context
        self.business_context = business_context
        
        # Performance tracking
        self.error_count = 0
        self.success_count = 0
        self.last_activity = datetime.utcnow()
        
        # Tool registry
        self.tools = self._register_tools()
        
        logger.info(f"Agent {self.agent_id} initialized: {self.config['name']}")
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Agent-specific system prompt. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _register_tools(self) -> List[AgentTool]:
        """Register agent-specific tools. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _handle_message_type(
        self, 
        message_type: MessageType, 
        content: str, 
        extracted_data: Dict[str, Any]
    ) -> AgentResponse:
        """Handle specific message types. Must be implemented by subclasses."""
        pass
    
    async def process_message(self, message: AgentMessageSchema) -> AgentResponse:
        """
        Process incoming message following 12-factor patterns.
        Main entry point for agent message processing.
        """
        start_time = datetime.utcnow()
        
        try:
            # Update activity
            self.last_activity = datetime.utcnow()
            self.status = AgentStatus.PROCESSING
            
            # Classify message if not already classified
            if hasattr(message, 'classification'):
                message_type, confidence, extracted_data = message.classification
            else:
                message_type, confidence, extracted_data = await self.message_classifier.classify_message(
                    content=message.content,
                    sender_info={"agent_id": message.agent_id},
                    context={"priority": message.priority}
                )
            
            # Check if confidence meets threshold
            if confidence < settings.target_classification_accuracy:
                logger.warning(f"Low confidence classification: {confidence:.2f} for {message.content[:50]}...")
                # Could escalate to human review here
            
            # Handle message based on type and agent specialization
            if self._should_handle_message_type(message_type):
                response = await self._handle_message_type(message_type, message.content, extracted_data)
            else:
                # Route to appropriate agent
                response = await self._route_to_specialist(message, message_type, extracted_data)
            
            # Update success metrics
            self.success_count += 1
            self.status = AgentStatus.ACTIVE
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            response.processing_time = processing_time
            
            logger.info(f"Agent {self.agent_id} processed message: {message_type.value} in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.error_count += 1
            self.status = AgentStatus.ERROR
            
            logger.error(f"Agent {self.agent_id} error processing message: {e}")
            
            return AgentResponse(
                agent_id=self.agent_id,
                status="error",
                response=f"Error processing message: {str(e)}",
                requires_escalation=True,
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _route_to_specialist(
        self, 
        message: AgentMessageSchema, 
        message_type: MessageType, 
        extracted_data: Dict[str, Any]
    ) -> AgentResponse:
        """Route message to specialist agent if this agent shouldn't handle it."""
        
        # Agent routing logic based on message type
        routing_map = {
            MessageType.JOB_ASSIGNMENT: "sophia",  # Booking coordinator
            MessageType.STATUS_UPDATE: "keith",   # Check-in tracker
            MessageType.QUALITY_VIOLATION: "dmitri",  # Escalation agent
            MessageType.PERFORMANCE_FEEDBACK: "maya",  # Coaching agent
            MessageType.ESCALATION: "dmitri",     # Escalation agent
            MessageType.COMPLIANCE_CHECK: "ava",  # Orchestrator handles compliance
            MessageType.BONUS_CALCULATION: "bruno",  # Bonus tracker
            MessageType.ANALYTICS_REPORT: "aiden"  # Analytics agent
        }
        
        target_agent = routing_map.get(message_type, "ava")  # Default to orchestrator
        
        if target_agent == self.agent_id:
            # This agent should handle it after all
            return await self._handle_message_type(message_type, message.content, extracted_data)
        
        return AgentResponse(
            agent_id=self.agent_id,
            status="routed",
            response=f"Message routed to {target_agent} for {message_type.value} handling",
            actions_taken=[f"route_to_{target_agent}"],
            next_steps=[f"Forward to {target_agent} agent for processing"]
        )
    
    def _should_handle_message_type(self, message_type: MessageType) -> bool:
        """Determine if this agent should handle the message type."""
        # Default implementation - subclasses can override
        return True
    
    async def call_openai(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Call OpenAI with structured output patterns.
        Following 12-factor principle of treating tools as structured outputs.
        """
        try:
            completion_args = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,  # Low temperature for consistent responses
                "max_tokens": 1000,
                "timeout": settings.agent_timeout
            }
            
            if tools:
                completion_args["tools"] = tools
                completion_args["tool_choice"] = "auto"
            
            response = await self.openai_client.chat.completions.create(**completion_args)
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls if tools else None,
                "usage": response.usage.dict() if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error for agent {self.agent_id}: {e}")
            raise
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent tool with parameters."""
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        
        # Get tool handler method
        handler_name = f"_tool_{tool_name}"
        if not hasattr(self, handler_name):
            raise ValueError(f"Tool handler {handler_name} not implemented")
        
        handler = getattr(self, handler_name)
        return await handler(**parameters)
    
    def get_agent_state(self) -> AgentState:
        """Get current agent state following stateless pattern."""
        return AgentState(
            agent_id=self.agent_id,
            status=self.status,
            last_activity=self.last_activity,
            message_queue_size=self.message_queue.qsize(),
            error_count=self.error_count,
            success_count=self.success_count,
            current_task=getattr(self, 'current_task', None),
            context=self._get_context_summary()
        )
    
    def _get_context_summary(self) -> Dict[str, Any]:
        """Get context summary for state management."""
        return {
            "config": self.config,
            "tools_count": len(self.tools),
            "business_context_available": self.business_context is not None,
            "last_error": getattr(self, 'last_error', None)
        }
    
    async def pause(self) -> None:
        """Pause agent following launch/pause/resume pattern."""
        self.status = AgentStatus.PAUSED
        logger.info(f"Agent {self.agent_id} paused")
    
    async def resume(self) -> None:
        """Resume agent following launch/pause/resume pattern."""
        self.status = AgentStatus.ACTIVE
        logger.info(f"Agent {self.agent_id} resumed")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown agent."""
        self.status = AgentStatus.MAINTENANCE
        # Process remaining messages in queue
        while not self.message_queue.empty():
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.process_message(message)
            except asyncio.TimeoutError:
                break
        
        logger.info(f"Agent {self.agent_id} shutdown complete")
    
    def _build_agent_prompt(self, message_content: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """Build agent-specific prompt with business context."""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add business context if available
        if self.business_context:
            context_prompt = f"""
            CURRENT BUSINESS CONTEXT:
            Active Jobs: {len(self.business_context.active_jobs)}
            Active Contractors: {len(self.business_context.contractor_statuses)}
            System Alerts: {len(self.business_context.system_alerts)}
            
            Current KPIs:
            - Jobs Today: {self.business_context.current_kpis.jobs_completed_today}
            - Compliance Rate: {self.business_context.current_kpis.checklist_compliance_rate}%
            - Revenue Today: ${self.business_context.current_kpis.revenue_today}
            """
            messages.append({"role": "system", "content": context_prompt})
        
        # Add current message
        messages.append({"role": "user", "content": message_content})
        
        return messages
    
    def _validate_business_rules(self, action: str, parameters: Dict[str, Any]) -> bool:
        """
        Validate actions against business rules.
        Ensures contractor independence and compliance.
        """
        
        # Contractor independence rules
        if "contractor" in parameters:
            contractor_control_actions = [
                "mandate_schedule", "require_availability", "control_work_method"
            ]
            if action in contractor_control_actions:
                logger.warning(f"Action {action} violates contractor independence")
                return False
        
        # Pricing validation
        if "price" in parameters or "pricing" in action:
            if not self._validate_pricing_rules(parameters):
                return False
        
        # Quality enforcement
        if "violation" in action:
            return self._validate_quality_enforcement(parameters)
        
        return True
    
    def _validate_pricing_rules(self, parameters: Dict[str, Any]) -> bool:
        """Validate pricing against business rules."""
        # Ensure tax is always applied
        if "price" in parameters and "tax_applied" not in parameters:
            logger.warning("Pricing action missing tax application")
            return False
        
        return True
    
    def _validate_quality_enforcement(self, parameters: Dict[str, Any]) -> bool:
        """Validate quality enforcement follows 3-strike system."""
        if "strike_count" in parameters:
            strike_count = parameters["strike_count"]
            if strike_count >= 3 and not parameters.get("human_approval"):
                logger.warning("3rd strike requires human approval")
                return False
        
        return True


class AgentManager:
    """
    Manages multiple agents following 12-factor principles.
    Provides launch/pause/resume functionality.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_states: Dict[str, AgentState] = {}
        
    def register_agent(self, agent: BaseAgent) -> None:
        """Register agent with manager."""
        self.agents[agent.agent_id] = agent
        self.agent_states[agent.agent_id] = agent.get_agent_state()
        logger.info(f"Registered agent: {agent.agent_id}")
    
    async def launch_agent(self, agent_id: str) -> bool:
        """Launch specific agent."""
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        agent = self.agents[agent_id]
        await agent.resume()
        self.agent_states[agent_id] = agent.get_agent_state()
        
        logger.info(f"Launched agent: {agent_id}")
        return True
    
    async def pause_agent(self, agent_id: str) -> bool:
        """Pause specific agent."""
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        agent = self.agents[agent_id]
        await agent.pause()
        self.agent_states[agent_id] = agent.get_agent_state()
        
        logger.info(f"Paused agent: {agent_id}")
        return True
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system-wide agent status."""
        # Update all agent states
        for agent_id, agent in self.agents.items():
            self.agent_states[agent_id] = agent.get_agent_state()
        
        active_count = sum(1 for state in self.agent_states.values() if state.status == AgentStatus.ACTIVE)
        error_count = sum(state.error_count for state in self.agent_states.values())
        success_count = sum(state.success_count for state in self.agent_states.values())
        
        return {
            "total_agents": len(self.agents),
            "active_agents": active_count,
            "total_errors": error_count,
            "total_successes": success_count,
            "success_rate": success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0,
            "agent_states": {agent_id: state.dict() for agent_id, state in self.agent_states.items()}
        }
    
    async def route_message(self, message: AgentMessageSchema) -> AgentResponse:
        """Route message to appropriate agent."""
        # Route to specific agent if specified
        if message.agent_id in self.agents:
            agent = self.agents[message.agent_id]
            return await agent.process_message(message)
        
        # Route to orchestrator by default
        if "ava" in self.agents:
            agent = self.agents["ava"]
            return await agent.process_message(message)
        
        raise ValueError("No suitable agent found for message routing")