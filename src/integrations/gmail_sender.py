"""
Gmail Sender — account-specific OAuth sender.
Instantiated once per Gmail account. Handles token refresh automatically.
"""

import base64
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional

import aiohttp

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class GmailSender:
    """
    Sends email from a single Gmail account via the Gmail API.
    Uses OAuth refresh token flow — no SMTP, no app passwords.

    Usage:
        sender = GmailSender(email="you@gmail.com", refresh_token="1//xxx...")
        async with aiohttp.ClientSession() as session:
            await sender.send(session, to="lead@example.com",
                              subject="...", body="...")
    """

    def __init__(self, email: str, refresh_token: str):
        self.email = email
        self.refresh_token = refresh_token
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_token(self, session: aiohttp.ClientSession) -> str:
        """Return a valid access token, refreshing if needed."""
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        async with session.post(OAUTH_TOKEN_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }) as resp:
            resp.raise_for_status()
            data = await resp.json()

        self._access_token = data["access_token"]
        self._token_expires_at = datetime.now() + timedelta(seconds=data.get("expires_in", 3600) - 60)
        logger.debug(f"Gmail token refreshed for {self.email}")
        return self._access_token

    async def send(
        self,
        session: aiohttp.ClientSession,
        to: str,
        subject: str,
        body: str,
    ) -> bool:
        """
        Send a plain-text email.

        Args:
            session: Shared aiohttp session.
            to: Recipient email address.
            subject: Email subject line.
            body: Plain-text email body.

        Returns:
            True on success, False on failure.
        """
        msg = MIMEText(body, "plain")
        msg["to"] = to
        msg["from"] = self.email
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        try:
            token = await self._get_token(session)
            async with session.post(
                GMAIL_SEND_URL,
                json={"raw": raw},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            ) as resp:
                resp.raise_for_status()
            logger.info(f"Email sent: {self.email} → {to} | {subject[:50]}")
            return True
        except Exception as e:
            logger.error(f"Gmail send failed ({self.email} → {to}): {e}")
            return False
