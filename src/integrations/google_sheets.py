"""
Google Sheets Integration — reads and writes the GG leads sheet.
Uses a service account (no OAuth needed, no token expiry).

Sheet: https://docs.google.com/spreadsheets/d/1HHH4A-jJOeoO1zztc2JoVMVPCGo-3iXLM5drOxmLoNw
Tab:   Contacts
"""

import json
import logging
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from google.oauth2 import service_account
from google.auth.transport.requests import Request

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SPREADSHEET_ID = "1HHH4A-jJOeoO1zztc2JoVMVPCGo-3iXLM5drOxmLoNw"
TAB = "Contacts"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"

# Map sheet Industry values → template keys used by DeanEmailCampaign
INDUSTRY_TO_CONTACT_TYPE: Dict[str, str] = {
    "property management": "property_manager",
    "realtor": "realtor",
    "real estate": "realtor",
    "construction": "construction",
    "real estate developer": "real_estate_developer",
    "general": "general",
}

# Exact column order from the sheet (0-indexed)
COL = {
    "name": 0,
    "industry": 1,
    "linkedin": 2,
    "websites": 3,
    "phone": 4,
    "phone_type": 5,
    "location": 6,
    "email": 7,
    "birthday": 8,
    "status": 9,
    "email_1_date": 10,
    "email_1_template": 11,
    "email_2_date": 12,
    "email_3_date": 13,
    "reply_date": 14,
    "reply_sentiment": 15,
    "notes": 16,
    "sender_account": 17,   # which Gmail account sent the initial email
}
TOTAL_COLS = 18


@dataclass
class SheetContact:
    row_index: int          # 1-based sheet row (for write-back)
    name: str
    email: str
    industry: str
    contact_type: str       # derived from industry
    phone: str = ""
    company: str = ""   # populated if a Company column is added to the sheet later
    location: str = ""
    status: str = "cold"
    email_1_date: str = ""
    email_1_template: str = ""
    email_2_date: str = ""
    email_3_date: str = ""
    reply_date: str = ""
    reply_sentiment: str = ""
    notes: str = ""
    sender_account: str = ""  # e.g. "brandonr@grimeguardians.com"


def _derive_contact_type(industry: str) -> str:
    """Map Industry column value to a template key."""
    key = industry.strip().lower()
    for pattern, ctype in INDUSTRY_TO_CONTACT_TYPE.items():
        if pattern in key:
            return ctype
    return "general"


class GoogleSheetsClient:
    """
    Thin async-friendly wrapper around the Sheets REST API.
    Uses a service account — no OAuth dance, no token expiry.
    """

    def __init__(self):
        self._creds: Optional[service_account.Credentials] = None

    def _get_token(self) -> str:
        """Return a valid bearer token, refreshing if needed."""
        if self._creds is None:
            sa_file = settings.google_service_account_file
            if not sa_file:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE not set in .env")
            self._creds = service_account.Credentials.from_service_account_file(
                sa_file, scopes=SCOPES
            )
        if not self._creds.valid:
            self._creds.refresh(Request())
        return self._creds.token

    def _request(self, method: str, url: str, body: Optional[dict] = None) -> dict:
        """Make an authenticated Sheets API request."""
        token = self._get_token()
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def read_contacts(self) -> List[SheetContact]:
        """
        Read all contacts from the sheet.
        Skips header row, skips rows with no email, skips status=skip.
        Returns SheetContact list ready for DeanEmailCampaign.
        """
        url = f"{BASE_URL}/{SPREADSHEET_ID}/values/{TAB}!A1:R"
        result = self._request("GET", url)
        rows = result.get("values", [])

        contacts = []
        for i, row in enumerate(rows[1:], start=2):  # row 2 onwards (1-indexed)
            # Pad short rows
            while len(row) < TOTAL_COLS:
                row.append("")

            email = row[COL["email"]].strip().lower()
            if not email:
                continue

            status = row[COL["status"]].strip().lower()
            if status == "skip":
                continue

            industry = row[COL["industry"]].strip()
            contacts.append(SheetContact(
                row_index=i,
                name=row[COL["name"]].strip(),
                email=email,
                industry=industry,
                contact_type=_derive_contact_type(industry),
                phone=row[COL["phone"]].strip(),
                location=row[COL["location"]].strip(),
                status=status or "cold",
                email_1_date=row[COL["email_1_date"]].strip(),
                email_1_template=row[COL["email_1_template"]].strip(),
                email_2_date=row[COL["email_2_date"]].strip(),
                email_3_date=row[COL["email_3_date"]].strip(),
                reply_date=row[COL["reply_date"]].strip(),
                reply_sentiment=row[COL["reply_sentiment"]].strip(),
                notes=row[COL["notes"]].strip(),
                sender_account=row[COL["sender_account"]].strip() if len(row) > COL["sender_account"] else "",
            ))

        logger.info(f"Sheets: read {len(contacts)} active contacts.")
        return contacts

    def update_contact(self, contact: SheetContact) -> None:
        """Write tracking columns back to the sheet for a single contact."""
        range_notation = f"{TAB}!J{contact.row_index}:R{contact.row_index}"
        url = (
            f"{BASE_URL}/{SPREADSHEET_ID}/values/{range_notation}"
            f"?valueInputOption=RAW"
        )
        values = [[
            contact.status,
            contact.email_1_date,
            contact.email_1_template,
            contact.email_2_date,
            contact.email_3_date,
            contact.reply_date,
            contact.reply_sentiment,
            contact.notes,
            contact.sender_account,
        ]]
        self._request("PUT", url, body={"values": values})
        logger.debug(f"Sheets: updated row {contact.row_index} ({contact.email})")
