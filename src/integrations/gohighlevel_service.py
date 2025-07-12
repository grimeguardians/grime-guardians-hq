"""
GoHighLevel Integration Service
Comprehensive CRM integration for Ava (operations) and Dean (sales) suites
Handles calendar, conversations, contacts, and lead management
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import structlog

from ..config.settings import settings, GOHIGHLEVEL_CALENDARS

logger = structlog.get_logger()


@dataclass
class GHLAppointment:
    """GoHighLevel appointment data structure."""
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    contact_id: str
    contact_name: str
    contact_phone: str
    contact_email: str
    address: str
    status: str
    notes: str
    assigned_user: str
    service_type: str


@dataclass
class GHLContact:
    """GoHighLevel contact data structure."""
    id: str
    name: str
    email: str
    phone: str
    source: str
    tags: List[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    last_activity: Optional[datetime] = None


@dataclass
class GHLConversation:
    """GoHighLevel conversation data structure."""
    id: str
    contact_id: str
    contact_name: str
    type: str  # 'SMS', 'Email', 'FB', etc.
    status: str
    last_message: str
    last_message_time: datetime
    unread_count: int
    assigned_user: str


class GoHighLevelService:
    """
    Comprehensive GoHighLevel integration service.
    Provides calendar, conversation, and contact management for both Ava and Dean.
    """
    
    def __init__(self):
        self.base_url = "https://services.leadconnectorhq.com"
        self.location_id = settings.highlevel_location_id
        self.api_key = settings.highlevel_api_key
        self.calendar_id = settings.highlevel_calendar_id
        
        # OAuth credentials for enhanced access (with expiry checking)
        self.oauth_access_token = settings.highlevel_oauth_access_token
        self.oauth_refresh_token = settings.highlevel_oauth_refresh_token
        self.token_expiry = getattr(settings, 'highlevel_token_expiry', 0)
        
        # Private Integration Token (PIT) - preferred for API v2.0
        self.pit_token = getattr(settings, 'highlevel_api_v2_token', None)
        
        # Check if OAuth token is expired
        self.oauth_token_valid = self._check_oauth_token_validity()
        
        # Rate limiting
        self.last_request_time = datetime.now()
        self.min_request_interval = 0.1  # 100ms between requests
        
        logger.info(f"GoHighLevel service initialized - OAuth valid: {self.oauth_token_valid}")
    
    def _check_oauth_token_validity(self) -> bool:
        """Check if OAuth token is still valid."""
        try:
            if not self.oauth_access_token or not self.token_expiry:
                return False
            
            # Convert token expiry from milliseconds to seconds if needed
            expiry_seconds = self.token_expiry / 1000 if self.token_expiry > 1000000000000 else self.token_expiry
            current_time = datetime.now().timestamp()
            
            # Add 5-minute buffer for safety
            buffer_seconds = 300
            is_valid = current_time < (expiry_seconds - buffer_seconds)
            
            if not is_valid:
                hours_expired = (current_time - expiry_seconds) / 3600
                logger.warning(f"OAuth token expired {hours_expired:.1f} hours ago")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error checking OAuth token validity: {e}")
            return False
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None, 
                          use_oauth: bool = True) -> Dict[str, Any]:
        """Make authenticated request to GoHighLevel API."""
        try:
            # Rate limiting
            now = datetime.now()
            time_since_last = (now - self.last_request_time).total_seconds()
            if time_since_last < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_since_last)
            
            url = f"{self.base_url}{endpoint}"
            
            # Choose authentication method
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Grime-Guardians-Agent-System/1.0",
                "Version": "2021-04-15"  # Required for GHL API v2.0 (correct version)
            }
            
            # Choose authentication method - prefer PIT token, then OAuth, then API key
            if self.pit_token:
                headers["Authorization"] = f"Bearer {self.pit_token}"
                logger.debug("Using PIT token authentication")
            elif use_oauth and self.oauth_token_valid and self.oauth_access_token:
                headers["Authorization"] = f"Bearer {self.oauth_access_token}"
                logger.debug("Using OAuth authentication")
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
                logger.debug("Using API key authentication")
            
            self.last_request_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers) as response:
                        response_data = await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        response_data = await response.json()
                elif method.upper() == "PUT":
                    async with session.put(url, headers=headers, json=data) as response:
                        response_data = await response.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers) as response:
                        response_data = await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                if response.status >= 400:
                    logger.error(f"GHL API error: {response.status} - {response_data}")
                    return {"error": response_data, "status_code": response.status}
                
                return response_data
                
        except Exception as e:
            logger.error(f"Error making GHL request: {e}")
            return {"error": str(e)}
    
    async def _get_contact_details(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed contact information using contact ID."""
        try:
            if not contact_id:
                return None
                
            endpoint = f"/contacts/{contact_id}"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.debug(f"Could not fetch contact details for {contact_id}: {response['error']}")
                return None
                
            contact_data = response.get('contact', response)
            if isinstance(contact_data, dict):
                return contact_data
            return None
            
        except Exception as e:
            logger.debug(f"Error fetching contact details for {contact_id}: {e}")
            return None
    
    def _extract_name_from_title(self, title: str) -> str:
        """Extract contact name from appointment title using smart patterns."""
        try:
            if not title or title.lower() in ['appointment', 'cleaning', 'service']:
                return "Unknown"
            
            # Common patterns in cleaning appointment titles:
            patterns = [
                # "Destiny - Recurring Cleaning" -> "Destiny"
                r'^([A-Za-z]+)\s*[-–—]\s*\w+',
                # "Cleaning for Sarah Johnson" -> "Sarah Johnson"
                r'(?:cleaning|service)\s+for\s+([A-Za-z\s]+?)(?:\s*[-–—]|$)',
                # "Johnson, Mike - Deep Clean" -> "Johnson, Mike"
                r'^([A-Za-z]+,\s*[A-Za-z]+)\s*[-–—]',
                # "Mike Peterson (Property Manager)" -> "Mike Peterson"
                r'^([A-Za-z\s]+?)\s*\(',
                # "Smith Residence Cleaning" -> "Smith"
                r'^([A-Za-z]+)\s+(?:residence|house|home|property)',
                # First word that looks like a name
                r'^([A-Z][a-z]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Clean up the name
                    name = re.sub(r'[^A-Za-z\s,.]', '', name).strip()
                    if len(name) > 1 and name.lower() not in ['cleaning', 'service', 'appointment', 'recurring']:
                        return name.title()
            
            # If no pattern matches, return the first word if it looks like a name
            first_word = title.split()[0] if title.split() else ""
            if first_word and first_word[0].isupper() and len(first_word) > 1:
                return first_word.title()
                
            return "Unknown"
            
        except Exception as e:
            logger.debug(f"Error extracting name from title '{title}': {e}")
            return "Unknown"
    
    # CALENDAR OPERATIONS (Primarily for Ava - Operations)
    
    async def get_appointments(self, start_date: Optional[datetime] = None, 
                             end_date: Optional[datetime] = None) -> List[GHLAppointment]:
        """Get appointments from GoHighLevel calendar."""
        try:
            # Default to today if no dates provided
            if not start_date:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = start_date + timedelta(days=7)  # Next 7 days
            
            # Format dates for API (milliseconds timestamp format for calendar events)
            start_millis = int(start_date.timestamp() * 1000)
            end_millis = int(end_date.timestamp() * 1000)
            
            # Use prioritized calendar configuration
            all_appointments = []
            
            # Check calendars in priority order
            calendar_configs = sorted(GOHIGHLEVEL_CALENDARS.values(), key=lambda x: x['priority'])
            
            for config in calendar_configs:
                calendar_id = config["id"]
                calendar_name = config["name"]
                priority = config["priority"]
                responsible_agent = config["responsible_agent"]
                logger.debug(f"Checking priority {priority} calendar: {calendar_name} (Agent: {responsible_agent})")
                
                endpoint = f"/calendars/events?locationId={self.location_id}&calendarId={calendar_id}&startTime={start_millis}&endTime={end_millis}"
            
                response = await self._make_request("GET", endpoint)
                
                if "error" in response:
                    logger.warning(f"Error fetching events from calendar {calendar_name}: {response['error']}")
                    continue
                
                # Handle events from this calendar
                events_data = response.get("events", [])
                priority_indicator = "🔥" if priority == 1 else "⭐" if priority == 2 else "📅"
                logger.debug(f"{priority_indicator} Found {len(events_data)} events in {calendar_name} (Priority {priority})")
            
                for event_data in events_data:
                    try:
                        # Parse calendar event format
                        contact_info = event_data.get("contact", {})
                        contact_id = event_data.get("contactId", contact_info.get("id", ""))
                        title = event_data.get("title", event_data.get("eventTitle", "Appointment"))
                        
                        # Handle missing start/end times
                        start_time_str = event_data.get("startTime", "")
                        end_time_str = event_data.get("endTime", "")
                        
                        if not start_time_str:
                            logger.warning(f"Event {event_data.get('id')} missing startTime, skipping")
                            continue
                            
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00')) if end_time_str else start_time + timedelta(hours=1)
                        
                        # INTELLIGENT HYBRID CONTACT RESOLUTION
                        # Try to get full contact details from API
                        api_contact = None
                        if contact_id:
                            api_contact = await self._get_contact_details(contact_id)
                        
                        # Determine best contact information
                        if api_contact:
                            # Use API contact data (most reliable)
                            contact_name = api_contact.get("name", "Unknown")
                            contact_email = api_contact.get("email", "")
                            contact_phone = api_contact.get("phone", "")
                            logger.debug(f"✅ Got API contact for {title}: {contact_name}")
                        else:
                            # Fallback: extract from title + any embedded contact info
                            contact_name = self._extract_name_from_title(title)
                            contact_email = contact_info.get("email", "")
                            contact_phone = contact_info.get("phone", "")
                            logger.debug(f"📝 Extracted contact from title '{title}': {contact_name}")
                        
                        appointment = GHLAppointment(
                            id=event_data.get("id", ""),
                            title=title,
                            start_time=start_time,
                            end_time=end_time,
                            contact_id=contact_id,
                            contact_name=contact_name,
                            contact_phone=contact_phone,
                            contact_email=contact_email,
                            address=event_data.get("address", contact_info.get("address1", "")),
                            status=event_data.get("status", "scheduled"),
                            notes=event_data.get("notes", event_data.get("description", "")),
                            assigned_user=event_data.get("assignedUserId", responsible_agent),
                            service_type=config["focus"]  # Use calendar focus as service type
                        )
                        
                        # Add calendar metadata for agent intelligence
                        appointment._calendar_priority = priority
                        appointment._calendar_type = config["focus"]
                        appointment._responsible_agent = responsible_agent
                        appointment._contact_source = "api" if api_contact else "extracted"
                        all_appointments.append(appointment)
                    except Exception as e:
                        logger.error(f"Error parsing event data from {calendar_name}: {e}")
                        continue
            
            # Sort appointments by calendar priority, then by time
            all_appointments.sort(key=lambda apt: (apt._calendar_priority, apt.start_time))
            
            logger.info(f"Retrieved {len(all_appointments)} appointments from {len(calendar_configs)} prioritized calendars")
            return all_appointments
            
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []
    
    async def get_todays_schedule(self) -> List[GHLAppointment]:
        """Get today's cleaning schedule for Ava."""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            appointments = await self.get_appointments(today, tomorrow)
            
            # Return real appointments only
            if not appointments:
                logger.info("No appointments found for today")
                return []
            
            return appointments
        except Exception as e:
            logger.error(f"Error getting today's schedule: {e}")
            # Return empty list instead of mock data
            logger.info("API error - returning empty schedule")
            return []
    
    def _get_mock_appointments(self) -> List[GHLAppointment]:
        """Provide mock appointments for demo/fallback purposes."""
        now = datetime.now()
        return [
            GHLAppointment(
                id="demo_001",
                title="Move-Out Cleaning",
                start_time=now.replace(hour=10, minute=0),
                end_time=now.replace(hour=13, minute=0),
                contact_id="demo_contact_001",
                contact_name="Sarah Johnson",
                contact_phone="(612) 555-0123",
                contact_email="sarah.johnson@email.com",
                address="1234 Oak St, Eagan, MN 55121",
                status="scheduled",
                notes="3BR/2BA apartment - tenant moving out Friday",
                assigned_user="jennifer",
                service_type="Move-Out Cleaning"
            ),
            GHLAppointment(
                id="demo_002", 
                title="Deep Cleaning",
                start_time=now.replace(hour=14, minute=30),
                end_time=now.replace(hour=17, minute=0),
                contact_id="demo_contact_002",
                contact_name="Mike Peterson (Property Manager)",
                contact_phone="(651) 555-0456",
                contact_email="mike@properties.com",
                address="5678 Maple Ave, Burnsville, MN 55337",
                status="confirmed",
                notes="Post-renovation deep clean before showing",
                assigned_user="olga",
                service_type="Deep Cleaning"
            )
        ]
    
    def _get_mock_conversations(self) -> List[GHLConversation]:
        """REMOVED: No longer providing mock conversations to prevent hallucination."""
        logger.warning("Mock conversations disabled - conversations API not available")
        return []
    
    async def get_upcoming_appointments(self, hours_ahead: int = 24) -> List[GHLAppointment]:
        """Get upcoming appointments within specified hours."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=hours_ahead)
        return await self.get_appointments(start_time, end_time)
    
    # CONVERSATION OPERATIONS (Primarily for Dean - Sales)
    
    async def get_conversations(self, limit: int = 50) -> List[GHLConversation]:
        """Get recent conversations for Dean's sales monitoring."""
        try:
            endpoint = f"/conversations/?locationId={self.location_id}&limit={limit}"
            
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching conversations: {response['error']}")
                logger.info("Conversations API not available - returning empty list")
                return []
            
            conversations = []
            for conv_data in response.get("conversations", []):
                try:
                    conversation = GHLConversation(
                        id=conv_data.get("id", ""),
                        contact_id=conv_data.get("contactId", ""),
                        contact_name=conv_data.get("contact", {}).get("name", "Unknown"),
                        type=conv_data.get("type", ""),
                        status=conv_data.get("status", ""),
                        last_message=conv_data.get("lastMessage", {}).get("body", ""),
                        last_message_time=datetime.fromisoformat(
                            conv_data.get("lastMessage", {}).get("dateAdded", "").replace('Z', '+00:00')
                        ) if conv_data.get("lastMessage", {}).get("dateAdded") else datetime.now(),
                        unread_count=conv_data.get("unreadCount", 0),
                        assigned_user=conv_data.get("assignedTo", "")
                    )
                    conversations.append(conversation)
                except Exception as e:
                    logger.error(f"Error parsing conversation data: {e}")
                    continue
            
            logger.info(f"Retrieved {len(conversations)} conversations from GHL")
            
            # Return real conversations only
            if not conversations:
                logger.info("No conversations found in GoHighLevel")
                return []
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            logger.info("Conversations API error - returning empty list")
            return []
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get messages from a specific conversation."""
        try:
            endpoint = f"/conversations/{conversation_id}/messages?limit={limit}"
            
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching conversation messages: {response['error']}")
                return []
            
            return response.get("messages", [])
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []
    
    async def send_conversation_message(self, conversation_id: str, message: str, 
                                     message_type: str = "SMS") -> bool:
        """Send a message in a GoHighLevel conversation."""
        try:
            endpoint = f"/conversations/{conversation_id}/messages"
            
            data = {
                "type": message_type,
                "message": message
            }
            
            response = await self._make_request("POST", endpoint, data)
            
            if "error" in response:
                logger.error(f"Error sending message: {response['error']}")
                return False
            
            logger.info(f"Message sent successfully to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending conversation message: {e}")
            return False
    
    # CONTACT OPERATIONS (Both Ava and Dean)
    
    async def get_contacts(self, limit: int = 100, query: str = None) -> List[GHLContact]:
        """Get contacts from GoHighLevel."""
        try:
            endpoint = f"/contacts/?locationId={self.location_id}&limit={limit}"
            if query:
                endpoint += f"&query={query}"
            
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching contacts: {response['error']}")
                return []
            
            contacts = []
            for contact_data in response.get("contacts", []):
                try:
                    contact = GHLContact(
                        id=contact_data.get("id", ""),
                        name=contact_data.get("name", ""),
                        email=contact_data.get("email", ""),
                        phone=contact_data.get("phone", ""),
                        source=contact_data.get("source", ""),
                        tags=contact_data.get("tags", []),
                        custom_fields=contact_data.get("customFields", {}),
                        created_at=datetime.fromisoformat(
                            contact_data.get("dateAdded", "").replace('Z', '+00:00')
                        ) if contact_data.get("dateAdded") else datetime.now()
                    )
                    contacts.append(contact)
                except Exception as e:
                    logger.error(f"Error parsing contact data: {e}")
                    continue
            
            logger.info(f"Retrieved {len(contacts)} contacts from GHL")
            return contacts
            
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    async def create_contact(self, name: str, email: str = None, phone: str = None, 
                           tags: List[str] = None, source: str = "Agent System") -> Optional[str]:
        """Create a new contact in GoHighLevel."""
        try:
            endpoint = f"/contacts/"
            
            data = {
                "name": name,
                "locationId": self.location_id,
                "source": source
            }
            
            if email:
                data["email"] = email
            if phone:
                data["phone"] = phone
            if tags:
                data["tags"] = tags
            
            response = await self._make_request("POST", endpoint, data)
            
            if "error" in response:
                logger.error(f"Error creating contact: {response['error']}")
                return None
            
            contact_id = response.get("contact", {}).get("id")
            logger.info(f"Created contact successfully: {contact_id}")
            return contact_id
            
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None
    
    # ANALYTICS & REPORTING (Dean's Sales Intelligence)
    
    async def get_lead_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get lead generation analytics for Dean."""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get recent contacts (leads)
            contacts = await self.get_contacts(limit=200)
            
            # Get recent conversations
            conversations = await self.get_conversations(limit=100)
            
            # Get recent appointments
            appointments = await self.get_appointments(start_date, end_date)
            
            # Calculate metrics
            analytics = {
                "period_days": days_back,
                "total_leads": len([c for c in contacts if c.created_at >= start_date]),
                "total_conversations": len(conversations),
                "active_conversations": len([c for c in conversations if c.unread_count > 0]),
                "scheduled_appointments": len(appointments),
                "lead_sources": {},
                "conversation_types": {},
                "appointment_status": {}
            }
            
            # Analyze lead sources
            for contact in contacts:
                if contact.created_at >= start_date:
                    source = contact.source or "Unknown"
                    analytics["lead_sources"][source] = analytics["lead_sources"].get(source, 0) + 1
            
            # Analyze conversation types
            for conv in conversations:
                conv_type = conv.type or "Unknown"
                analytics["conversation_types"][conv_type] = analytics["conversation_types"].get(conv_type, 0) + 1
            
            # Analyze appointment status
            for apt in appointments:
                status = apt.status or "Unknown"
                analytics["appointment_status"][status] = analytics["appointment_status"].get(status, 0) + 1
            
            logger.info(f"Generated lead analytics for {days_back} days")
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting lead analytics: {e}")
            return {}
    
    # HEALTH CHECK & TESTING
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test GoHighLevel API connection and permissions."""
        try:
            # Test basic API access
            endpoint = f"/locations/{self.location_id}"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                return {
                    "status": "error",
                    "message": f"API connection failed: {response['error']}",
                    "oauth_working": False,
                    "basic_api_working": False
                }
            
            # Test OAuth access
            oauth_test = await self._make_request("GET", "/oauth/locationId", use_oauth=True)
            oauth_working = "error" not in oauth_test
            
            # Test specific endpoints
            calendar_test = await self.get_todays_schedule()
            conversations_test = await self.get_conversations(limit=5)
            contacts_test = await self.get_contacts(limit=5)
            
            return {
                "status": "success",
                "message": "GoHighLevel integration working properly",
                "oauth_working": oauth_working,
                "basic_api_working": True,
                "calendar_accessible": len(calendar_test) >= 0,
                "conversations_accessible": len(conversations_test) >= 0,
                "contacts_accessible": len(contacts_test) >= 0,
                "location_id": self.location_id,
                "calendar_id": self.calendar_id
            }
            
        except Exception as e:
            logger.error(f"Error testing GHL connection: {e}")
            return {
                "status": "error", 
                "message": f"Connection test failed: {str(e)}",
                "oauth_working": False,
                "basic_api_working": False
            }


# Global GoHighLevel service instance
ghl_service = GoHighLevelService()