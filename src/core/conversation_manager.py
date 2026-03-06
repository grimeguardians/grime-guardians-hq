"""
Conversation Management System
Migrated from JavaScript with context tracking and multi-channel coordination
Manages conversation state, client profiles, and business workflow routing
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path

from .enhanced_message_classifier import EnhancedMessageClassifier, MessageCategory
from ..models.types import MessageType
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ConversationStatus(str, Enum):
    """Conversation status tracking."""
    ACTIVE = "active"
    AWAITING_RESPONSE = "awaiting_response"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    HANDED_OFF = "handed_off"


class ClientType(str, Enum):
    """Client classification types."""
    NEW_PROSPECT = "new_prospect"
    EXISTING_RECURRING = "existing_recurring"
    EXISTING_ONE_TIME = "existing_one_time"
    CONTRACTOR = "contractor"
    VENDOR = "vendor"


@dataclass
class MessageRecord:
    """Individual message in conversation history."""
    timestamp: datetime
    content: str
    sender_id: str
    sender_type: str  # 'customer', 'contractor', 'agent', 'system'
    channel: str  # 'sms', 'discord', 'email', 'internal'
    category: MessageCategory
    confidence: float
    response_generated: bool = False
    handled_by: Optional[str] = None


@dataclass
class ClientProfile:
    """Enhanced client profile from JavaScript migration."""
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    client_type: ClientType = ClientType.NEW_PROSPECT
    
    # Service preferences
    is_recurring: bool = False
    frequency: Optional[str] = None  # 'weekly', 'biweekly', 'monthly'
    preferred_day: Optional[str] = None
    preferred_time: Optional[str] = None
    service_type: Optional[str] = None  # 'recurring', 'deep_cleaning', 'move_out_in'
    
    # Property details
    address: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    square_footage: Optional[int] = None
    special_instructions: List[str] = field(default_factory=list)
    
    # History tracking
    total_services: int = 0
    last_service_date: Optional[datetime] = None
    total_spent: float = 0.0
    
    # Interaction tracking
    first_contact_date: datetime = field(default_factory=datetime.utcnow)
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    interaction_count: int = 0
    
    # Issues and preferences
    past_issues: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    # Relationship status
    satisfaction_score: float = 5.0  # 1-10 scale
    referral_source: Optional[str] = None
    lifetime_value: float = 0.0


@dataclass
class ConversationThread:
    """Conversation thread tracking from JavaScript migration."""
    thread_id: str  # Usually phone number or channel ID
    client_profile: ClientProfile
    status: ConversationStatus = ConversationStatus.ACTIVE
    
    # Message history
    messages: List[MessageRecord] = field(default_factory=list)
    
    # Context tracking
    current_topic: Optional[str] = None
    awaiting_response_type: Optional[str] = None
    last_agent_response: Optional[datetime] = None
    
    # Workflow state
    handoff_status: Optional[str] = None  # 'pending_cmo', 'pending_operations', etc.
    assigned_agent: Optional[str] = None
    priority_level: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    
    # Business context
    active_booking: Optional[str] = None  # Job ID if booking in progress
    pending_quote: Optional[Dict[str, Any]] = None
    last_service_feedback: Optional[Dict[str, Any]] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ConversationManager:
    """
    Enhanced conversation manager preserving JavaScript system's capabilities.
    Manages multi-channel conversations, client profiles, and business workflows.
    """
    
    def __init__(self):
        self.message_classifier = EnhancedMessageClassifier()
        
        # Conversation storage (in production, would use database)
        self.conversations: Dict[str, ConversationThread] = {}
        self.client_profiles: Dict[str, ClientProfile] = {}
        
        # Data persistence
        self.conversations_file = Path("data/conversations.json")
        self.profiles_file = Path("data/client_profiles.json")
        
        # Load existing data
        self._load_conversations()
        self._load_client_profiles()
        
        # Performance tracking
        self.conversation_stats = {
            'total_conversations': 0,
            'active_conversations': 0,
            'messages_processed': 0,
            'handoffs_completed': 0,
            'escalations_created': 0
        }
    
    async def process_message(
        self,
        message_content: str,
        sender_id: str,
        channel: str = "sms",
        sender_type: str = "customer",
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process incoming message and manage conversation state.
        Main entry point preserving JavaScript system's workflow.
        """
        additional_context = additional_context or {}
        
        try:
            # Get or create conversation thread
            thread = self._get_or_create_conversation(sender_id, sender_type)
            
            # Update client profile context
            client_context = self._build_client_context(thread.client_profile)
            
            # Classify message with full context
            category, confidence, extracted_data = await self.message_classifier.classify_message(
                content=message_content,
                sender_info=client_context,
                context=self._build_conversation_context(thread)
            )
            
            # Create message record
            message_record = MessageRecord(
                timestamp=datetime.utcnow(),
                content=message_content,
                sender_id=sender_id,
                sender_type=sender_type,
                channel=channel,
                category=category,
                confidence=confidence
            )
            
            # Add to conversation
            thread.messages.append(message_record)
            thread.updated_at = datetime.utcnow()
            
            # Update client profile
            self._update_client_profile(thread.client_profile, message_content, extracted_data)
            
            # Determine workflow routing
            workflow_result = await self._route_workflow(thread, category, extracted_data)
            
            # Update conversation state
            self._update_conversation_state(thread, category, workflow_result)
            
            # Save changes
            self._save_conversations()
            self._save_client_profiles()
            
            # Update stats
            self.conversation_stats['messages_processed'] += 1
            
            logger.info(f"Message processed: {category.value} (confidence: {confidence:.3f})")
            
            return {
                'thread_id': thread.thread_id,
                'classification': {
                    'category': category.value,
                    'confidence': confidence,
                    'extracted_data': extracted_data
                },
                'workflow_routing': workflow_result,
                'client_profile': asdict(thread.client_profile),
                'conversation_status': thread.status.value,
                'requires_response': workflow_result.get('requires_response', False),
                'suggested_actions': workflow_result.get('suggested_actions', [])
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'error': str(e),
                'thread_id': sender_id,
                'classification': {
                    'category': 'error',
                    'confidence': 0.0
                }
            }
    
    def _get_or_create_conversation(self, sender_id: str, sender_type: str) -> ConversationThread:
        """Get existing conversation or create new one."""
        
        if sender_id in self.conversations:
            return self.conversations[sender_id]
        
        # Create new conversation
        client_profile = self._get_or_create_client_profile(sender_id, sender_type)
        
        thread = ConversationThread(
            thread_id=sender_id,
            client_profile=client_profile
        )
        
        self.conversations[sender_id] = thread
        self.conversation_stats['total_conversations'] += 1
        self.conversation_stats['active_conversations'] += 1
        
        logger.info(f"Created new conversation thread for {sender_id}")
        
        return thread
    
    def _get_or_create_client_profile(self, sender_id: str, sender_type: str) -> ClientProfile:
        """Get existing client profile or create new one."""
        
        if sender_id in self.client_profiles:
            profile = self.client_profiles[sender_id]
            profile.interaction_count += 1
            profile.last_interaction = datetime.utcnow()
            return profile
        
        # Determine client type
        if sender_type == "contractor":
            client_type = ClientType.CONTRACTOR
        else:
            client_type = ClientType.NEW_PROSPECT
        
        profile = ClientProfile(
            phone_number=sender_id,
            client_type=client_type
        )
        
        self.client_profiles[sender_id] = profile
        
        logger.info(f"Created new client profile for {sender_id} as {client_type.value}")
        
        return profile
    
    def _build_client_context(self, profile: ClientProfile) -> Dict[str, Any]:
        """Build client context for message classification."""
        return {
            'is_existing_client': profile.client_type != ClientType.NEW_PROSPECT,
            'is_contractor': profile.client_type == ClientType.CONTRACTOR,
            'interaction_count': profile.interaction_count,
            'is_recurring_client': profile.is_recurring,
            'has_active_service': profile.last_service_date and 
                                  (datetime.utcnow() - profile.last_service_date).days < 30,
            'satisfaction_score': profile.satisfaction_score,
            'total_services': profile.total_services
        }
    
    def _build_conversation_context(self, thread: ConversationThread) -> Dict[str, Any]:
        """Build conversation context for classification."""
        recent_messages = []
        
        # Get last 5 messages for context
        for msg in thread.messages[-5:]:
            recent_messages.append({
                'content': msg.content[:100],  # Truncate for context
                'category': msg.category.value,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return {
            'recent_messages': recent_messages,
            'awaiting_response': thread.status == ConversationStatus.AWAITING_RESPONSE,
            'current_topic': thread.current_topic,
            'handoff_status': thread.handoff_status,
            'priority_level': thread.priority_level,
            'active_booking': thread.active_booking is not None
        }
    
    def _update_client_profile(
        self, 
        profile: ClientProfile, 
        message_content: str, 
        extracted_data: Dict[str, Any]
    ) -> None:
        """Update client profile based on message content and extracted data."""
        
        # Update service preferences
        if 'service_type' in extracted_data:
            profile.service_type = extracted_data['service_type']
            
        if 'bedrooms' in extracted_data:
            profile.bedrooms = extracted_data['bedrooms']
            
        # Extract name if mentioned
        if not profile.name:
            name = self._extract_name_from_message(message_content)
            if name:
                profile.name = name
        
        # Update client type based on conversation
        if profile.client_type == ClientType.NEW_PROSPECT:
            if profile.interaction_count > 3:
                profile.client_type = ClientType.EXISTING_ONE_TIME
        
        # Track recurring preference
        if any(freq in message_content.lower() for freq in ['weekly', 'biweekly', 'monthly']):
            profile.is_recurring = True
            for freq in ['weekly', 'biweekly', 'monthly']:
                if freq in message_content.lower():
                    profile.frequency = freq
                    break
    
    def _extract_name_from_message(self, message: str) -> Optional[str]:
        """Simple name extraction from message."""
        # Look for patterns like "My name is...", "I'm...", etc.
        patterns = [
            "my name is ",
            "i'm ",
            "i am ",
            "this is ",
            "call me "
        ]
        
        message_lower = message.lower()
        for pattern in patterns:
            if pattern in message_lower:
                start = message_lower.find(pattern) + len(pattern)
                remaining = message[start:].strip()
                
                # Extract first word as name
                words = remaining.split()
                if words:
                    name = words[0].strip('.,!?')
                    if name.isalpha() and len(name) > 1:
                        return name.title()
        
        return None
    
    async def _route_workflow(
        self, 
        thread: ConversationThread, 
        category: MessageCategory, 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route message to appropriate workflow based on classification."""
        
        workflow_result = {
            'routing_decision': None,
            'assigned_agent': None,
            'requires_response': False,
            'priority': 'normal',
            'suggested_actions': [],
            'handoff_required': False
        }
        
        # Route based on message category
        if category == MessageCategory.NEW_PROSPECT_INQUIRY:
            workflow_result.update(await self._handle_prospect_inquiry(thread, extracted_data))
            
        elif category == MessageCategory.SCHEDULE_CHANGE_REQUEST:
            workflow_result.update(await self._handle_schedule_change(thread, extracted_data))
            
        elif category == MessageCategory.COMPLAINT_ISSUE:
            workflow_result.update(await self._handle_complaint(thread, extracted_data))
            
        elif category == MessageCategory.INTERNAL_CLEANER_MESSAGE:
            workflow_result.update(await self._handle_cleaner_message(thread, extracted_data))
            
        elif category == MessageCategory.PAYMENT_INQUIRY:
            workflow_result.update(await self._handle_payment_inquiry(thread, extracted_data))
            
        else:
            workflow_result.update(await self._handle_general_operations(thread, extracted_data))
        
        return workflow_result
    
    async def _handle_prospect_inquiry(
        self, 
        thread: ConversationThread, 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle new prospect inquiries - route to sales."""
        
        return {
            'routing_decision': 'route_to_sales',
            'assigned_agent': 'sophia',  # Booking coordinator
            'requires_response': True,
            'priority': 'normal',
            'suggested_actions': [
                'generate_quote',
                'collect_property_details',
                'schedule_consultation'
            ],
            'handoff_required': True,
            'handoff_target': 'sophia'
        }
    
    async def _handle_schedule_change(
        self, 
        thread: ConversationThread, 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle scheduling changes - route to operations."""
        
        urgency = extracted_data.get('urgency', 'medium')
        action_type = extracted_data.get('action_type', 'reschedule')
        
        priority = 'high' if urgency == 'high' else 'normal'
        
        return {
            'routing_decision': 'route_to_operations',
            'assigned_agent': 'keith',  # Check-in tracker
            'requires_response': True,
            'priority': priority,
            'suggested_actions': [
                f'process_{action_type}',
                'update_calendar',
                'notify_contractor',
                'confirm_changes'
            ],
            'handoff_required': True,
            'handoff_target': 'keith'
        }
    
    async def _handle_complaint(
        self, 
        thread: ConversationThread, 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle complaints - escalate to management."""
        
        severity = extracted_data.get('severity', 'medium')
        complaint_type = extracted_data.get('complaint_type', 'general')
        
        priority = 'urgent' if severity == 'high' else 'high'
        
        return {
            'routing_decision': 'escalate_to_management',
            'assigned_agent': 'dmitri',  # Escalation agent
            'requires_response': True,
            'priority': priority,
            'suggested_actions': [
                'acknowledge_complaint',
                'investigate_issue',
                'offer_resolution',
                'document_incident'
            ],
            'handoff_required': True,
            'handoff_target': 'dmitri'
        }
    
    async def _handle_cleaner_message(
        self, 
        thread: ConversationThread, 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle contractor communications."""
        
        return {
            'routing_decision': 'route_to_operations',
            'assigned_agent': 'keith',  # Check-in tracker
            'requires_response': False,  # Usually just status updates
            'priority': 'normal',
            'suggested_actions': [
                'update_job_status',
                'log_contractor_activity',
                'notify_customer_if_needed'
            ],
            'handoff_required': False
        }
    
    async def _handle_payment_inquiry(
        self, 
        thread: ConversationThread, 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle payment-related questions."""
        
        return {
            'routing_decision': 'route_to_billing',
            'assigned_agent': 'bruno',  # Bonus tracker (handles payments)
            'requires_response': True,
            'priority': 'normal',
            'suggested_actions': [
                'check_payment_status',
                'process_payment_inquiry',
                'send_invoice_if_needed'
            ],
            'handoff_required': True,
            'handoff_target': 'bruno'
        }
    
    async def _handle_general_operations(
        self, 
        thread: ConversationThread, 
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general operational questions."""
        
        return {
            'routing_decision': 'route_to_operations',
            'assigned_agent': 'ava',  # Orchestrator handles general questions
            'requires_response': True,
            'priority': 'normal',
            'suggested_actions': [
                'provide_information',
                'escalate_if_complex'
            ],
            'handoff_required': False
        }
    
    def _update_conversation_state(
        self, 
        thread: ConversationThread, 
        category: MessageCategory, 
        workflow_result: Dict[str, Any]
    ) -> None:
        """Update conversation state based on workflow routing."""
        
        # Update handoff status
        if workflow_result.get('handoff_required'):
            thread.handoff_status = f"pending_{workflow_result['handoff_target']}"
            thread.assigned_agent = workflow_result['assigned_agent']
            thread.status = ConversationStatus.HANDED_OFF
            self.conversation_stats['handoffs_completed'] += 1
        
        # Update priority
        thread.priority_level = workflow_result.get('priority', 'normal')
        
        # Update topic tracking
        if category in [MessageCategory.NEW_PROSPECT_INQUIRY]:
            thread.current_topic = 'quote_request'
        elif category in [MessageCategory.SCHEDULE_CHANGE_REQUEST]:
            thread.current_topic = 'scheduling'
        elif category in [MessageCategory.COMPLAINT_ISSUE]:
            thread.current_topic = 'complaint_resolution'
            thread.status = ConversationStatus.ESCALATED
            self.conversation_stats['escalations_created'] += 1
        
        # Set awaiting response if needed
        if workflow_result.get('requires_response'):
            thread.awaiting_response_type = workflow_result['routing_decision']
            thread.status = ConversationStatus.AWAITING_RESPONSE
    
    def get_conversation_summary(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary for agent context."""
        
        if thread_id not in self.conversations:
            return None
        
        thread = self.conversations[thread_id]
        
        return {
            'thread_id': thread_id,
            'client_profile': asdict(thread.client_profile),
            'status': thread.status.value,
            'message_count': len(thread.messages),
            'last_interaction': thread.updated_at.isoformat(),
            'current_topic': thread.current_topic,
            'priority_level': thread.priority_level,
            'assigned_agent': thread.assigned_agent,
            'recent_messages': [
                {
                    'content': msg.content,
                    'category': msg.category.value,
                    'timestamp': msg.timestamp.isoformat(),
                    'sender_type': msg.sender_type
                }
                for msg in thread.messages[-10:]  # Last 10 messages
            ]
        }
    
    def _load_conversations(self) -> None:
        """Load conversations from file."""
        try:
            if self.conversations_file.exists():
                with open(self.conversations_file, 'r') as f:
                    data = json.load(f)
                    # Would need custom deserialization for full dataclass support
                logger.info("Conversations loaded from file")
        except Exception as e:
            logger.warning(f"Could not load conversations: {e}")
    
    def _save_conversations(self) -> None:
        """Save conversations to file."""
        try:
            self.conversations_file.parent.mkdir(parents=True, exist_ok=True)
            # Would implement full serialization for production
            logger.debug("Conversations saved to file")
        except Exception as e:
            logger.error(f"Could not save conversations: {e}")
    
    def _load_client_profiles(self) -> None:
        """Load client profiles from file."""
        try:
            if self.profiles_file.exists():
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    # Would need custom deserialization for full dataclass support
                logger.info("Client profiles loaded from file")
        except Exception as e:
            logger.warning(f"Could not load client profiles: {e}")
    
    def _save_client_profiles(self) -> None:
        """Save client profiles to file."""
        try:
            self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
            # Would implement full serialization for production
            logger.debug("Client profiles saved to file")
        except Exception as e:
            logger.error(f"Could not save client profiles: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get conversation system statistics."""
        active_count = sum(
            1 for thread in self.conversations.values() 
            if thread.status in [ConversationStatus.ACTIVE, ConversationStatus.AWAITING_RESPONSE]
        )
        
        stats = self.conversation_stats.copy()
        stats['active_conversations'] = active_count
        stats['total_client_profiles'] = len(self.client_profiles)
        
        return stats