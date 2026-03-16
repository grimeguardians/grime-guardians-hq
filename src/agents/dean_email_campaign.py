"""
Dean — Email Outreach Campaign
Reads leads from Google Sheets, sends personalized plain-text emails
from two Gmail accounts, and writes tracking data back to the sheet.

Cadence:
  Day 1  — Initial outreach (status: cold)
  Day 2  — The Bump (1 day after Day 1, no reply)
  Day 7  — Door Slam (7 days after Day 1, no reply)
  Day 8+ — Move to Recycle Bin (status: recycled) — no more emails
  Day 90+ — Drip reactivation (every 60-90 days for recycled contacts)
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import aiohttp

from ..config.settings import get_settings
from ..integrations.gmail_sender import GmailSender
from ..integrations.gmail_reader import GmailReader
from ..integrations.google_sheets import GoogleSheetsClient, SheetContact
from ..utils.time_utils import now_ct

logger = logging.getLogger(__name__)
settings = get_settings()

# Delay range between sends (seconds) — human-like pacing
SEND_DELAY_MIN = 180   # 3 minutes
SEND_DELAY_MAX = 480   # 8 minutes

# Days between sequence steps (from Day 1 send date)
BUMP_DAYS = 1       # Day 2: Bump fires 1 day after initial
DOOR_SLAM_DAYS = 7  # Day 7: Door Slam fires 7 days after initial
RECYCLE_DAYS = 8    # Day 8: Move to Recycle Bin if still no reply
DRIP_DAYS = 90      # Day 90+: Reactivation drip for recycled contacts


# ─── Avatar Pain Points (per industry, for drip campaign) ──────────────────────

AVATAR_PAIN: Dict[str, str] = {
    "property_manager": "vacancies sitting dirty between tenants",
    "construction": "final inspections held up by a dusty site",
    "realtor": "listings that aren't photo-ready on shoot day",
    "real_estate_developer": "flips delayed from hitting the market",
    "general": "cleaning headaches slowing down your business",
}


# ─── Email Templates ──────────────────────────────────────────────────────────
# Plain text only. No links, no images, no HTML.
# Lowercase subject lines. Single-dash sign-off.
# A/B variants per industry — alternated by contact row index.
# {at_company} renders as " at [Company]" or "" if company unknown.
# {for_company} renders as " for [Company]" or "" if company unknown.

TEMPLATES: Dict[str, Dict[str, Dict[str, str]]] = {

    # ── Day 1: Initial Outreach ──────────────────────────────────────────────

    "property_manager": {
        "A": {
            "subject": "backup vendor{for_company}",
            "body": "Hey {first_name}, would you be opposed to having a backup cleaning vendor on standby for the next time your main crew no-shows{at_company}?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "quick question",
            "body": "Hey {first_name}, are you currently looking to eliminate move-in touch-ups{at_company}?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },

    "construction": {
        "A": {
            "subject": "final inspections",
            "body": "Hey {first_name}, would you be against having a backup cleaning crew on standby for the next time your main team holds up a final inspection?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "walkthroughs{at_company}",
            "body": "Hey {first_name}, are you currently looking to eliminate final walkthrough dust complaints{at_company}?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },

    "realtor": {
        "A": {
            "subject": "picture day",
            "body": "Hey {first_name}, would you be opposed to having a backup cleaning crew on standby the next time a listing isn't photo-ready?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "new listings",
            "body": "Hey {first_name}, are you currently looking to get your new listings photo-ready?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },

    "real_estate_developer": {
        "A": {
            "subject": "delayed flips",
            "body": "Hey {first_name}, would you be opposed to having a backup turnover crew on standby for the next time your main guys delay a flip hitting the market?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "market-ready",
            "body": "Hey {first_name}, are you currently looking to get your latest flip market-ready?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },

    "general": {
        "A": {
            "subject": "quick question",
            "body": "Hey {first_name}, would you be opposed to having a reliable backup cleaning crew on standby in the Twin Cities?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "twin cities cleaning",
            "body": "Hey {first_name}, are you currently looking for a reliable cleaning crew in the Twin Cities?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },

    # ── Day 2: The Bump ──────────────────────────────────────────────────────
    # Same subject as Day 1 (re: prefix), floats the thread, under 15 words.

    "followup_2": {
        "A": {
            "subject": "re: {original_subject}",
            "body": "Hey {first_name}, just floating this back to the top.\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "re: {original_subject}",
            "body": "Hey {first_name}, wanted to make sure this didn't get buried.\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },

    # ── Day 7: The Door Slam ─────────────────────────────────────────────────
    # Takes the offer away. Triggers loss aversion. Closes the loop.

    "followup_3": {
        "A": {
            "subject": "re: {original_subject}",
            "body": "Hey {first_name}, I'll assume the timing isn't right and take you off my list. If you ever need a reliable crew on short notice, we're here.\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "re: {original_subject}",
            "body": "Hey {first_name}, no worries — I won't keep bugging you. If {avatar_pain} ever becomes a problem worth solving, feel free to reach back out.\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },

    # ── Day 90+: Drip Reactivation ────────────────────────────────────────────
    # Alternates Value Drop (A) and 9-Word Check-In (B) every 60-90 days.

    "drip": {
        "A": {
            "subject": "re: {original_subject}",
            "body": "Hey {first_name}, quick update — we've been handling {avatar_pain} for a few clients in the area. If that's ever on your radar, I'd be happy to put together something fast.\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
        "B": {
            "subject": "re: {original_subject}",
            "body": "Hey {first_name}, are you still dealing with {avatar_pain}?\n\n- Brandon\nTo opt out, reply \"unsubscribe\"",
        },
    },
}


def _ab_variant(contact: SheetContact) -> str:
    """Alternate A/B by row index — even rows get A, odd get B."""
    return "A" if contact.row_index % 2 == 0 else "B"


def _intro_type(contact_type: str) -> str:
    """Return the template group key, falling back to general."""
    return contact_type if contact_type in TEMPLATES else "general"


def _pick_template_and_step(contact: SheetContact) -> Optional[Tuple[str, str, int]]:
    """
    Determine which template group, variant, and step to send.

    Step mapping:
      1 = Day 1 initial outreach
      2 = Day 2 bump (1 day after step 1)
      3 = Day 7 door slam (7 days after step 1)
      4 = Day 90+ drip (recycled contacts, 90+ days since door slam)

    Returns (template_group, variant, step) or None if nothing to send.
    """
    now = now_ct()
    variant = _ab_variant(contact)
    status = contact.status.lower()

    # Step 1 — never emailed, status cold
    if not contact.email_1_date and status == "cold":
        return _intro_type(contact.contact_type), variant, 1

    # Parse email_1_date once for steps 2/3/recycle checks
    day1_sent: Optional[datetime] = None
    if contact.email_1_date:
        try:
            day1_sent = datetime.fromisoformat(contact.email_1_date)
        except ValueError:
            pass

    if day1_sent and not contact.reply_date:
        days_since_day1 = (now - day1_sent).days

        # Step 2 — Bump (1+ day after step 1, no reply, no bump sent yet)
        if not contact.email_2_date and days_since_day1 >= BUMP_DAYS:
            return "followup_2", variant, 2

        # Step 3 — Door Slam (7+ days after step 1, no reply, bump sent, no door slam yet)
        if contact.email_2_date and not contact.email_3_date and days_since_day1 >= DOOR_SLAM_DAYS:
            return "followup_3", variant, 3

    # Drip — recycled contacts 90+ days since door slam
    if status == "recycled" and contact.email_3_date and not contact.reply_date:
        try:
            day3_sent = datetime.fromisoformat(contact.email_3_date)
            if (now - day3_sent).days >= DRIP_DAYS:
                return "drip", variant, 4
        except ValueError:
            pass

    return None


def _should_recycle(contact: SheetContact) -> bool:
    """
    Returns True if contact should be moved to Recycle Bin.
    Condition: Day 1 sent 8+ days ago, no reply, door slam sent.
    """
    if contact.reply_date or contact.status.lower() == "recycled":
        return False
    if not contact.email_3_date:
        return False
    if not contact.email_1_date:
        return False
    try:
        day1_sent = datetime.fromisoformat(contact.email_1_date)
        return (now_ct().replace(tzinfo=None) - day1_sent).days >= RECYCLE_DAYS
    except ValueError:
        return False


def _render(template_group: str, variant: str, contact: SheetContact) -> Tuple[str, str]:
    """Render subject + body for a contact. Returns (subject, body)."""
    t = TEMPLATES[template_group][variant]
    first_name = contact.name.split()[0].title() if contact.name else "there"

    # Company tokens — gracefully empty if unknown
    company = contact.company.strip() if contact.company else ""
    at_company = f" at {company}" if company else ""
    for_company = f" for {company}" if company else ""

    # Avatar pain per contact type
    avatar_pain = AVATAR_PAIN.get(contact.contact_type, AVATAR_PAIN["general"])

    # Original subject for follow-up threading
    intro_group = _intro_type(contact.contact_type)
    intro_variant = _ab_variant(contact)
    original_subject = TEMPLATES[intro_group][intro_variant]["subject"].format(
        first_name=first_name, at_company=at_company, for_company=for_company
    )

    subject = t["subject"].format(
        first_name=first_name,
        at_company=at_company,
        for_company=for_company,
        original_subject=original_subject,
        avatar_pain=avatar_pain,
    )
    body = t["body"].format(
        first_name=first_name,
        at_company=at_company,
        for_company=for_company,
        original_subject=original_subject,
        avatar_pain=avatar_pain,
    )
    return subject, body


class DeanEmailCampaign:
    """
    Orchestrates Dean's email outreach using Google Sheets as source of truth.
    Reads contacts, sends emails with human-like delays, writes tracking back to sheet.
    """

    def __init__(self):
        """Initialize with Gmail accounts and sheet client from settings."""
        self.sheets = GoogleSheetsClient()
        self.accounts: List[GmailSender] = []
        if settings.gmail_account_1_email and settings.gmail_account_1_refresh_token:
            self.accounts.append(GmailSender(
                email=settings.gmail_account_1_email,
                refresh_token=settings.gmail_account_1_refresh_token,
            ))
        if settings.gmail_account_2_email and settings.gmail_account_2_refresh_token:
            self.accounts.append(GmailSender(
                email=settings.gmail_account_2_email,
                refresh_token=settings.gmail_account_2_refresh_token,
            ))
        self.daily_limit = settings.email_daily_limit_per_account

        # Readers mirror accounts 1:1 — same credentials, read-only scope used
        self.readers: List[GmailReader] = []
        if settings.gmail_account_1_email and settings.gmail_account_1_refresh_token:
            self.readers.append(GmailReader(
                email=settings.gmail_account_1_email,
                refresh_token=settings.gmail_account_1_refresh_token,
            ))
        if settings.gmail_account_2_email and settings.gmail_account_2_refresh_token:
            self.readers.append(GmailReader(
                email=settings.gmail_account_2_email,
                refresh_token=settings.gmail_account_2_refresh_token,
            ))

    async def scan_replies(self) -> Dict[str, int]:
        """
        Scan both Gmail inboxes for replies from known leads.
        Updates reply_date + reply_sentiment in the sheet for any matches.
        Returns {"found": N, "positive": N, "negative": N, "neutral": N}.

        Designed to run before run_batch() so overnight replies suppress
        that day's follow-up before it fires.
        """
        if not self.readers:
            return {"found": 0, "positive": 0, "negative": 0, "neutral": 0}

        contacts = self.sheets.read_contacts()
        # Only contacts we've emailed and haven't logged a reply for yet
        pending: Dict[str, SheetContact] = {
            c.email: c
            for c in contacts
            if c.email_1_date and not c.reply_date
        }

        if not pending:
            logger.debug("Reply scan: no pending contacts to check.")
            return {"found": 0, "positive": 0, "negative": 0, "neutral": 0}

        lead_emails = set(pending.keys())
        stats = {"found": 0, "positive": 0, "negative": 0, "neutral": 0}

        async with aiohttp.ClientSession() as session:
            for reader in self.readers:
                replies = await reader.scan_for_replies(session, lead_emails)
                for reply in replies:
                    contact = pending.get(reply.contact_email)
                    if not contact:
                        continue

                    contact.reply_date = reply.received_at.strftime("%Y-%m-%d %H:%M")
                    contact.reply_sentiment = reply.sentiment
                    if reply.sentiment in ("positive", "negative"):
                        contact.status = "replied"

                    try:
                        self.sheets.update_contact(contact)
                        stats["found"] += 1
                        stats[reply.sentiment] += 1
                        logger.info(
                            f"Reply logged: {contact.email} → {reply.sentiment} "
                            f"(via {reply.sender_account})"
                        )
                    except Exception as e:
                        logger.error(f"Sheet reply write-back failed for {contact.email}: {e}")

                    # Remove from pending so a second reader doesn't double-log
                    pending.pop(reply.contact_email, None)
                    lead_emails.discard(reply.contact_email)

        return stats

    async def run_batch(self) -> Dict[str, int]:
        """
        Run today's outreach batch.
        Sends up to daily_limit emails per account, writes results back to sheet.
        Also recycles contacts that hit Day 8+ with no reply.

        Returns:
            {"sent": N, "skipped": N, "failed": N, "recycled": N}
        """
        if not self.accounts:
            logger.warning("Email campaign: no Gmail accounts configured.")
            return {"sent": 0, "skipped": 0, "failed": 0, "recycled": 0}

        contacts = self.sheets.read_contacts()
        to_send: List[Tuple[SheetContact, str, str, int]] = []
        recycled_count = 0

        for contact in contacts:
            # Skip contacts that already replied (handled separately)
            if contact.reply_sentiment.lower() in ("positive", "negative"):
                continue

            # Recycle contacts that hit Day 8 with no reply
            if _should_recycle(contact):
                contact.status = "recycled"
                try:
                    self.sheets.update_contact(contact)
                    recycled_count += 1
                    logger.info(f"Recycled {contact.email} (no reply after door slam)")
                except Exception as e:
                    logger.error(f"Sheet recycle failed for {contact.email}: {e}")
                continue

            result = _pick_template_and_step(contact)
            if result:
                template_group, variant, step = result
                to_send.append((contact, template_group, variant, step))

        total_limit = self.daily_limit * len(self.accounts)
        to_send = to_send[:total_limit]

        if not to_send:
            logger.info("Email campaign: no contacts to send today.")
            return {"sent": 0, "skipped": len(contacts), "failed": 0, "recycled": recycled_count}

        stats: Dict[str, int] = {"sent": 0, "skipped": 0, "failed": 0, "recycled": recycled_count}
        account_counts = {a.email: 0 for a in self.accounts}

        async with aiohttp.ClientSession() as session:
            for i, (contact, template_group, variant, step) in enumerate(to_send):
                sender = min(self.accounts, key=lambda a: account_counts[a.email])
                if account_counts[sender.email] >= self.daily_limit:
                    stats["skipped"] += 1
                    continue

                subject, body = _render(template_group, variant, contact)
                ok = await sender.send(session, to=contact.email, subject=subject, body=body)

                if ok:
                    now_str = now_ct().strftime("%Y-%m-%d %H:%M")
                    if step == 1:
                        contact.email_1_date = now_str
                        contact.email_1_template = f"{template_group}_{variant}"
                        contact.status = "contacted"
                        contact.sender_account = sender.email
                    elif step == 2:
                        contact.email_2_date = now_str
                    elif step == 3:
                        contact.email_3_date = now_str
                    elif step == 4:
                        # Drip: update email_3_date to reset the 90-day clock
                        contact.email_3_date = now_str

                    try:
                        self.sheets.update_contact(contact)
                    except Exception as e:
                        logger.error(f"Sheet write-back failed for {contact.email}: {e}")

                    account_counts[sender.email] += 1
                    stats["sent"] += 1
                else:
                    stats["failed"] += 1

                if i < len(to_send) - 1:
                    delay = random.randint(SEND_DELAY_MIN, SEND_DELAY_MAX)
                    logger.debug(f"Email campaign: waiting {delay}s before next send.")
                    await asyncio.sleep(delay)

        logger.info(
            f"Email campaign complete: {stats['sent']} sent, "
            f"{stats['skipped']} skipped, {stats['failed']} failed, "
            f"{stats['recycled']} recycled."
        )
        return stats
