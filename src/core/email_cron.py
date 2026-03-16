"""
Email Cron — runs Dean's outreach campaign once per business day.
Fires at a configurable time (default 9:15am CT), Monday–Friday only.
Runs inside the existing asyncio event loop alongside the Discord bots.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..agents.dean_email_campaign import DeanEmailCampaign

logger = logging.getLogger(__name__)

CENTRAL = ZoneInfo("America/Chicago")

# Time of day to fire the campaign (24h, Central Time)
SEND_HOUR = 9
SEND_MINUTE = 15


def _next_run_at() -> datetime:
    """
    Return the next datetime (Central) to run the campaign.
    Always a weekday at SEND_HOUR:SEND_MINUTE. If we're past today's window,
    advance to tomorrow (and skip over weekends).
    """
    now = datetime.now(CENTRAL)
    candidate = now.replace(hour=SEND_HOUR, minute=SEND_MINUTE, second=0, microsecond=0)

    # If today's window has passed, start from tomorrow
    if now >= candidate:
        candidate += timedelta(days=1)

    # Advance past weekends (Monday=0 … Sunday=6)
    while candidate.weekday() >= 5:  # Saturday or Sunday
        candidate += timedelta(days=1)

    return candidate


async def run_email_cron() -> None:
    """
    Long-running coroutine. Sleeps until the next send window,
    fires the campaign, then loops. Add this to asyncio.gather in run_bot.py.
    """
    campaign = DeanEmailCampaign()
    logger.info("Email cron started.")

    while True:
        next_run = _next_run_at()
        now = datetime.now(CENTRAL)
        sleep_seconds = (next_run - now).total_seconds()

        logger.info(
            f"Email cron: next batch at {next_run.strftime('%A %b %d %I:%M %p CT')} "
            f"(sleeping {sleep_seconds / 3600:.1f}h)"
        )
        await asyncio.sleep(sleep_seconds)

        logger.info("Email cron: starting daily outreach batch.")
        try:
            stats = await campaign.run_batch()
            logger.info(f"Email cron: batch done — {stats}")
        except Exception as e:
            logger.error(f"Email cron: batch failed — {e}", exc_info=True)
