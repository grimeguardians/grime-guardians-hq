"""
GoHighLevel CRM Integration
Comprehensive integration with GoHighLevel for client management, conversations, and workflow automation
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json

from ..config.settings import get_settings
from ..models.schemas import ClientProfile, JobRecord, ContactInfo

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class GoHighLevelContact:
    """GoHighLevel contact representation."""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    tags: List[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class GoHighLevelConversation:
    """GoHighLevel conversation representation."""
    id: str
    contact_id: str
    messages: List[Dict[str, Any]]
    status: str
    last_message_at: datetime


class GoHighLevelIntegration:
    """
    Comprehensive GoHighLevel CRM integration for Grime Guardians.
    
    Capabilities:
    - Contact management and synchronization
    - Conversation tracking and message handling
    - Pipeline management for sales processes
    - Custom field management for cleaning preferences
    - Webhook handling for real-time updates
    - Calendar integration for appointment scheduling
    """
    
    def __init__(self):
        self.api_key = settings.gohighlevel_api_key
        self.location_id = settings.gohighlevel_location_id
        self.base_url = "https://rest.gohighlevel.com/v1"
        self.oauth_access_token = settings.highlevel_oauth_access_token
        self.oauth_refresh_token = settings.highlevel_oauth_refresh_token
        self.client_id = settings.highlevel_oauth_client_id
        self.client_secret = settings.highlevel_oauth_client_secret
        
        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GoHighLevel API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Grime-Guardians-Agentic-Suite/1.0"
        }
        
        if self.oauth_access_token:
            headers["Authorization"] = f"Bearer {self.oauth_access_token}"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request to GoHighLevel."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                
                if response.status == 401:
                    # Token expired, try to refresh
                    await self._refresh_oauth_token()
                    # Retry the request
                    self.session.headers.update(self._get_headers())
                    async with self.session.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"GoHighLevel API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in GoHighLevel request: {e}")
            raise
    
    async def _refresh_oauth_token(self) -> bool:
        """Refresh OAuth access token."""
        if not self.oauth_refresh_token:
            logger.warning("No refresh token available for GoHighLevel OAuth")
            return False
        
        refresh_url = "https://services.leadconnectorhq.com/oauth/token"
        refresh_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.oauth_refresh_token
        }
        
        try:
            async with aiohttp.ClientSession() as temp_session:
                async with temp_session.post(refresh_url, json=refresh_data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.oauth_access_token = token_data.get("access_token")
                        self.oauth_refresh_token = token_data.get("refresh_token", self.oauth_refresh_token)
                        logger.info("GoHighLevel OAuth token refreshed successfully")
                        return True
                    else:
                        logger.error(f"Failed to refresh GoHighLevel token: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error refreshing GoHighLevel OAuth token: {e}")
            return False
    
    # Contact Management
    async def get_contact(self, contact_id: str) -> Optional[GoHighLevelContact]:
        """Get contact by ID from GoHighLevel."""
        try:
            response = await self._make_request("GET", f"contacts/{contact_id}")
            return self._parse_contact(response.get("contact", {}))
        except Exception as e:
            logger.error(f"Error getting contact {contact_id}: {e}")
            return None
    
    async def search_contacts(
        self, 
        phone: Optional[str] = None, 
        email: Optional[str] = None,
        name: Optional[str] = None
    ) -> List[GoHighLevelContact]:
        """Search for contacts by phone, email, or name."""
        params = {}
        if phone:
            params["phone"] = phone
        if email:
            params["email"] = email
        if name:
            params["query"] = name
        
        try:
            response = await self._make_request("GET", "contacts/", params=params)
            contacts = response.get("contacts", [])
            return [self._parse_contact(contact) for contact in contacts]
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []
    
    async def create_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: Optional[str] = None,
        custom_fields: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[GoHighLevelContact]:
        """Create new contact in GoHighLevel."""
        contact_data = {
            "firstName": first_name,
            "lastName": last_name,
            "phone": phone,
            "locationId": self.location_id
        }
        
        if email:
            contact_data["email"] = email
        
        if custom_fields:
            contact_data.update(custom_fields)
        
        if tags:
            contact_data["tags"] = tags
        
        try:
            response = await self._make_request("POST", "contacts/", data=contact_data)
            return self._parse_contact(response.get("contact", {}))
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None
    
    async def update_contact(
        self,
        contact_id: str,
        updates: Dict[str, Any]
    ) -> Optional[GoHighLevelContact]:
        """Update existing contact in GoHighLevel."""
        try:
            response = await self._make_request("PUT", f"contacts/{contact_id}", data=updates)
            return self._parse_contact(response.get("contact", {}))
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            return None
    
    # Conversation Management
    async def get_conversations(self, contact_id: str) -> List[GoHighLevelConversation]:
        """Get all conversations for a contact."""
        try:
            response = await self._make_request("GET", f"conversations/", params={"contactId": contact_id})
            conversations = response.get("conversations", [])
            return [self._parse_conversation(conv) for conv in conversations]
        except Exception as e:
            logger.error(f"Error getting conversations for contact {contact_id}: {e}")
            return []
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages from a specific conversation."""
        try:
            response = await self._make_request("GET", f"conversations/{conversation_id}/messages")
            return response.get("messages", [])
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            return []
    
    async def send_message(
        self,
        conversation_id: str,
        message: str,
        message_type: str = "SMS"
    ) -> bool:
        """Send message through GoHighLevel conversation."""
        message_data = {
            "type": message_type,
            "message": message
        }
        
        try:
            await self._make_request("POST", f"conversations/{conversation_id}/messages", data=message_data)
            logger.info(f"Message sent to conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending message to conversation {conversation_id}: {e}")
            return False
    
    # Pipeline and Opportunity Management
    async def get_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipelines for the location."""
        try:
            response = await self._make_request("GET", f"pipelines/", params={"locationId": self.location_id})
            return response.get("pipelines", [])
        except Exception as e:
            logger.error(f"Error getting pipelines: {e}")
            return []
    
    async def create_opportunity(
        self,
        contact_id: str,
        pipeline_id: str,
        stage_id: str,
        title: str,
        value: Optional[float] = None,
        status: str = "open"
    ) -> Optional[Dict[str, Any]]:
        """Create opportunity/deal in GoHighLevel."""
        opportunity_data = {
            "title": title,
            "contactId": contact_id,
            "pipelineId": pipeline_id,
            "stageId": stage_id,
            "status": status,
            "locationId": self.location_id
        }
        
        if value:
            opportunity_data["monetaryValue"] = value
        
        try:
            response = await self._make_request("POST", "opportunities/", data=opportunity_data)
            return response.get("opportunity", {})
        except Exception as e:
            logger.error(f"Error creating opportunity: {e}")
            return None
    
    # Calendar Integration
    async def get_calendars(self) -> List[Dict[str, Any]]:
        """Get available calendars for appointment scheduling."""
        try:
            response = await self._make_request("GET", f"calendars/", params={"locationId": self.location_id})
            return response.get("calendars", [])
        except Exception as e:
            logger.error(f"Error getting calendars: {e}")
            return []
    
    async def create_appointment(
        self,
        calendar_id: str,
        contact_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create appointment in GoHighLevel calendar."""
        appointment_data = {
            "calendarId": calendar_id,
            "contactId": contact_id,
            "title": title,
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "locationId": self.location_id
        }
        
        if notes:
            appointment_data["notes"] = notes
        
        try:
            response = await self._make_request("POST", "appointments/", data=appointment_data)
            return response.get("appointment", {})
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None
    
    # Custom Fields Management
    async def get_custom_fields(self) -> List[Dict[str, Any]]:
        """Get custom fields configuration."""
        try:
            response = await self._make_request("GET", f"custom-fields/", params={"locationId": self.location_id})
            return response.get("customFields", [])
        except Exception as e:
            logger.error(f"Error getting custom fields: {e}")
            return []
    
    async def update_contact_custom_fields(
        self,
        contact_id: str,
        custom_fields: Dict[str, Any]
    ) -> bool:
        """Update custom fields for a contact."""
        try:
            await self._make_request("PUT", f"contacts/{contact_id}", data=custom_fields)
            return True
        except Exception as e:
            logger.error(f"Error updating custom fields for contact {contact_id}: {e}")
            return False
    
    # Grime Guardians Specific Methods
    async def sync_client_profile(self, client_profile: ClientProfile) -> bool:
        """Sync Grime Guardians client profile with GoHighLevel contact."""
        try:
            # Search for existing contact
            contacts = await self.search_contacts(
                phone=client_profile.contact_info.phone,
                email=client_profile.contact_info.email
            )
            
            custom_fields = {
                "grime_guardians_client_id": client_profile.client_id,
                "service_preferences": json.dumps(client_profile.service_preferences),
                "satisfaction_score": client_profile.satisfaction_score,
                "total_jobs": len(client_profile.cleaning_history),
                "last_service_date": client_profile.last_service_date.isoformat() if client_profile.last_service_date else None,
                "client_status": client_profile.status,
                "preferred_contractor": client_profile.service_preferences.get("preferred_contractor"),
                "service_frequency": client_profile.service_preferences.get("frequency", "one_time")
            }
            
            if contacts:
                # Update existing contact
                contact = contacts[0]
                await self.update_contact(contact.id, custom_fields)
                logger.info(f"Updated GoHighLevel contact for client {client_profile.client_id}")
            else:
                # Create new contact
                await self.create_contact(
                    first_name=client_profile.contact_info.first_name,
                    last_name=client_profile.contact_info.last_name,
                    phone=client_profile.contact_info.phone,
                    email=client_profile.contact_info.email,
                    custom_fields=custom_fields,
                    tags=["Grime Guardians Client"]
                )
                logger.info(f"Created new GoHighLevel contact for client {client_profile.client_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing client profile {client_profile.client_id}: {e}")
            return False
    
    async def create_job_opportunity(self, job_record: JobRecord) -> Optional[str]:
        """Create opportunity in GoHighLevel for a cleaning job."""
        try:
            # Find contact for the client
            contacts = await self.search_contacts(phone=job_record.client_phone)
            if not contacts:
                logger.warning(f"No contact found for job {job_record.job_id}")
                return None
            
            contact_id = contacts[0].id
            
            # Get pipelines to find cleaning services pipeline
            pipelines = await self.get_pipelines()
            cleaning_pipeline = next(
                (p for p in pipelines if "cleaning" in p.get("name", "").lower()),
                pipelines[0] if pipelines else None
            )
            
            if not cleaning_pipeline:
                logger.warning("No suitable pipeline found for cleaning jobs")
                return None
            
            # Create opportunity
            opportunity = await self.create_opportunity(
                contact_id=contact_id,
                pipeline_id=cleaning_pipeline["id"],
                stage_id=cleaning_pipeline["stages"][0]["id"],  # First stage
                title=f"{job_record.service_type} - {job_record.scheduled_date}",
                value=float(job_record.total_price) if job_record.total_price else None,
                status="open"
            )
            
            if opportunity:
                logger.info(f"Created opportunity for job {job_record.job_id}")
                return opportunity.get("id")
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating job opportunity for {job_record.job_id}: {e}")
            return None
    
    # Webhook Handling
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook from GoHighLevel."""
        event_type = webhook_data.get("type")
        
        if event_type == "ContactCreate":
            return await self._handle_contact_created(webhook_data)
        elif event_type == "ContactUpdate":
            return await self._handle_contact_updated(webhook_data)
        elif event_type == "InboundMessage":
            return await self._handle_inbound_message(webhook_data)
        elif event_type == "AppointmentCreate":
            return await self._handle_appointment_created(webhook_data)
        else:
            logger.info(f"Unhandled webhook type: {event_type}")
            return {"status": "ignored", "reason": f"Unhandled event type: {event_type}"}
    
    async def _handle_contact_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle contact creation webhook."""
        contact_data = webhook_data.get("contact", {})
        logger.info(f"New contact created: {contact_data.get('id')}")
        return {"status": "processed", "action": "contact_created"}
    
    async def _handle_contact_updated(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle contact update webhook."""
        contact_data = webhook_data.get("contact", {})
        logger.info(f"Contact updated: {contact_data.get('id')}")
        return {"status": "processed", "action": "contact_updated"}
    
    async def _handle_inbound_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inbound message webhook."""
        message_data = webhook_data.get("message", {})
        contact_id = message_data.get("contactId")
        message_text = message_data.get("body", "")
        
        logger.info(f"Inbound message from contact {contact_id}: {message_text[:50]}...")
        
        # This would trigger message classification and routing to appropriate agents
        return {
            "status": "processed", 
            "action": "message_received",
            "contact_id": contact_id,
            "requires_classification": True
        }
    
    async def _handle_appointment_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment creation webhook."""
        appointment_data = webhook_data.get("appointment", {})
        logger.info(f"Appointment created: {appointment_data.get('id')}")
        return {"status": "processed", "action": "appointment_created"}
    
    # Helper Methods
    def _parse_contact(self, contact_data: Dict[str, Any]) -> GoHighLevelContact:
        """Parse GoHighLevel contact data into structured format."""
        return GoHighLevelContact(
            id=contact_data.get("id", ""),
            first_name=contact_data.get("firstName", ""),
            last_name=contact_data.get("lastName", ""),
            email=contact_data.get("email", ""),
            phone=contact_data.get("phone", ""),
            tags=contact_data.get("tags", []),
            custom_fields=contact_data.get("customFields", {}),
            created_at=datetime.fromisoformat(contact_data.get("dateAdded", datetime.now().isoformat()).replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(contact_data.get("dateUpdated", datetime.now().isoformat()).replace('Z', '+00:00'))
        )
    
    def _parse_conversation(self, conversation_data: Dict[str, Any]) -> GoHighLevelConversation:
        """Parse GoHighLevel conversation data into structured format."""
        return GoHighLevelConversation(
            id=conversation_data.get("id", ""),
            contact_id=conversation_data.get("contactId", ""),
            messages=conversation_data.get("messages", []),
            status=conversation_data.get("status", ""),
            last_message_at=datetime.fromisoformat(
                conversation_data.get("lastMessageDate", datetime.now().isoformat()).replace('Z', '+00:00')
            )
        )


# Singleton instance for global use
_ghl_integration = None

def get_gohighlevel_integration() -> GoHighLevelIntegration:
    """Get singleton GoHighLevel integration instance."""
    global _ghl_integration
    if _ghl_integration is None:
        _ghl_integration = GoHighLevelIntegration()
    return _ghl_integration