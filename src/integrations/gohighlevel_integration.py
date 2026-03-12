"""
GoHighLevel CRM Integration — v2 API
Uses https://services.leadconnectorhq.com with required Version header.
Supports multi-calendar queries, hybrid contact resolution, and conversations.
"""

import asyncio
import aiohttp
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from ..config.settings import get_settings, GHL_CALENDARS

logger = logging.getLogger(__name__)
settings = get_settings()

# GHL v2 base URL — the old v1 (rest.gohighlevel.com) does NOT work with current API keys
GHL_BASE_URL = "https://services.leadconnectorhq.com"

# Required by GHL v2 — without this header, calendar and contact calls return errors
GHL_CALENDAR_VERSION = "2021-04-15"
GHL_CONTACTS_VERSION = "2021-07-28"


@dataclass
class GHLAppointment:
    """Parsed GoHighLevel appointment."""
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
    calendar_name: str = ""


@dataclass
class GHLContact:
    """Parsed GoHighLevel contact."""
    id: str
    name: str
    email: str
    phone: str
    tags: List[str]
    custom_fields: Dict[str, Any]
    created_at: datetime


@dataclass
class GHLConversation:
    """Parsed GoHighLevel conversation."""
    id: str
    contact_id: str
    contact_name: str
    type: str
    status: str
    last_message: str
    last_message_time: datetime
    unread_count: int


class GoHighLevelIntegration:
    """
    GoHighLevel v2 CRM integration for Grime Guardians.

    Key fixes vs previous version:
    - Correct base URL: services.leadconnectorhq.com (not rest.gohighlevel.com/v1)
    - Required Version header on all requests
    - Calendar endpoint: /calendars/events with Unix ms timestamps
    - Multi-calendar support (cleaning, walkthrough, commercial)
    - Hybrid contact resolution: ID lookup → name search → title extraction
    """

    def __init__(self):
        self.api_key = settings.gohighlevel_api_key
        self.location_id = settings.gohighlevel_location_id
        self.pit_token = settings.highlevel_pit_token          # Preferred — never expires
        self.oauth_access_token = settings.highlevel_oauth_access_token
        self.oauth_refresh_token = settings.highlevel_oauth_refresh_token
        self.client_id = settings.highlevel_oauth_client_id
        self.client_secret = settings.highlevel_oauth_client_secret

        # Rate limiting — 100ms between requests
        self._last_request_time = datetime.now()
        self._min_interval = 0.1

        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    # ─── Auth ────────────────────────────────────────────────────────────────

    def _auth_header(self) -> str:
        """Return Bearer token — PIT preferred, then OAuth, then legacy API key."""
        token = self.pit_token or self.oauth_access_token or self.api_key
        return f"Bearer {token}"

    def _base_headers(self, version: str) -> Dict[str, str]:
        """Build headers required by GHL v2."""
        return {
            "Authorization": self._auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Version": version,
        }

    # ─── HTTP ────────────────────────────────────────────────────────────────

    async def _request(
        self,
        method: str,
        endpoint: str,
        version: str = GHL_CALENDAR_VERSION,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated GHL v2 API request.

        Args:
            method: HTTP method (GET, POST, PUT).
            endpoint: Path starting with /, e.g. '/calendars/events'.
            version: GHL API version header value.
            params: Query string params.
            data: JSON body for POST/PUT.

        Returns:
            Parsed JSON response dict, or {'error': ...} on failure.
        """
        if not self.session:
            raise RuntimeError("Use GoHighLevelIntegration as an async context manager.")

        # Rate limiting
        elapsed = (datetime.now() - self._last_request_time).total_seconds()
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)

        url = f"{GHL_BASE_URL}{endpoint}"
        headers = self._base_headers(version)
        self._last_request_time = datetime.now()

        try:
            async with self.session.request(
                method, url, headers=headers, params=params, json=data
            ) as resp:
                body = await resp.json(content_type=None)

                if resp.status == 401:
                    # Try refresh once
                    if await self._refresh_token():
                        headers["Authorization"] = self._auth_header()
                        async with self.session.request(
                            method, url, headers=headers, params=params, json=data
                        ) as retry:
                            body = await retry.json(content_type=None)
                            if retry.status >= 400:
                                logger.error(f"GHL {method} {endpoint} retry failed {retry.status}: {body}")
                                return {"error": body, "status_code": retry.status}
                            return body

                if resp.status >= 400:
                    logger.error(f"GHL {method} {endpoint} failed {resp.status}: {body}")
                    return {"error": body, "status_code": resp.status}

                return body

        except aiohttp.ClientError as e:
            logger.error(f"GHL request error {endpoint}: {e}")
            return {"error": str(e)}

    async def _refresh_token(self) -> bool:
        """Refresh OAuth access token using refresh token."""
        if not self.oauth_refresh_token:
            return False
        try:
            async with aiohttp.ClientSession() as tmp:
                async with tmp.post(
                    "https://services.leadconnectorhq.com/oauth/token",
                    json={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": self.oauth_refresh_token,
                    },
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.oauth_access_token = data.get("access_token", self.oauth_access_token)
                        self.oauth_refresh_token = data.get("refresh_token", self.oauth_refresh_token)
                        logger.info("GHL OAuth token refreshed.")
                        return True
                    logger.warning(f"Token refresh failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    # ─── Calendar / Appointments ─────────────────────────────────────────────

    async def get_appointments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[GHLAppointment]:
        """
        Fetch appointments across all configured GHL calendars.

        Args:
            start_date: ISO date string 'YYYY-MM-DD'. Defaults to today.
            end_date:   ISO date string 'YYYY-MM-DD'. Defaults to +7 days.

        Returns:
            List of GHLAppointment, sorted by calendar priority then start time.
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_dt = datetime.fromisoformat(start_date) if start_date else today
        end_dt = datetime.fromisoformat(end_date) if end_date else (today + timedelta(days=7))

        # If end is the same as start (or has no time component), extend to end of that day
        # so a single-date query like start=2026-03-13, end=2026-03-13 captures all day's events
        if end_dt <= start_dt:
            end_dt = start_dt.replace(hour=23, minute=59, second=59)

        # GHL v2 calendar events require Unix millisecond timestamps
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)

        all_appointments: List[GHLAppointment] = []
        calendars = sorted(GHL_CALENDARS.values(), key=lambda c: c["priority"])

        for cal in calendars:
            cal_id = cal["id"]
            cal_name = cal["name"]

            params = {
                "locationId": self.location_id,
                "calendarId": cal_id,
                "startTime": start_ms,
                "endTime": end_ms,
            }

            resp = await self._request("GET", "/calendars/events", params=params)

            if "error" in resp:
                logger.warning(f"Calendar '{cal_name}' error: {resp['error']}")
                continue

            events = resp.get("events", [])
            logger.info(f"Calendar '{cal_name}': {len(events)} events")

            for event in events:
                apt = await self._parse_event(event, cal)
                if apt:
                    all_appointments.append(apt)

        all_appointments.sort(key=lambda a: a.start_time)
        logger.info(f"Total appointments fetched: {len(all_appointments)}")
        return all_appointments

    async def get_todays_schedule(self) -> List[GHLAppointment]:
        """Get today's appointments."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return await self.get_appointments(
            today.strftime("%Y-%m-%d"),
            tomorrow.strftime("%Y-%m-%d"),
        )

    async def get_weeks_schedule(self) -> List[GHLAppointment]:
        """Get this week's appointments (today + 6 days)."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = today + timedelta(days=7)
        return await self.get_appointments(
            today.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
        )

    async def _parse_event(
        self, event: Dict[str, Any], cal_config: Dict[str, Any]
    ) -> Optional[GHLAppointment]:
        """
        Parse a raw GHL calendar event dict into a GHLAppointment.

        Uses hybrid contact resolution:
        1. Direct contact ID lookup via API
        2. Search contacts by name extracted from title
        3. Fall back to whatever is embedded in the event
        """
        try:
            start_str = event.get("startTime", "")
            end_str = event.get("endTime", "")
            if not start_str:
                return None

            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_time = (
                datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                if end_str
                else start_time + timedelta(hours=2)
            )

            title = event.get("title", event.get("eventTitle", "Appointment"))
            contact_id = event.get("contactId", event.get("contact", {}).get("id", ""))
            embedded = event.get("contact", {})

            # Hybrid contact resolution
            contact_name, contact_email, contact_phone = await self._resolve_contact(
                contact_id=contact_id,
                title=title,
                embedded=embedded,
            )

            return GHLAppointment(
                id=event.get("id", ""),
                title=title,
                start_time=start_time,
                end_time=end_time,
                contact_id=contact_id,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                address=event.get("address", embedded.get("address1", "")),
                status=event.get("appointmentStatus", event.get("status", "scheduled")),
                notes=event.get("notes", event.get("description", "")),
                assigned_user=event.get("assignedUserId", ""),
                service_type=cal_config.get("focus", ""),
                calendar_name=cal_config.get("name", ""),
            )

        except Exception as e:
            logger.error(f"Error parsing event {event.get('id', '?')}: {e}")
            return None

    async def _resolve_contact(
        self,
        contact_id: str,
        title: str,
        embedded: Dict[str, Any],
    ):
        """
        Resolve contact name/email/phone using a 3-step fallback strategy.

        Returns:
            Tuple of (name, email, phone) strings.
        """
        # Step 1: Direct API lookup by contact ID
        if contact_id:
            contact = await self._get_contact_by_id(contact_id)
            if contact:
                name = (contact.get("name") or
                        f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip())
                return name or "Unknown", contact.get("email", ""), contact.get("phone", "")

        # Step 2: Search by name extracted from title
        extracted = self._extract_name_from_title(title)
        if extracted and extracted != "Unknown":
            contact = await self._search_contact_by_name(extracted)
            if contact:
                name = (contact.get("name") or
                        f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip())
                return name or extracted, contact.get("email", ""), contact.get("phone", "")

        # Step 3: Use whatever is embedded in the event + extracted name
        return (
            extracted,
            embedded.get("email", ""),
            embedded.get("phone", ""),
        )

    async def _get_contact_by_id(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Direct contact lookup by ID."""
        try:
            resp = await self._request(
                "GET", f"/contacts/{contact_id}", version=GHL_CONTACTS_VERSION
            )
            if "error" not in resp:
                return resp.get("contact", resp)
        except Exception as e:
            logger.debug(f"Contact ID lookup failed for {contact_id}: {e}")
        return None

    async def _search_contact_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Search contacts by name using the v2 search endpoint."""
        try:
            resp = await self._request(
                "POST",
                "/contacts/search",
                version=GHL_CONTACTS_VERSION,
                data={
                    "locationId": self.location_id,
                    "filters": [{"field": "name", "operator": "contains", "value": name}],
                    "pageLimit": 3,
                },
            )
            contacts = resp.get("contacts", [])
            return contacts[0] if contacts else None
        except Exception as e:
            logger.debug(f"Contact name search failed for '{name}': {e}")
        return None

    @staticmethod
    def _extract_name_from_title(title: str) -> str:
        """
        Extract a contact name from an appointment title.

        Handles patterns like:
        - 'Destiny - Recurring Cleaning' → 'Destiny'
        - 'Cleaning for Sarah Johnson' → 'Sarah Johnson'
        - 'Smith Residence Deep Clean' → 'Smith'
        """
        if not title or title.lower() in ("appointment", "cleaning", "service"):
            return "Unknown"

        patterns = [
            r"^([A-Za-z]+(?:\s[A-Za-z]+)?)\s*[-–—]\s*\w+",
            r"(?:cleaning|service)\s+for\s+([A-Za-z\s]+?)(?:\s*[-–—]|$)",
            r"^([A-Za-z]+,\s*[A-Za-z]+)\s*[-–—]",
            r"^([A-Za-z\s]+?)\s*\(",
            r"^([A-Za-z]+)\s+(?:residence|house|home|property)",
            r"^([A-Z][a-z]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                name = re.sub(r"[^A-Za-z\s,.]", "", match.group(1)).strip()
                if len(name) > 1 and name.lower() not in (
                    "cleaning", "service", "appointment", "recurring"
                ):
                    return name.title()

        first = title.split()[0] if title.split() else ""
        return first.title() if first and first[0].isupper() and len(first) > 1 else "Unknown"

    # ─── Contacts ────────────────────────────────────────────────────────────

    async def search_contacts(
        self,
        query: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> List[GHLContact]:
        """
        Search contacts by phone, email, or name/query string.

        Returns:
            List of matching GHLContact objects.
        """
        params: Dict[str, Any] = {"locationId": self.location_id}
        search_term = query or name
        if phone:
            params["phone"] = phone
        if email:
            params["email"] = email
        if search_term:
            params["query"] = search_term

        resp = await self._request(
            "GET", "/contacts/", version=GHL_CONTACTS_VERSION, params=params
        )
        if "error" in resp:
            logger.error(f"Contact search failed: {resp['error']}")
            return []

        return [self._parse_contact(c) for c in resp.get("contacts", [])]

    async def get_contact(self, contact_id: str) -> Optional[GHLContact]:
        """Get a single contact by ID."""
        contact_data = await self._get_contact_by_id(contact_id)
        if contact_data:
            return self._parse_contact(contact_data)
        return None

    async def create_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[GHLContact]:
        """Create a new contact in GHL."""
        body: Dict[str, Any] = {
            "firstName": first_name,
            "lastName": last_name,
            "phone": phone,
            "locationId": self.location_id,
        }
        if email:
            body["email"] = email
        if tags:
            body["tags"] = tags

        resp = await self._request(
            "POST", "/contacts/", version=GHL_CONTACTS_VERSION, data=body
        )
        if "error" in resp:
            logger.error(f"Create contact failed: {resp['error']}")
            return None
        return self._parse_contact(resp.get("contact", {}))

    def _parse_contact(self, data: Dict[str, Any]) -> GHLContact:
        """Parse raw GHL contact dict."""
        created_raw = data.get("dateAdded", "")
        try:
            created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.now()

        return GHLContact(
            id=data.get("id", ""),
            name=data.get("name") or f"{data.get('firstName','')} {data.get('lastName','')}".strip(),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            tags=data.get("tags", []),
            custom_fields=data.get("customFields", {}),
            created_at=created_at,
        )

    # ─── Conversations (for Emma / CXO) ──────────────────────────────────────

    async def get_conversations(self, limit: int = 50) -> List[GHLConversation]:
        """
        Fetch recent conversations — used by Emma (CXO) to monitor client sentiment.

        Args:
            limit: Max number of conversations to return.

        Returns:
            List of GHLConversation objects.
        """
        resp = await self._request(
            "GET",
            "/conversations/search",
            params={"locationId": self.location_id, "limit": limit},
        )
        if "error" in resp:
            logger.error(f"Conversations fetch failed: {resp['error']}")
            return []

        results = []
        for conv in resp.get("conversations", []):
            try:
                last_msg = conv.get("lastMessage", {})
                last_msg_time_raw = last_msg.get("dateAdded", "")
                try:
                    last_msg_time = datetime.fromisoformat(
                        last_msg_time_raw.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    last_msg_time = datetime.now()

                results.append(GHLConversation(
                    id=conv.get("id", ""),
                    contact_id=conv.get("contactId", ""),
                    contact_name=conv.get("contact", {}).get("name", "Unknown"),
                    type=conv.get("type", ""),
                    status=conv.get("status", ""),
                    last_message=last_msg.get("body", ""),
                    last_message_time=last_msg_time,
                    unread_count=conv.get("unreadCount", 0),
                ))
            except Exception as e:
                logger.error(f"Error parsing conversation: {e}")

        logger.info(f"Fetched {len(results)} conversations.")
        return results

    async def get_conversation_messages(
        self, conversation_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get messages from a specific conversation."""
        resp = await self._request(
            "GET",
            f"/conversations/{conversation_id}/messages",
            params={"limit": limit},
        )
        if "error" in resp:
            logger.error(f"Messages fetch failed for {conversation_id}: {resp['error']}")
            return []
        return resp.get("messages", [])

    async def send_message(
        self,
        conversation_id: str,
        message: str,
        message_type: str = "SMS",
    ) -> bool:
        """Send a message in a GHL conversation (SMS, Email, etc.)."""
        resp = await self._request(
            "POST",
            f"/conversations/{conversation_id}/messages",
            data={"type": message_type, "message": message},
        )
        if "error" in resp:
            logger.error(f"Send message failed for {conversation_id}: {resp['error']}")
            return False
        logger.info(f"Message sent to conversation {conversation_id}")
        return True

    # ─── Health Check ─────────────────────────────────────────────────────────

    async def test_connection(self) -> Dict[str, Any]:
        """
        Verify GHL connectivity and surface any auth/endpoint issues.

        Returns:
            Dict with status, calendar count, contact count, conversation count.
        """
        result: Dict[str, Any] = {
            "status": "unknown",
            "base_url": GHL_BASE_URL,
            "location_id": self.location_id,
            "auth_method": "oauth" if self.oauth_access_token else "api_key",
        }

        try:
            # Test 1: location lookup
            loc = await self._request("GET", f"/locations/{self.location_id}")
            result["location_ok"] = "error" not in loc

            # Test 2: today's calendar
            today_apts = await self.get_todays_schedule()
            result["calendar_ok"] = True
            result["todays_appointments"] = len(today_apts)

            # Test 3: contacts
            contacts = await self.search_contacts(query="a")
            result["contacts_ok"] = isinstance(contacts, list)
            result["sample_contacts"] = len(contacts)

            # Test 4: conversations
            convs = await self.get_conversations(limit=5)
            result["conversations_ok"] = isinstance(convs, list)
            result["sample_conversations"] = len(convs)

            result["status"] = "success" if result.get("location_ok") else "partial"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result


# ─── Singleton ───────────────────────────────────────────────────────────────

_ghl: Optional[GoHighLevelIntegration] = None


def get_gohighlevel_integration() -> GoHighLevelIntegration:
    """Get singleton GoHighLevel integration instance."""
    global _ghl
    if _ghl is None:
        _ghl = GoHighLevelIntegration()
    return _ghl
