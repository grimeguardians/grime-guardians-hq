"""
Dean — Email Outreach Campaign
Pulls leads from GHL (tagged 'email-outreach') or a CSV fallback,
sends personalized plain-text emails from two Gmail accounts,
and tracks sent status to prevent duplicate sends.

Sequence:
  Step 1 — Initial outreach
  Step 2 — Follow-up (sent 7 days after step 1 if no reply tracked)
"""

import asyncio
import csv
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from ..config.settings import get_settings
from ..integrations.gohighlevel_integration import GoHighLevelIntegration
from ..integrations.gmail_sender import GmailSender

logger = logging.getLogger(__name__)
settings = get_settings()

# Sent log path — tracks who's been emailed and when
SENT_LOG_PATH = Path("data/email_sent_log.json")
# CSV fallback for contacts not in GHL
CSV_LEADS_PATH = Path("data/email_leads.csv")

# Delay range between sends (seconds) — looks human, avoids bulk flags
SEND_DELAY_MIN = 180   # 3 minutes
SEND_DELAY_MAX = 480   # 8 minutes


@dataclass
class OutreachContact:
    name: str
    email: str
    company: str = ""
    contact_type: str = "general"  # property_manager | realtor | general
    ghl_id: str = ""


# ─── Email Templates ──────────────────────────────────────────────────────────
# Plain text only. Short. Personalized. No "click here", no images, no links.
# Subject lines and bodies are tuned to avoid spam filters.

TEMPLATES: Dict[str, Dict[str, str]] = {

    "property_manager_intro": {
        "subject": "Faster unit turnovers — Twin Cities",
        "body": """\
Hi {first_name},

Quick question — what does a slow turnover cost you per unit in lost rent?

We're Grime Guardians, a premium cleaning service in the Twin Cities. We work with property managers to get units show-ready fast after move-out — thorough clean, inside appliances, photo-ready results.

Our B2B rates: Studio $399 | 1bd/1ba $499 | 2bd/2ba $599 | 3bd/2ba $699.
No contracts. We show up when you need us.

Worth a 10-minute call to see if we're a fit for {company_or_your} portfolio?

— Dean
Grime Guardians | grimeguardians.com
To opt out of these emails, reply "unsubscribe".""",
    },

    "realtor_intro": {
        "subject": "Move-out cleans that get listings photo-ready",
        "body": """\
Hi {first_name},

Listings sell faster when they look like they've never been lived in.

I'm Dean with Grime Guardians — we specialize in move-out cleans for Twin Cities realtors. Our Elite Listing Polish ($549–$749) gets properties camera-ready: inside appliances, baseboards, windows, the works.

We've helped agents in Eagan, Edina, and Eden Prairie close faster by eliminating the "it needs a deep clean" buyer objection before it's ever raised.

Is this something you'd want available for your next listing?

— Dean
Grime Guardians | grimeguardians.com
To opt out, reply "unsubscribe".""",
    },

    "general_intro": {
        "subject": "Professional cleaning in {area}",
        "body": """\
Hi {first_name},

We're Grime Guardians — a premium cleaning service serving the Twin Cities. BBB-accredited, 70+ five-star Google reviews, fully insured.

For first-time clients we offer an Elite Home Reset: a deep, top-to-bottom clean at a flat rate ($299–$549 depending on size) with no recurring obligation.

Most clients book once to see if we're a fit — then stay for years.

Would you be open to a quick quote?

— Dean
Grime Guardians | grimeguardians.com
To opt out, reply "unsubscribe".""",
    },

    "followup": {
        "subject": "Re: {original_subject}",
        "body": """\
Hi {first_name},

Just circling back on my last note — wanted to make sure it didn't get buried.

No pressure at all. If timing isn't right or you're already covered, totally understand. Just reply and I'll take you off my list.

If you've been curious and haven't had a chance to respond — happy to answer any questions or put together a quick quote.

— Dean
Grime Guardians
To opt out, reply "unsubscribe".""",
    },
}


def _load_sent_log() -> Dict:
    """Load the sent log from disk."""
    if SENT_LOG_PATH.exists():
        try:
            return json.loads(SENT_LOG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_sent_log(log: Dict) -> None:
    """Persist the sent log to disk."""
    SENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SENT_LOG_PATH.write_text(json.dumps(log, indent=2, default=str))


def _load_csv_contacts() -> List[OutreachContact]:
    """Load contacts from CSV fallback. Expected columns: name, email, company, contact_type."""
    if not CSV_LEADS_PATH.exists():
        return []
    contacts = []
    try:
        with open(CSV_LEADS_PATH, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email", "").strip()
                if not email:
                    continue
                contacts.append(OutreachContact(
                    name=row.get("name", "").strip(),
                    email=email.lower(),
                    company=row.get("company", "").strip(),
                    contact_type=row.get("contact_type", "general").strip(),
                ))
    except Exception as e:
        logger.error(f"CSV load error: {e}")
    return contacts


def _pick_template(contact: OutreachContact, step: int) -> str:
    """Select the right template key based on contact type and sequence step."""
    if step == 2:
        return "followup"
    if contact.contact_type == "property_manager":
        return "property_manager_intro"
    if contact.contact_type == "realtor":
        return "realtor_intro"
    return "general_intro"


def _render(template_key: str, contact: OutreachContact) -> tuple[str, str]:
    """Render subject + body for a contact. Returns (subject, body)."""
    t = TEMPLATES[template_key]
    first_name = contact.name.split()[0].title() if contact.name else "there"
    company_or_your = contact.company if contact.company else "your"

    # Determine the intro subject for follow-up threading
    intro_key = _pick_template(contact, step=1)
    original_subject = TEMPLATES[intro_key]["subject"].format(
        first_name=first_name,
        company_or_your=company_or_your,
        area="the Twin Cities",
    )

    subject = t["subject"].format(
        first_name=first_name,
        original_subject=original_subject,
        area="the Twin Cities",
    )
    body = t["body"].format(
        first_name=first_name,
        company_or_your=company_or_your,
        area="the Twin Cities",
        original_subject=original_subject,
    )
    return subject, body


class DeanEmailCampaign:
    """
    Orchestrates Dean's email outreach. Pulls contacts from GHL or CSV,
    skips already-emailed contacts, and sends with human-like delays.
    """

    def __init__(self):
        accounts = []
        if settings.gmail_account_1_email and settings.gmail_account_1_refresh_token:
            accounts.append(GmailSender(
                email=settings.gmail_account_1_email,
                refresh_token=settings.gmail_account_1_refresh_token,
            ))
        if settings.gmail_account_2_email and settings.gmail_account_2_refresh_token:
            accounts.append(GmailSender(
                email=settings.gmail_account_2_email,
                refresh_token=settings.gmail_account_2_refresh_token,
            ))
        self.accounts = accounts
        self.daily_limit = settings.email_daily_limit_per_account

    async def _fetch_ghl_contacts(self) -> List[OutreachContact]:
        """Pull contacts from GHL tagged for email outreach."""
        contacts = []
        try:
            async with GoHighLevelIntegration() as ghl:
                results = await ghl.search_contacts(query=settings.email_outreach_tag)
                for c in results:
                    if not c.email:
                        continue
                    ctype = "general"
                    tags = [t.lower() for t in (c.tags or [])]
                    if "property-manager" in tags or "property manager" in tags:
                        ctype = "property_manager"
                    elif "realtor" in tags or "agent" in tags:
                        ctype = "realtor"
                    contacts.append(OutreachContact(
                        name=c.name or "",
                        email=c.email.lower(),
                        company="",
                        contact_type=ctype,
                        ghl_id=c.id,
                    ))
        except Exception as e:
            logger.error(f"GHL contact fetch failed: {e}")
        return contacts

    def _contacts_to_send(
        self,
        all_contacts: List[OutreachContact],
        sent_log: Dict,
    ) -> List[tuple[OutreachContact, int]]:
        """
        Return contacts that should be emailed today and their sequence step.
        Step 1: Never emailed.
        Step 2: Step 1 was sent 7+ days ago and no reply recorded.
        """
        to_send = []
        for contact in all_contacts:
            record = sent_log.get(contact.email)
            if record is None:
                to_send.append((contact, 1))
            elif record.get("sequence_step") == 1 and not record.get("replied"):
                sent_at = datetime.fromisoformat(record["sent_at"])
                if datetime.now() - sent_at >= timedelta(days=7):
                    to_send.append((contact, 2))
            # step 2 already sent — nothing more to do
        return to_send

    async def run_batch(self) -> Dict[str, int]:
        """
        Run today's outreach batch. Sends up to daily_limit emails per account,
        alternating between accounts with random delays.

        Returns:
            {"sent": N, "skipped": N, "failed": N}
        """
        if not self.accounts:
            logger.warning("Email campaign: no Gmail accounts configured.")
            return {"sent": 0, "skipped": 0, "failed": 0}

        sent_log = _load_sent_log()
        ghl_contacts = await self._fetch_ghl_contacts()
        csv_contacts = _load_csv_contacts()

        # Deduplicate by email
        seen = set()
        all_contacts = []
        for c in ghl_contacts + csv_contacts:
            if c.email not in seen:
                seen.add(c.email)
                all_contacts.append(c)

        to_send = self._contacts_to_send(all_contacts, sent_log)
        if not to_send:
            logger.info("Email campaign: no contacts to send today.")
            return {"sent": 0, "skipped": len(all_contacts), "failed": 0}

        # Cap at daily_limit per account total across both accounts
        total_limit = self.daily_limit * len(self.accounts)
        to_send = to_send[:total_limit]

        stats = {"sent": 0, "skipped": 0, "failed": 0}
        account_counts = {a.email: 0 for a in self.accounts}

        async with aiohttp.ClientSession() as session:
            for i, (contact, step) in enumerate(to_send):
                # Pick account with fewest sends today, rotating
                sender = min(self.accounts, key=lambda a: account_counts[a.email])
                if account_counts[sender.email] >= self.daily_limit:
                    stats["skipped"] += 1
                    continue

                template_key = _pick_template(contact, step)
                subject, body = _render(template_key, contact)

                ok = await sender.send(session, to=contact.email, subject=subject, body=body)

                if ok:
                    sent_log[contact.email] = {
                        "sent_at": datetime.now().isoformat(),
                        "template": template_key,
                        "account": sender.email,
                        "sequence_step": step,
                        "replied": False,
                    }
                    account_counts[sender.email] += 1
                    stats["sent"] += 1
                    _save_sent_log(sent_log)
                else:
                    stats["failed"] += 1

                # Human-like delay between sends (skip delay on last send)
                if i < len(to_send) - 1:
                    delay = random.randint(SEND_DELAY_MIN, SEND_DELAY_MAX)
                    logger.debug(f"Email campaign: waiting {delay}s before next send.")
                    await asyncio.sleep(delay)

        logger.info(
            f"Email campaign complete: {stats['sent']} sent, "
            f"{stats['skipped']} skipped, {stats['failed']} failed."
        )
        return stats
