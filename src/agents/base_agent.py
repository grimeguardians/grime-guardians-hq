import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from openai import AsyncOpenAI
from ..models.schemas import AgentMessage, AgentResponse, AgentType, MessagePriority
from ..config import settings
import structlog

logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Abstract base class for all Grime Guardians agents.
    
    Implements 12-Factor Agent methodology:
    - Stateless reducer pattern
    - Structured outputs via Pydantic
    - Natural language to tool calls
    - Own your prompts and context
    """
    
    def __init__(self, agent_id: AgentType, description: str):
        self.agent_id = agent_id
        self.description = description
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.message_queue = asyncio.Queue()
        self.is_running = False
        self.message_handlers: Dict[str, Callable] = {}
        
        # Performance tracking
        self.messages_processed = 0
        self.errors_encountered = 0
        self.last_activity = datetime.utcnow()
        
        logger.info(f"Initialized agent {self.agent_id}: {self.description}")
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """
        System prompt defining the agent's role and capabilities.
        Each agent must define its own specialized prompt.
        """
        pass
    
    @property
    @abstractmethod
    def available_tools(self) -> List[Dict[str, Any]]:
        """
        List of tools/functions available to this agent.
        Returns OpenAI function calling format.
        """
        pass
    
    async def start(self):
        """Start the agent's message processing loop."""
        if self.is_running:
            logger.warning(f"Agent {self.agent_id} is already running")
            return
            
        self.is_running = True
        logger.info(f"Starting agent {self.agent_id}")
        
        # Start message processing task
        asyncio.create_task(self._message_processing_loop())
    
    async def stop(self):
        """Stop the agent gracefully."""
        self.is_running = False
        logger.info(f"Stopping agent {self.agent_id}")
    
    async def send_message(self, message: AgentMessage) -> str:
        """
        Send a message to this agent for processing.
        
        Args:
            message: AgentMessage to process
            
        Returns:
            correlation_id for tracking the message
        """
        correlation_id = str(uuid.uuid4())
        message.correlation_id = correlation_id
        message.timestamp = datetime.utcnow()
        
        await self.message_queue.put(message)
        logger.info(
            f"Message queued for {self.agent_id}",
            message_type=message.message_type,
            priority=message.priority.value,
            correlation_id=correlation_id
        )
        
        return correlation_id
    
    async def _message_processing_loop(self):
        """Main message processing loop."""
        while self.is_running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=settings.agent_timeout_seconds
                )
                
                # Process the message
                response = await self._process_message(message)
                
                # Update metrics
                self.messages_processed += 1
                self.last_activity = datetime.utcnow()
                
                # Handle response routing if needed
                if message.requires_response:
                    await self._handle_response(response)
                    
            except asyncio.TimeoutError:
                # No messages to process, continue loop
                continue
            except Exception as e:
                self.errors_encountered += 1
                logger.error(
                    f"Error in {self.agent_id} message processing",
                    error=str(e),
                    agent_id=self.agent_id
                )
                await asyncio.sleep(1)  # Brief pause before continuing
    
    async def _process_message(self, message: AgentMessage) -> AgentResponse:
        """
        Process a single message using OpenAI GPT-4.
        
        Args:
            message: AgentMessage to process
            
        Returns:
            AgentResponse with the agent's response
        """
        try:
            logger.info(
                f"Processing message in {self.agent_id}",
                message_type=message.message_type,
                correlation_id=message.correlation_id
            )
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self._format_user_message(message)}
            ]
            
            # Add context if available
            context = await self._get_context(message)
            if context:
                messages.insert(1, {"role": "system", "content": context})
            
            # Call OpenAI with function calling
            completion = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=self.available_tools if self.available_tools else None,
                tool_choice="auto" if self.available_tools else None,
                max_tokens=settings.openai_max_tokens,
                temperature=0.1  # Low temperature for consistency
            )
            
            # Process the response
            return await self._handle_completion(completion, message)
            
        except Exception as e:
            logger.error(
                f"Error processing message in {self.agent_id}",
                error=str(e),
                correlation_id=message.correlation_id
            )
            
            return AgentResponse(
                agent_id=self.agent_id,
                response_to=message.correlation_id or "unknown",
                content=f"Error processing message: {str(e)}",
                success=False,
                error_message=str(e)
            )
    
    def _format_user_message(self, message: AgentMessage) -> str:
        """
        Format the user message with metadata for better context.
        
        Args:
            message: AgentMessage to format
            
        Returns:
            Formatted message string
        """
        formatted = f"Message Type: {message.message_type}\n"
        formatted += f"Priority: {message.priority.value}\n"
        formatted += f"Content: {message.content}\n"
        
        if message.metadata:
            formatted += f"Additional Context: {json.dumps(message.metadata, indent=2)}\n"
            
        return formatted
    
    async def _get_context(self, message: AgentMessage) -> Optional[str]:
        """
        Get additional context for message processing.
        Override in subclasses for agent-specific context.
        
        Args:
            message: AgentMessage being processed
            
        Returns:
            Additional context string or None
        """
        return None
    
    async def _handle_completion(self, completion, message: AgentMessage) -> AgentResponse:
        """
        Handle OpenAI completion response.
        
        Args:
            completion: OpenAI completion response
            message: Original message
            
        Returns:
            AgentResponse
        """
        response_message = completion.choices[0].message
        actions_taken = []
        next_actions = []
        
        # Handle tool calls if present
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                try:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool function
                    result = await self._execute_tool(function_name, function_args)
                    actions_taken.append(f"Executed {function_name}: {result}")
                    
                except Exception as e:
                    logger.error(
                        f"Error executing tool {tool_call.function.name}",
                        error=str(e),
                        agent_id=self.agent_id
                    )
                    actions_taken.append(f"Failed to execute {tool_call.function.name}: {str(e)}")
        
        # Extract next actions from response if mentioned
        content = response_message.content or ""
        if "Next actions:" in content:
            next_actions_text = content.split("Next actions:")[1].strip()
            next_actions = [action.strip() for action in next_actions_text.split("\n") if action.strip()]
        
        return AgentResponse(
            agent_id=self.agent_id,
            response_to=message.correlation_id or "unknown",
            content=content,
            success=True,
            actions_taken=actions_taken,
            next_actions=next_actions,
            metadata={"tool_calls_count": len(response_message.tool_calls or [])}
        )
    
    async def _execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> str:
        """
        Execute a tool function.
        
        Args:
            function_name: Name of the function to execute
            function_args: Arguments for the function
            
        Returns:
            Result of the function execution
        """
        if function_name in self.message_handlers:
            return await self.message_handlers[function_name](**function_args)
        else:
            raise ValueError(f"Unknown tool function: {function_name}")
    
    async def _handle_response(self, response: AgentResponse):
        """
        Handle response routing to other agents or systems.
        Override in subclasses for specific routing logic.
        
        Args:
            response: AgentResponse to route
        """
        logger.info(
            f"Response from {self.agent_id}",
            response_to=response.response_to,
            success=response.success
        )
    
    def register_tool_handler(self, function_name: str, handler: Callable):
        """
        Register a handler for a specific tool function.
        
        Args:
            function_name: Name of the function
            handler: Async callable to handle the function
        """
        self.message_handlers[function_name] = handler
        logger.info(f"Registered tool handler {function_name} for {self.agent_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the agent.
        
        Returns:
            Status dictionary
        """
        return {
            "agent_id": self.agent_id.value,
            "description": self.description,
            "is_running": self.is_running,
            "messages_processed": self.messages_processed,
            "errors_encountered": self.errors_encountered,
            "last_activity": self.last_activity.isoformat(),
            "queue_size": self.message_queue.qsize()
        }
    
    async def health_check(self) -> bool:
        """
        Perform health check on the agent.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple test message to verify OpenAI connectivity
            test_message = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a health check assistant."},
                    {"role": "user", "content": "Respond with 'OK' if you can process this message."}
                ],
                max_tokens=10
            )
            
            response_content = test_message.choices[0].message.content
            return "OK" in response_content if response_content else False
            
        except Exception as e:
            logger.error(f"Health check failed for {self.agent_id}", error=str(e))
            return False