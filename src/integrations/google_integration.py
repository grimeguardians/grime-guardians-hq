"""
Google Services Integration
Comprehensive integration with Google Calendar, Gmail, and Drive for scheduling and communication
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config.settings import get_settings
from ..models.schemas import JobRecord, ClientProfile

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class GoogleCalendarEvent:
    """Google Calendar event representation."""
    id: str
    summary: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    attendees: List[str]
    status: str


@dataclass
class GmailMessage:
    """Gmail message representation."""
    id: str
    thread_id: str
    subject: str
    sender: str
    recipient: str
    body: str
    timestamp: datetime
    labels: List[str]


class GoogleServicesIntegration:
    """
    Comprehensive Google Services integration for Grime Guardians.
    
    Capabilities:
    - Google Calendar integration for appointment scheduling
    - Gmail integration for client communication
    - Google Drive integration for document storage
    - OAuth 2.0 authentication and token management
    - Real-time synchronization with Google services
    """
    
    def __init__(self):
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret
        self.refresh_token = settings.gmail_refresh_token
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Google API endpoints
        self.oauth_url = "https://oauth2.googleapis.com/token"
        self.calendar_api_url = "https://www.googleapis.com/calendar/v3"
        self.gmail_api_url = "https://gmail.googleapis.com/gmail/v1"
        self.drive_api_url = "https://www.googleapis.com/drive/v3"
        
        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        await self._ensure_valid_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_valid_token(self):
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            await self._refresh_access_token()
    
    async def _refresh_access_token(self):
        """Refresh OAuth access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            async with self.session.post(self.oauth_url, data=token_data) as response:
                response.raise_for_status()
                token_response = await response.json()
                
                self.access_token = token_response["access_token"]
                expires_in = token_response.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60s buffer
                
                logger.info("Google OAuth token refreshed successfully")
                
        except Exception as e:
            logger.error(f"Failed to refresh Google OAuth token: {e}")
            raise
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers for Google API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_google_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Google API."""
        await self._ensure_valid_token()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_auth_headers()
            ) as response:
                
                if response.status == 401:
                    # Token expired, refresh and retry
                    await self._refresh_access_token()
                    async with self.session.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params,
                        headers=self._get_auth_headers()
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"Google API request failed: {e}")
            raise
    
    # Google Calendar Integration
    async def get_calendar_list(self) -> List[Dict[str, Any]]:
        """Get list of available calendars."""
        try:
            response = await self._make_google_request("GET", f"{self.calendar_api_url}/users/me/calendarList")
            return response.get("items", [])
        except Exception as e:
            logger.error(f"Error getting calendar list: {e}")
            return []
    
    async def create_calendar_event(
        self,
        calendar_id: str,
        summary: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Optional[GoogleCalendarEvent]:
        """Create new calendar event."""
        event_data = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Chicago"  # Central Time for Grime Guardians
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Chicago"
            }
        }
        
        if location:
            event_data["location"] = location
        
        if attendees:
            event_data["attendees"] = [{"email": email} for email in attendees]
        
        try:
            response = await self._make_google_request(
                "POST",
                f"{self.calendar_api_url}/calendars/{calendar_id}/events",
                data=event_data
            )
            return self._parse_calendar_event(response)
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None
    
    async def update_calendar_event(
        self,
        calendar_id: str,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Optional[GoogleCalendarEvent]:
        """Update existing calendar event."""
        try:
            response = await self._make_google_request(
                "PATCH",
                f"{self.calendar_api_url}/calendars/{calendar_id}/events/{event_id}",
                data=updates
            )
            return self._parse_calendar_event(response)
        except Exception as e:
            logger.error(f"Error updating calendar event {event_id}: {e}")
            return None
    
    async def delete_calendar_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete calendar event."""
        try:
            await self._make_google_request(
                "DELETE",
                f"{self.calendar_api_url}/calendars/{calendar_id}/events/{event_id}"
            )
            logger.info(f"Deleted calendar event {event_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting calendar event {event_id}: {e}")
            return False
    
    async def get_calendar_events(
        self,
        calendar_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 250
    ) -> List[GoogleCalendarEvent]:
        """Get calendar events within time range."""
        params = {
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        if time_min:
            params["timeMin"] = time_min.isoformat()
        if time_max:
            params["timeMax"] = time_max.isoformat()
        
        try:
            response = await self._make_google_request(
                "GET",
                f"{self.calendar_api_url}/calendars/{calendar_id}/events",
                params=params
            )
            events = response.get("items", [])
            return [self._parse_calendar_event(event) for event in events]
        except Exception as e:
            logger.error(f"Error getting calendar events: {e}")
            return []
    
    # Gmail Integration
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email through Gmail API."""
        if not from_email:
            from_email = settings.gmail_emails[0] if settings.gmail_emails else "noreply@grimeguardians.com"
        
        # Create message
        message = MIMEMultipart("alternative") if html_body else MIMEText(body)
        message["to"] = to_email
        message["from"] = from_email
        message["subject"] = subject
        
        if html_body:
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(html_body, "html")
            message.attach(text_part)
            message.attach(html_part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        try:
            await self._make_google_request(
                "POST",
                f"{self.gmail_api_url}/users/me/messages/send",
                data={"raw": raw_message}
            )
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def get_emails(
        self,
        query: Optional[str] = None,
        max_results: int = 50,
        include_spam_trash: bool = False
    ) -> List[GmailMessage]:
        """Get emails matching query."""
        params = {
            "maxResults": max_results,
            "includeSpamTrash": include_spam_trash
        }
        
        if query:
            params["q"] = query
        
        try:
            # Get message list
            response = await self._make_google_request(
                "GET",
                f"{self.gmail_api_url}/users/me/messages",
                params=params
            )
            
            messages = []
            for message_info in response.get("messages", []):
                message = await self.get_email_details(message_info["id"])
                if message:
                    messages.append(message)
            
            return messages
        except Exception as e:
            logger.error(f"Error getting emails: {e}")
            return []
    
    async def get_email_details(self, message_id: str) -> Optional[GmailMessage]:
        """Get detailed email information."""
        try:
            response = await self._make_google_request(
                "GET",
                f"{self.gmail_api_url}/users/me/messages/{message_id}"
            )
            return self._parse_gmail_message(response)
        except Exception as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None
    
    # Grime Guardians Specific Methods
    async def create_job_calendar_event(self, job_record: JobRecord) -> Optional[str]:
        """Create calendar event for cleaning job."""
        calendars = await self.get_calendar_list()
        if not calendars:
            logger.warning("No calendars available for job scheduling")
            return None
        
        # Use primary calendar or first available
        calendar_id = "primary"
        
        # Calculate end time based on service type
        duration_hours = {
            "move_out_in": 5,
            "deep_cleaning": 4,
            "recurring": 3,
            "one_time": 3,
            "post_construction": 6
        }.get(job_record.service_type, 3)
        
        end_time = job_record.scheduled_date + timedelta(hours=duration_hours)
        
        # Create event
        event = await self.create_calendar_event(
            calendar_id=calendar_id,
            summary=f"Cleaning: {job_record.service_type.replace('_', ' ').title()}",
            description=f"""
            Job ID: {job_record.job_id}
            Service: {job_record.service_type.replace('_', ' ').title()}
            Contractor: {job_record.assigned_contractor.title()}
            Client Phone: {job_record.client_phone}
            Price: ${job_record.total_price}
            
            Address: {job_record.client_address}
            """.strip(),
            start_time=job_record.scheduled_date,
            end_time=end_time,
            location=job_record.client_address
        )
        
        if event:
            logger.info(f"Created calendar event for job {job_record.job_id}")
            return event.id
        
        return None
    
    async def send_appointment_confirmation(
        self,
        client_profile: ClientProfile,
        job_record: JobRecord
    ) -> bool:
        """Send appointment confirmation email to client."""
        subject = f"Cleaning Appointment Confirmed - {job_record.scheduled_date.strftime('%m/%d/%Y')}"
        
        body = f"""
        Dear {client_profile.contact_info.first_name},
        
        Your cleaning appointment has been confirmed!
        
        APPOINTMENT DETAILS:
        Date: {job_record.scheduled_date.strftime('%A, %B %d, %Y')}
        Time: {job_record.scheduled_date.strftime('%I:%M %p')}
        Service: {job_record.service_type.replace('_', ' ').title()}
        Contractor: {job_record.assigned_contractor.title()}
        Address: {job_record.client_address}
        
        Your contractor will text you 30 minutes before arrival.
        
        We clean like it's our name on the lease!
        
        Best regards,
        Grime Guardians Team
        Phone: (555) 123-4567
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Cleaning Appointment Confirmed</h2>
            <p>Dear {client_profile.contact_info.first_name},</p>
            <p>Your cleaning appointment has been confirmed!</p>
            
            <div style="background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>APPOINTMENT DETAILS</h3>
                <p><strong>Date:</strong> {job_record.scheduled_date.strftime('%A, %B %d, %Y')}</p>
                <p><strong>Time:</strong> {job_record.scheduled_date.strftime('%I:%M %p')}</p>
                <p><strong>Service:</strong> {job_record.service_type.replace('_', ' ').title()}</p>
                <p><strong>Contractor:</strong> {job_record.assigned_contractor.title()}</p>
                <p><strong>Address:</strong> {job_record.client_address}</p>
            </div>
            
            <p>Your contractor will text you 30 minutes before arrival.</p>
            <p><em>We clean like it's our name on the lease!</em></p>
            
            <p>Best regards,<br>
            Grime Guardians Team<br>
            Phone: (555) 123-4567</p>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=client_profile.contact_info.email,
            subject=subject,
            body=body,
            html_body=html_body
        )
    
    async def send_completion_notification(
        self,
        client_profile: ClientProfile,
        job_record: JobRecord,
        satisfaction_survey_link: Optional[str] = None
    ) -> bool:
        """Send job completion notification to client."""
        subject = f"Cleaning Complete - Thank You!"
        
        body = f"""
        Dear {client_profile.contact_info.first_name},
        
        Your cleaning service has been completed successfully!
        
        SERVICE SUMMARY:
        Date: {job_record.completed_at.strftime('%A, %B %d, %Y') if job_record.completed_at else 'Today'}
        Service: {job_record.service_type.replace('_', ' ').title()}
        Contractor: {job_record.assigned_contractor.title()}
        
        We hope you're thrilled with the results! Our team takes pride in delivering exceptional cleaning services.
        
        {f'Please take a moment to share your feedback: {satisfaction_survey_link}' if satisfaction_survey_link else ''}
        
        Thank you for choosing Grime Guardians!
        
        Best regards,
        Grime Guardians Team
        """
        
        return await self.send_email(
            to_email=client_profile.contact_info.email,
            subject=subject,
            body=body
        )
    
    # Helper Methods
    def _parse_calendar_event(self, event_data: Dict[str, Any]) -> GoogleCalendarEvent:
        """Parse Google Calendar event data."""
        start_time = datetime.fromisoformat(
            event_data["start"].get("dateTime", event_data["start"].get("date")).replace('Z', '+00:00')
        )
        end_time = datetime.fromisoformat(
            event_data["end"].get("dateTime", event_data["end"].get("date")).replace('Z', '+00:00')
        )
        
        attendees = []
        if event_data.get("attendees"):
            attendees = [attendee.get("email", "") for attendee in event_data["attendees"]]
        
        return GoogleCalendarEvent(
            id=event_data["id"],
            summary=event_data.get("summary", ""),
            description=event_data.get("description", ""),
            start_time=start_time,
            end_time=end_time,
            location=event_data.get("location", ""),
            attendees=attendees,
            status=event_data.get("status", "")
        )
    
    def _parse_gmail_message(self, message_data: Dict[str, Any]) -> GmailMessage:
        """Parse Gmail message data."""
        headers = {h["name"]: h["value"] for h in message_data["payload"]["headers"]}
        
        # Extract body
        body = ""
        if "parts" in message_data["payload"]:
            for part in message_data["payload"]["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode()
                    break
        elif "body" in message_data["payload"] and "data" in message_data["payload"]["body"]:
            body = base64.urlsafe_b64decode(message_data["payload"]["body"]["data"]).decode()
        
        return GmailMessage(
            id=message_data["id"],
            thread_id=message_data["threadId"],
            subject=headers.get("Subject", ""),
            sender=headers.get("From", ""),
            recipient=headers.get("To", ""),
            body=body,
            timestamp=datetime.fromtimestamp(int(message_data["internalDate"]) / 1000),
            labels=message_data.get("labelIds", [])
        )


# Singleton instance
_google_integration = None

def get_google_integration() -> GoogleServicesIntegration:
    """Get singleton Google Services integration instance."""
    global _google_integration
    if _google_integration is None:
        _google_integration = GoogleServicesIntegration()
    return _google_integration