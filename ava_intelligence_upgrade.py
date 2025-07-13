#!/usr/bin/env python3
"""
Ava Intelligence Upgrade
Enhances Ava's GoHighLevel integration, date parsing, and conversational context
"""

import re
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger()


class AvaDateParser:
    """Enhanced date parsing for Ava to understand natural language dates."""
    
    def __init__(self):
        self.weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        self.months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
    
    def parse_date_from_message(self, message: str) -> Optional[datetime]:
        """Parse various date formats from user message."""
        message = message.lower().strip()
        now = datetime.now()
        
        # Pattern 1: "Monday the 14th", "Tuesday the 15th"
        match = re.search(r'(\w+day)\s+(?:the\s+)?(\d{1,2})(?:th|st|nd|rd)?', message)
        if match:
            weekday_name = match.group(1)
            day_num = int(match.group(2))
            
            if weekday_name in self.weekdays:
                target_weekday = self.weekdays[weekday_name]
                
                # Find the target date
                for days_ahead in range(0, 14):  # Look up to 2 weeks ahead
                    target_date = now + timedelta(days=days_ahead)
                    if target_date.weekday() == target_weekday and target_date.day == day_num:
                        return target_date
        
        # Pattern 2: "next Monday", "this Friday", or just "Monday"
        match = re.search(r'(?:(?:next|this)\s+)?(\w+day)', message)
        if match:
            weekday_name = match.group(1)
            if weekday_name in self.weekdays:
                target_weekday = self.weekdays[weekday_name]
                days_ahead = (target_weekday - now.weekday()) % 7
                if days_ahead == 0:  # If it's today, assume next week
                    days_ahead = 7
                return now + timedelta(days=days_ahead)
        
        # Pattern 3: "tomorrow", "today"
        if 'tomorrow' in message:
            return now + timedelta(days=1)
        elif 'today' in message:
            return now
        
        # Pattern 4: "July 14", "December 25"
        match = re.search(r'(\w+)\s+(\d{1,2})', message)
        if match:
            month_name = match.group(1)
            day_num = int(match.group(2))
            
            if month_name in self.months:
                month_num = self.months[month_name]
                try:
                    # Try current year first
                    target_date = datetime(now.year, month_num, day_num)
                    if target_date < now:
                        # If it's in the past, try next year
                        target_date = datetime(now.year + 1, month_num, day_num)
                    return target_date
                except ValueError:
                    pass
        
        # Pattern 5: "in 3 days", "in a week"
        match = re.search(r'in\s+(\d+)\s+days?', message)
        if match:
            days_ahead = int(match.group(1))
            return now + timedelta(days=days_ahead)
        
        if 'in a week' in message or 'next week' in message:
            return now + timedelta(days=7)
        
        return None


class AvaGoHighLevelIntegration:
    """Enhanced GoHighLevel integration for Ava with real API calls."""
    
    def __init__(self):
        from src.integrations.gohighlevel_service import ghl_service
        self.ghl_service = ghl_service
    
    async def get_appointments_for_date(self, target_date: datetime) -> List[Dict[str, Any]]:
        """Get appointments for a specific date."""
        try:
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            appointments = await self.ghl_service.get_appointments(start_date, end_date)
            
            # Convert to dict format for Discord display (preserve metadata)
            appointment_dicts = []
            for apt in appointments:
                apt_dict = {
                    'id': apt.id,
                    'title': apt.title,
                    'startTime': apt.start_time.isoformat(),
                    'endTime': apt.end_time.isoformat(),
                    'contact': {
                        'name': apt.contact_name,
                        'phone': apt.contact_phone,
                        'email': apt.contact_email
                    },
                    'address': apt.address,
                    'status': apt.status,
                    'notes': apt.notes,
                    'assignedUser': apt.assigned_user,
                    'serviceType': apt.service_type,
                    # Preserve calendar metadata
                    '_calendar_priority': getattr(apt, '_calendar_priority', 1),
                    '_calendar_type': getattr(apt, '_calendar_type', 'residential_commercial_cleaning'),
                    '_responsible_agent': getattr(apt, '_responsible_agent', 'ava'),
                    '_contact_source': getattr(apt, '_contact_source', 'api')
                }
                appointment_dicts.append(apt_dict)
            
            return appointment_dicts
            
        except Exception as e:
            logger.error(f"Error getting appointments for {target_date}: {e}")
            return []
    
    async def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations from GoHighLevel."""
        try:
            conversations = await self.ghl_service.get_conversations(limit)
            
            # Convert to dict format
            conv_dicts = []
            for conv in conversations:
                conv_dict = {
                    'id': conv.id,
                    'contactName': conv.contact_name,
                    'type': conv.type,
                    'status': conv.status,
                    'lastMessage': conv.last_message,
                    'lastMessageTime': conv.last_message_time.isoformat(),
                    'unreadCount': conv.unread_count,
                    'assignedUser': conv.assigned_user
                }
                conv_dicts.append(conv_dict)
            
            return conv_dicts
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    async def get_lead_analytics(self) -> Dict[str, Any]:
        """Get lead analytics from GoHighLevel."""
        try:
            analytics = await self.ghl_service.get_lead_analytics(days_back=7)
            return analytics
        except Exception as e:
            logger.error(f"Error getting lead analytics: {e}")
            return {}


class AvaIntelligentResponse:
    """Enhanced response generation for Ava with context awareness."""
    
    def __init__(self):
        self.date_parser = AvaDateParser()
        self.ghl_integration = AvaGoHighLevelIntegration()
    
    async def handle_schedule_question(self, message: str) -> str:
        """Handle schedule-related questions with date parsing."""
        # Parse the date from the message
        target_date = self.date_parser.parse_date_from_message(message)
        
        if not target_date:
            # Default to today if no date specified
            target_date = datetime.now()
        
        # Get appointments for the target date
        appointments = await self.ghl_integration.get_appointments_for_date(target_date)
        
        # Format the date for display
        date_str = target_date.strftime('%A, %B %d, %Y')
        
        if appointments:
            response = f"📅 **Schedule for {date_str}:**\n\n"
            
            # Group appointments by calendar type
            cleaning_appointments = []
            walkthrough_appointments = []
            commercial_appointments = []
            
            for apt in appointments:
                calendar_type = apt.get('_calendar_type', 'residential_commercial_cleaning')
                if calendar_type == 'residential_commercial_cleaning':
                    cleaning_appointments.append(apt)
                elif calendar_type == 'lead_qualification':
                    walkthrough_appointments.append(apt)
                elif calendar_type == 'commercial_lead_generation':
                    commercial_appointments.append(apt)
            
            # Display by priority
            appointment_groups = [
                ("🔥 **CLEANING APPOINTMENTS** (Priority 1)", cleaning_appointments),
                ("⭐ **WALKTHROUGH APPOINTMENTS** (Priority 2)", walkthrough_appointments), 
                ("📅 **COMMERCIAL WALKTHROUGHS** (Priority 3)", commercial_appointments)
            ]
            
            total_shown = 0
            for group_title, group_appointments in appointment_groups:
                if group_appointments:
                    response += f"{group_title}:\n"
                    
                    for apt in group_appointments:
                        total_shown += 1
                        contact = apt.get('contact', {})
                        start_time = apt.get('startTime', '')
                        
                        if start_time:
                            try:
                                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                time_str = dt.strftime('%I:%M %p')
                            except:
                                time_str = start_time
                        else:
                            time_str = "Time TBD"
                        
                        client_name = contact.get('name', 'Unknown Client')
                        title = apt.get('title', 'Service')
                        address = apt.get('address', 'Address TBD')
                        assigned_user = apt.get('assignedUser', 'Unassigned')
                        
                        response += f"• **{time_str} - {client_name}**\n"
                        response += f"  📋 {title}\n"
                        response += f"  👤 {assigned_user}\n"
                        response += f"  📍 {address[:50]}{'...' if len(address) > 50 else ''}\n"
                        if apt.get('notes'):
                            response += f"  📝 {apt['notes'][:60]}{'...' if len(apt['notes']) > 60 else ''}\n"
                        response += "\n"
                    
                    response += "\n"
            
            # Add summary
            if total_shown > 1:
                response += f"📊 **Total: {total_shown} appointments**\n"
                response += f"🔥 Cleaning: {len(cleaning_appointments)} | ⭐ Walkthroughs: {len(walkthrough_appointments)} | 📅 Commercial: {len(commercial_appointments)}"
            
            return response
        else:
            return f"📅 No appointments scheduled for {date_str}. The schedule is clear."
    
    async def handle_conversation_question(self, message: str) -> str:
        """Handle questions about recent conversations."""
        conversations = await self.ghl_integration.get_recent_conversations(limit=5)
        
        if conversations:
            response = "💬 **Recent GoHighLevel Conversations:**\n\n"
            
            for i, conv in enumerate(conversations, 1):
                contact_name = conv.get('contactName', 'Unknown')
                msg_type = conv.get('type', 'Message')
                last_msg = conv.get('lastMessage', '')
                unread = conv.get('unreadCount', 0)
                
                response += f"**{i}. {contact_name}** ({msg_type})\n"
                if unread > 0:
                    response += f"   🔴 {unread} unread messages\n"
                if last_msg:
                    response += f"   💬 Last: {last_msg[:100]}{'...' if len(last_msg) > 100 else ''}\n"
                response += "\n"
            
            return response
        else:
            return "💬 I don't have access to conversation data through the current GoHighLevel API configuration. You can check your messages directly in GoHighLevel."
    
    async def handle_analytics_question(self, message: str) -> str:
        """Handle questions about lead analytics."""
        analytics = await self.ghl_integration.get_lead_analytics()
        
        if analytics:
            response = "📊 **Lead Analytics (Last 7 Days):**\n\n"
            response += f"📈 **Total Leads:** {analytics.get('total_leads', 0)}\n"
            response += f"💬 **Conversations:** {analytics.get('total_conversations', 0)}\n"
            response += f"🔥 **Active Chats:** {analytics.get('active_conversations', 0)}\n"
            response += f"📅 **Appointments:** {analytics.get('scheduled_appointments', 0)}\n"
            
            # Lead sources
            sources = analytics.get('lead_sources', {})
            if sources:
                response += "\n**📍 Lead Sources:**\n"
                for source, count in sources.items():
                    response += f"• {source}: {count}\n"
            
            return response
        else:
            return "📊 Unable to retrieve analytics data at this time."


# Global instance
ava_intelligence = AvaIntelligentResponse()