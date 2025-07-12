"""
Conversational AI Engine for Grime Guardians Executive Bots
Reusable template framework for role-specific conversational AI
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import openai
import structlog

from ..config import settings

logger = structlog.get_logger()


@dataclass
class ConversationMessage:
    """Single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    """Conversation context and memory."""
    user_id: str
    conversation_id: str
    messages: List[ConversationMessage]
    persona_type: str
    last_activity: datetime
    context_data: Dict[str, Any]


class ConversationEngine:
    """
    Reusable conversational AI engine that can be specialized for different roles.
    
    This provides the core conversation management, memory, and OpenAI integration
    while allowing role-specific customization through persona configurations.
    """
    
    def __init__(self, persona_config: Dict[str, Any]):
        self.persona_config = persona_config
        self.conversations: Dict[str, ConversationContext] = {}
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Conversation memory settings
        self.max_messages = persona_config.get('max_messages', 20)
        self.context_timeout = persona_config.get('context_timeout_hours', 24)
        
        # Concise response enforcement
        self.enforce_concise = persona_config.get('enforce_concise', True)
        
    def get_conversation_id(self, user_id: str, channel_id: str = None) -> str:
        """Generate conversation ID for user/channel combination."""
        if channel_id:
            return f"{user_id}_{channel_id}"
        return f"{user_id}_dm"
    
    def get_or_create_conversation(self, user_id: str, channel_id: str = None) -> ConversationContext:
        """Get existing conversation or create new one."""
        conv_id = self.get_conversation_id(user_id, channel_id)
        
        if conv_id in self.conversations:
            conv = self.conversations[conv_id]
            # Check if conversation has expired
            if datetime.utcnow() - conv.last_activity > timedelta(hours=self.context_timeout):
                logger.info(f"Conversation expired, creating new one: {conv_id}")
                del self.conversations[conv_id]
            else:
                return conv
        
        # Create new conversation
        conversation = ConversationContext(
            user_id=user_id,
            conversation_id=conv_id,
            messages=[],
            persona_type=self.persona_config['name'],
            last_activity=datetime.utcnow(),
            context_data={}
        )
        
        self.conversations[conv_id] = conversation
        logger.info(f"Created new conversation: {conv_id}")
        return conversation
    
    def add_message(self, conversation: ConversationContext, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add message to conversation history."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        conversation.messages.append(message)
        conversation.last_activity = datetime.utcnow()
        
        # Trim conversation if too long
        if len(conversation.messages) > self.max_messages:
            # Keep system message and recent messages
            system_messages = [msg for msg in conversation.messages if msg.role == 'system']
            recent_messages = conversation.messages[-(self.max_messages - len(system_messages)):]
            conversation.messages = system_messages + recent_messages
    
    def build_system_prompt(self, conversation: ConversationContext) -> str:
        """Build system prompt with persona and context."""
        base_prompt = self.persona_config['system_prompt']
        
        # Add business context
        business_context = self.get_business_context(conversation)
        if business_context:
            base_prompt += f"\n\nCurrent Business Context:\n{business_context}"
        
        # Add conversation context
        if conversation.context_data:
            context_summary = self.summarize_context_data(conversation.context_data)
            base_prompt += f"\n\nRelevant Context:\n{context_summary}"
        
        return base_prompt
    
    def get_business_context(self, conversation: ConversationContext) -> str:
        """Get current business context relevant to this persona."""
        # This will be overridden by specific persona implementations
        return ""
    
    def summarize_context_data(self, context_data: Dict[str, Any]) -> str:
        """Summarize context data for prompt injection."""
        if not context_data:
            return ""
        
        summary_parts = []
        for key, value in context_data.items():
            if isinstance(value, dict):
                summary_parts.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                summary_parts.append(f"{key}: {value}")
        
        return "\n".join(summary_parts)
    
    def build_messages_for_openai(self, conversation: ConversationContext) -> List[Dict[str, str]]:
        """Build message list for OpenAI API."""
        messages = []
        
        # Add system prompt
        system_prompt = self.build_system_prompt(conversation)
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history (skip system messages from history)
        for msg in conversation.messages:
            if msg.role != 'system':
                messages.append({"role": msg.role, "content": msg.content})
        
        return messages
    
    async def generate_response(self, conversation: ConversationContext, user_message: str) -> str:
        """Generate AI response using OpenAI."""
        try:
            # Add user message to conversation
            self.add_message(conversation, "user", user_message)
            
            # Build messages for OpenAI
            messages = self.build_messages_for_openai(conversation)
            
            # Log the conversation for debugging
            logger.info(f"Generating response for {conversation.conversation_id}")
            logger.debug(f"Messages sent to OpenAI: {len(messages)} messages")
            
            # Call OpenAI
            response = await self.openai_client.chat.completions.create(
                model=self.persona_config.get('model', 'gpt-4-turbo-preview'),
                messages=messages,
                max_tokens=self.persona_config.get('max_tokens', 500),
                temperature=self.persona_config.get('temperature', 0.7),
            )
            
            assistant_response = response.choices[0].message.content
            
            # Enforce concise responses if enabled
            if self.enforce_concise:
                assistant_response = self._enforce_concise_response(assistant_response)
            
            # Add assistant response to conversation
            self.add_message(conversation, "assistant", assistant_response)
            
            logger.info(f"Generated response for {conversation.conversation_id}")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self.persona_config.get('error_message', 
                "I'm experiencing technical difficulties. Please try again in a moment.")
    
    async def handle_conversation(self, user_id: str, user_message: str, channel_id: str = None, 
                                user_context: Dict[str, Any] = None) -> str:
        """Main conversation handler."""
        try:
            # Get or create conversation
            conversation = self.get_or_create_conversation(user_id, channel_id)
            
            # Update context data if provided
            if user_context:
                conversation.context_data.update(user_context)
            
            # Generate and return response
            response = await self.generate_response(conversation, user_message)
            return response
            
        except Exception as e:
            logger.error(f"Error in conversation handler: {e}")
            return "I'm having trouble processing your message right now. Please try again."
    
    def clear_conversation(self, user_id: str, channel_id: str = None):
        """Clear conversation history for user."""
        conv_id = self.get_conversation_id(user_id, channel_id)
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            logger.info(f"Cleared conversation: {conv_id}")
    
    def get_conversation_summary(self, user_id: str, channel_id: str = None) -> Optional[Dict[str, Any]]:
        """Get conversation summary for user."""
        conv_id = self.get_conversation_id(user_id, channel_id)
        if conv_id not in self.conversations:
            return None
        
        conversation = self.conversations[conv_id]
        return {
            'conversation_id': conv_id,
            'message_count': len(conversation.messages),
            'last_activity': conversation.last_activity.isoformat(),
            'persona_type': conversation.persona_type
        }
    
    def _enforce_concise_response(self, response: str) -> str:
        """Enforce concise response limits."""
        # Split into sentences
        sentences = response.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Limit to 2 sentences maximum
        if len(sentences) > 2:
            response = '. '.join(sentences[:2]) + '.'
            logger.debug(f"Truncated response from {len(sentences)} to 2 sentences")
        
        return response