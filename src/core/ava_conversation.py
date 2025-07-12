"""
Ava's Operational Conversation Implementation
Focused on scheduling, logistics, personnel, and operational optimization
"""

from typing import Dict, Any
from datetime import datetime
from .conversation_engine import ConversationEngine, ConversationContext
from ..config import settings
import structlog

logger = structlog.get_logger()


class AvaConversationEngine(ConversationEngine):
    """
    Ava's specialized conversation engine for operational matters.
    
    Focuses on:
    - Scheduling and logistics optimization
    - Personnel management and assignments
    - Quality operations and SOPs
    - Problem-solving for operational issues
    """
    
    def __init__(self):
        # Ava's persona configuration
        persona_config = {
            'name': 'Ava',
            'role': 'Operations Coordinator',
            'model': 'gpt-4-turbo-preview',
            'max_tokens': 150,  # Very concise responses
            'temperature': 0.7,
            'max_messages': 25,
            'context_timeout_hours': 8,  # Shorter for active operations
            'system_prompt': self._build_ava_system_prompt(),
            'error_message': "I'm having trouble accessing my operational systems right now. Please try again, or contact the team directly if it's urgent."
        }
        
        super().__init__(persona_config)
        
        # Ava's operational knowledge base
        self.operational_knowledge = self._load_operational_knowledge()
    
    def _build_ava_system_prompt(self) -> str:
        """Build Ava's comprehensive system prompt."""
        return f"""You are Ava, the Operations Coordinator for Grime Guardians, a premium cleaning service in the Twin Cities, MN area.

ROLE & PERSONALITY:
- Professional, efficient, solution-oriented
- Deep operational knowledge, optimization-focused
- Supportive of contractors while maintaining standards
- Practical solutions, clear communication
- Friendly but professional tone
- CRITICAL: Keep ALL responses under 2 sentences maximum

YOUR OPERATIONAL DOMAIN:
✅ SCHEDULING & LOGISTICS:
- Job assignments and contractor scheduling
- Route optimization and geographic preferences
- Timing conflicts and schedule adjustments
- Same-day changes and emergency coverage

✅ PERSONNEL MANAGEMENT:
- Contractor availability and capacity
- Performance tracking and coaching needs
- Geographic preferences (Jennifer: south metro, Liuda: north metro only)
- Skills matching for specific job types

✅ QUALITY OPERATIONS:
- Standard Operating Procedures (SOPs)
- Checklist compliance and requirements
- Photo submission standards and requirements
- 3-strike quality system enforcement

✅ OPTIMIZATION & EFFICIENCY:
- Workflow improvements and bottleneck identification
- Contractor utilization optimization
- Process improvements and efficiency gains
- Operational best practices

❌ NOT YOUR DOMAIN (Refer to appropriate executive):
- Financial matters, pricing, revenue (CFO domain)
- Strategic business decisions, partnerships (Dean domain)
- Marketing, lead generation, sales (Emma domain)
- HR policies, payroll, legal matters (Executive team)

BUSINESS CONTEXT:
- Company: Grime Guardians (Premium cleaning service)
- Mission: "We clean like it's our name on the lease"
- Service Area: Twin Cities, MN (Primary: South metro/Eagan)
- Target: 6-10 cleans per day, $7,500+/month per cleaner
- Structure: All 1099 contractors (Jennifer, Olga, Liuda, Zhanna)

CONTRACTOR PROFILES:
- Jennifer: $28/hr, South metro preference, experienced
- Olga: $25/hr, Any location, reliable
- Liuda: $30/hr, North metro ONLY, skilled
- Zhanna: $25/hr, Any location, developing

QUALITY REQUIREMENTS:
- Arrival check-in: 🚗 emoji or "arrived" 
- Completion check-in: 🏁 emoji or "finished"
- Required photos: Kitchen, bathrooms, entry area, impacted rooms
- Checklist completion for all job types
- 3-strike system: Warning → Formal warning → $10 deduction

SERVICE TYPES:
- Move-Out/Move-In: Most complex, highest value
- Deep Cleaning: Thorough initial cleaning
- Recurring Maintenance: Regular upkeep
- Post-Construction: Specialized cleanup
- Commercial: Requires walkthrough

RESPONSE GUIDELINES:
- MAXIMUM 2 sentences - absolutely no exceptions
- Be direct and actionable - no fluff or explanations
- Bullet points acceptable for lists
- One specific recommendation per response
- Single clarifying question if needed
- Escalate non-operational matters with one sentence

Current date: {datetime.now().strftime('%A, %B %d, %Y')}
Current time: {datetime.now().strftime('%I:%M %p')} CST"""

    def _load_operational_knowledge(self) -> Dict[str, Any]:
        """Load Ava's operational knowledge base."""
        return {
            'sops': {
                'arrival_checkin': {
                    'requirement': '15 minutes before scheduled time',
                    'method': 'Discord message with 🚗 or "arrived"',
                    'purpose': 'Client coordination and tracking'
                },
                'completion_checkin': {
                    'requirement': 'Immediately after job completion',
                    'method': 'Discord message with 🏁 or "finished"',
                    'purpose': 'Job closure and quality tracking'
                },
                'photo_requirements': {
                    'required_photos': ['kitchen', 'bathrooms', 'entry_area', 'impacted_rooms'],
                    'quality_standards': 'Clear, well-lit, shows completed work',
                    'submission_method': 'Discord attachment in check-in channel'
                },
                'checklist_completion': {
                    'requirement': 'Complete job-specific checklist',
                    'types': ['move_in_out', 'deep_cleaning', 'recurring'],
                    'purpose': 'Quality consistency and compliance'
                }
            },
            'scheduling_guidelines': {
                'geographic_optimization': {
                    'jennifer': 'South metro preferred (Eagan, Burnsville, Apple Valley)',
                    'liuda': 'North metro ONLY (Minneapolis, St. Paul north)',
                    'olga': 'Any location, good for gap filling',
                    'zhanna': 'Any location, learning all areas'
                },
                'timing_standards': {
                    'arrival_buffer': '15 minutes early',
                    'job_duration_estimates': {
                        'move_out_in': '3-5 hours depending on size',
                        'deep_cleaning': '2-4 hours depending on size',
                        'recurring': '1.5-3 hours depending on size',
                        'post_construction': 'Varies by square footage'
                    }
                }
            },
            'quality_standards': {
                'three_strike_system': {
                    'first_violation': 'Friendly reminder and coaching',
                    'second_violation': 'Formal warning and process review',
                    'third_violation': '$10 deduction and performance plan'
                },
                'common_violations': [
                    'Missing check-in messages',
                    'Incomplete photo submissions',
                    'Uncompleted checklists',
                    'Late arrivals without notice'
                ]
            }
        }
    
    def get_business_context(self, conversation: ConversationContext) -> str:
        """Get current operational context for Ava."""
        context_parts = []
        
        # Add current operational status
        context_parts.append("CURRENT OPERATIONAL STATUS:")
        context_parts.append("- All contractors active and available")
        context_parts.append("- Quality compliance monitoring active")
        context_parts.append("- Check-in tracking system operational")
        context_parts.append("- GoHighLevel calendar integration active")
        
        # Add relevant SOPs based on conversation
        if self._conversation_mentions_quality(conversation):
            context_parts.append("\nQUALITY REQUIREMENTS ACTIVE:")
            context_parts.append("- Photo submissions required for all jobs")
            context_parts.append("- Check-in compliance monitored via Discord")
            context_parts.append("- 3-strike system enforced")
        
        if self._conversation_mentions_scheduling(conversation):
            context_parts.append("\nSCHEDULING CONSIDERATIONS:")
            context_parts.append("- Jennifer: South metro preference")
            context_parts.append("- Liuda: North metro ONLY")
            context_parts.append("- Target: 6-10 jobs per day")
            context_parts.append("- 15-minute arrival buffer standard")
            context_parts.append("- Live schedule available via GoHighLevel")
        
        # Add schedule context if conversation mentions schedule/appointments
        if self._conversation_mentions_schedule_viewing(conversation):
            context_parts.append("\nSCHEDULE ACCESS:")
            context_parts.append("- Real-time GoHighLevel calendar integration")
            context_parts.append("- Can view today's appointments and upcoming schedule")
            context_parts.append("- Contractor assignments and contact details available")
        
        return "\n".join(context_parts)
    
    def _conversation_mentions_quality(self, conversation: ConversationContext) -> bool:
        """Check if conversation involves quality topics."""
        quality_keywords = ['quality', 'checklist', 'photo', 'sop', 'standard', 'violation', 'compliance']
        recent_messages = conversation.messages[-5:]  # Check last 5 messages
        
        for message in recent_messages:
            if any(keyword in message.content.lower() for keyword in quality_keywords):
                return True
        return False
    
    def _conversation_mentions_scheduling(self, conversation: ConversationContext) -> bool:
        """Check if conversation involves scheduling topics."""
        scheduling_keywords = ['schedule', 'assignment', 'route', 'time', 'availability', 'jennifer', 'liuda', 'olga', 'zhanna']
        recent_messages = conversation.messages[-5:]  # Check last 5 messages
        
        for message in recent_messages:
            if any(keyword in message.content.lower() for keyword in scheduling_keywords):
                return True
        return False
    
    def _conversation_mentions_schedule_viewing(self, conversation: ConversationContext) -> bool:
        """Check if conversation involves viewing schedule/appointments."""
        schedule_view_keywords = ['schedule', 'appointment', 'calendar', 'today', 'tomorrow', 'upcoming', 'jobs today', 'what jobs']
        recent_messages = conversation.messages[-5:]  # Check last 5 messages
        
        for message in recent_messages:
            if any(keyword in message.content.lower() for keyword in schedule_view_keywords):
                return True
        return False
    
    async def get_contractor_status(self) -> Dict[str, Any]:
        """Get current contractor status (would integrate with real data)."""
        # This would integrate with actual contractor tracking system
        return {
            'jennifer': {'status': 'available', 'current_job': None, 'next_job': '2:00 PM'},
            'olga': {'status': 'on_job', 'current_job': 'Deep cleaning - Burnsville', 'eta_completion': '1:30 PM'},
            'liuda': {'status': 'available', 'current_job': None, 'next_job': '3:00 PM'},
            'zhanna': {'status': 'available', 'current_job': None, 'next_job': 'Tomorrow 9:00 AM'}
        }
    
    async def get_scheduling_recommendations(self, job_details: Dict[str, Any]) -> str:
        """Generate scheduling recommendations for a job."""
        location = job_details.get('location', '').lower()
        service_type = job_details.get('service_type', '')
        urgency = job_details.get('urgency', 'normal')
        
        recommendations = []
        
        # Geographic matching
        if any(area in location for area in ['eagan', 'burnsville', 'apple valley', 'south']):
            recommendations.append("📍 GEOGRAPHIC MATCH: Jennifer (south metro preference) - ideal assignment")
        elif any(area in location for area in ['minneapolis', 'st. paul', 'north']):
            recommendations.append("📍 GEOGRAPHIC MATCH: Liuda (north metro only) - required assignment")
        else:
            recommendations.append("📍 FLEXIBLE LOCATION: Olga or Zhanna available for any area")
        
        # Service type considerations
        if 'move' in service_type.lower():
            recommendations.append("🏠 MOVE SERVICE: Consider experience level - Jennifer or Liuda preferred")
        elif 'deep' in service_type.lower():
            recommendations.append("🧽 DEEP CLEANING: All contractors qualified")
        
        # Urgency considerations
        if urgency == 'urgent':
            recommendations.append("⚡ URGENT: Prioritize nearest available contractor")
        
        return "\n".join(recommendations)
    
    async def get_todays_schedule(self) -> str:
        """Get today's schedule from GoHighLevel."""
        try:
            from ..integrations.gohighlevel_service import ghl_service
            appointments = await ghl_service.get_todays_schedule()
            
            if not appointments:
                return "No appointments scheduled for today."
            
            schedule_summary = f"TODAY'S SCHEDULE ({len(appointments)} appointments):\n"
            
            for apt in sorted(appointments, key=lambda x: x.start_time):
                time_str = apt.start_time.strftime('%I:%M %p')
                contractor = self._get_contractor_from_assignment(apt.assigned_user)
                
                schedule_summary += f"• {time_str} - {apt.contact_name} ({apt.service_type})\n"
                schedule_summary += f"  📍 {apt.address[:50]}{'...' if len(apt.address) > 50 else ''}\n"
                schedule_summary += f"  👤 {contractor} | 📞 {apt.contact_phone}\n\n"
            
            return schedule_summary.strip()
            
        except Exception as e:
            logger.error(f"Error getting today's schedule: {e}")
            return "Unable to retrieve today's schedule from GoHighLevel."
    
    async def check_upcoming_appointments(self, hours_ahead: int = 4) -> str:
        """Check for upcoming appointments in the next few hours."""
        try:
            from ..integrations.gohighlevel_service import ghl_service
            appointments = await ghl_service.get_upcoming_appointments(hours_ahead)
            
            if not appointments:
                return f"No appointments in the next {hours_ahead} hours."
            
            upcoming_summary = f"UPCOMING ({hours_ahead}h): {len(appointments)} appointments\n"
            
            for apt in sorted(appointments, key=lambda x: x.start_time):
                time_str = apt.start_time.strftime('%I:%M %p')
                contractor = self._get_contractor_from_assignment(apt.assigned_user)
                
                upcoming_summary += f"• {time_str} - {apt.contact_name}\n"
                upcoming_summary += f"  👤 {contractor} | Status: {apt.status}\n"
            
            return upcoming_summary.strip()
            
        except Exception as e:
            logger.error(f"Error checking upcoming appointments: {e}")
            return "Unable to check upcoming appointments."
    
    def _get_contractor_from_assignment(self, assigned_user_id: str) -> str:
        """Map assigned user ID to contractor name."""
        # This would map GHL user IDs to contractor names
        contractor_mapping = {
            # Add actual GHL user IDs here
            "": "Unassigned"
        }
        return contractor_mapping.get(assigned_user_id, "Unknown Contractor")


# Global Ava conversation instance
ava_conversation = AvaConversationEngine()