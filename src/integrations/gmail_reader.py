"""
Gmail Reader — scans inbox for replies from known leads.
Runs before the daily send batch so overnight replies suppress follow-ups.

Sentiment classification is keyword-based (no AI cost):
  positive  — any engagement (interest, questions, availability)
  negative  — unsubscribe / stop / remove requests
  neutral   — ambiguous replies (logged but no sheet update; human reviews)

Auth reuses the same OAuth client_id/secret as GmailSender.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import base64
import json

import aiohttp

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"

# Keywords that indicate the lead wants out
UNSUBSCRIBE_KEYWORDS = {
    "unsubscribe", "remove me", "remove from", "stop emailing",
    "stop contacting", "not interested", "do not contact", "opt out",
    "take me off", "no thanks", "no thank you", "leave me alone",
    "please remove", "don't email", "dont email",
}

# Keywords that indicate genuine interest
POSITIVE_KEYWORDS = {
    "interested", "tell me more", "sounds good", "yes", "sure",
    "how much", "what's the price", "pricing", "price", "quote",
    "available", "availability", "when can", "let's talk", "lets talk",
    "schedule", "call me", "reach out", "follow up", "follow-up",
    "send me", "more info", "what do you", "can you", "would love",
    "absolutely", "definitely", "let me know", "set up", "set something",
    "open to", "open to it", "happy to", "works for me",
}


@dataclass
class ReplyResult:
    """A reply found in the inbox matching a known lead."""
    contact_email: str
    message_id: str
    received_at: datetime
    subject: str
    snippet: str
    sentiment: str  # "positive", "negative", "neutral"
    sender_account: str  # which Gmail account received the reply


def _classify_sentiment(subject: str, snippet: str) -> str:
    """
    Keyword-based sentiment classification.
    Returns 'positive', 'negative', or 'neutral'.
    """
    text = (subject + " " + snippet).lower()

    for kw in UNSUBSCRIBE_KEYWORDS:
        if kw in text:
            return "negative"

    for kw in POSITIVE_KEYWORDS:
        if kw in text:
            return "positive"

    # Any reply that isn't clearly negative or positive
    return "neutral"


class GmailReader:
    """
    Reads a single Gmail account's inbox for replies from known leads.
    Reuses the same OAuth refresh token flow as GmailSender.
    """

    def __init__(self, email: str, refresh_token: str):
        """
        Args:
            email: The Gmail account address.
            refresh_token: OAuth refresh token for this account.
        """
        self.email = email
        self.refresh_token = refresh_token
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_token(self, session: aiohttp.ClientSession) -> str:
        """Return a valid access token, refreshing if needed."""
        if (
            self._access_token
            and self._token_expires_at
            and datetime.now() < self._token_expires_at
        ):
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
        self._token_expires_at = datetime.now() + timedelta(
            seconds=data.get("expires_in", 3600) - 60
        )
        return self._access_token

    async def _list_message_ids(
        self,
        session: aiohttp.ClientSession,
        since_days: int = 30,
    ) -> List[str]:
        """
        Return message IDs received in the last `since_days` days,
        in:inbox only (excludes sent, drafts, spam).
        """
        token = await self._get_token(session)
        query = f"in:inbox newer_than:{since_days}d"
        url = f"{GMAIL_BASE_URL}/messages?q={query}&maxResults=200"

        async with session.get(
            url, headers={"Authorization": f"Bearer {token}"}
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        return [m["id"] for m in data.get("messages", [])]

    async def _get_message_meta(
        self,
        session: aiohttp.ClientSession,
        message_id: str,
    ) -> Optional[dict]:
        """
        Fetch metadata + snippet for a single message.
        Uses format=metadata to avoid downloading full bodies.
        """
        token = await self._get_token(session)
        url = (
            f"{GMAIL_BASE_URL}/messages/{message_id}"
            f"?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date"
        )
        try:
            async with session.get(
                url, headers={"Authorization": f"Bearer {token}"}
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            logger.warning(f"GmailReader: failed to fetch message {message_id}: {e}")
            return None

    async def scan_for_replies(
        self,
        session: aiohttp.ClientSession,
        lead_emails: Set[str],
        since_days: int = 30,
    ) -> List[ReplyResult]:
        """
        Scan inbox for messages from any email in `lead_emails`.

        Args:
            session: Shared aiohttp session.
            lead_emails: Set of lowercase lead email addresses to match against.
            since_days: How many days back to look.

        Returns:
            List of ReplyResult for any matching messages found.
        """
        results: List[ReplyResult] = []

        try:
            message_ids = await self._list_message_ids(session, since_days)
        except Exception as e:
            logger.error(f"GmailReader ({self.email}): inbox list failed — {e}")
            return results

        logger.debug(
            f"GmailReader ({self.email}): scanning {len(message_ids)} inbox messages"
        )

        for msg_id in message_ids:
            meta = await self._get_message_meta(session, msg_id)
            if not meta:
                continue

            headers = {
                h["name"].lower(): h["value"]
                for h in meta.get("payload", {}).get("headers", [])
            }
            from_header = headers.get("from", "")
            subject = headers.get("subject", "")
            date_str = headers.get("date", "")
            snippet = meta.get("snippet", "")

            # Extract email address from "Name <email>" or bare "email"
            sender_email = from_header.lower()
            if "<" in sender_email:
                sender_email = sender_email.split("<")[-1].rstrip(">").strip()

            if sender_email not in lead_emails:
                continue

            # Parse received date
            try:
                internal_date_ms = int(meta.get("internalDate", 0))
                received_at = datetime.fromtimestamp(internal_date_ms / 1000)
            except (ValueError, TypeError):
                received_at = datetime.now()

            sentiment = _classify_sentiment(subject, snippet)

            results.append(ReplyResult(
                contact_email=sender_email,
                message_id=msg_id,
                received_at=received_at,
                subject=subject,
                snippet=snippet[:200],
                sentiment=sentiment,
                sender_account=self.email,
            ))
            logger.info(
                f"GmailReader: reply from {sender_email} "
                f"({sentiment}) received {received_at.strftime('%Y-%m-%d %H:%M')}"
            )

        return results
