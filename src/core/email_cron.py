"""
Email Cron — two loops running concurrently inside the asyncio event loop:

  reply_scan_loop  — checks both Gmail inboxes every 5 minutes for replies.
                     Updates sheet immediately so follow-ups are suppressed
                     before the next send window.

  send_batch_loop  — fires Dean's outreach batch once per business day
                     at SEND_HOUR:SEND_MINUTE CT (default 9:15am).
                     Runs reply scan one final time right before sending.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ..agents.dean_email_campaign import DeanEmailCampaign

logger = logging.getLogger(__name__)

CENTRAL = ZoneInfo("America/Chicago")

SEND_HOUR = 9
SEND_MINUTE = 15

REPLY_SCAN_INTERVAL_SECONDS = 300  # 5 minutes


def _next_send_at() -> datetime:
    """
    Return the next weekday datetime (CT) to fire the send batch.
    If today's window has passed, advance to next weekday.
    """
    now = datetime.now(CENTRAL)
    candidate = now.replace(
        hour=SEND_HOUR, minute=SEND_MINUTE, second=0, microsecond=0
    )

    if now >= candidate:
        candidate += timedelta(days=1)

    while candidate.weekday() >= 5:  # skip Saturday / Sunday
        candidate += timedelta(days=1)

    return candidate


async def reply_scan_loop(campaign: DeanEmailCampaign) -> None:
    """
    Long-running coroutine. Scans inboxes every 5 minutes.
    Logs results; Discord notification for positive replies is handled
    inside scan_replies() via the campaign's Discord hook.
    """
    logger.info(
        f"Reply scan loop started — checking every "
        f"{REPLY_SCAN_INTERVAL_SECONDS // 60} minutes."
    )
    while True:
        try:
            stats = await campaign.scan_replies()
            if stats["found"] > 0:
                logger.info(f"Reply scan: {stats}")
        except Exception as e:
            logger.error(f"Reply scan failed: {e}", exc_info=True)

        await asyncio.sleep(REPLY_SCAN_INTERVAL_SECONDS)


async def send_batch_loop(campaign: DeanEmailCampaign) -> None:
    """
    Long-running coroutine. Fires the daily send batch on business days.
    Runs a final reply scan immediately before each batch.
    """
    logger.info("Send batch loop started.")

    while True:
        next_run = _next_send_at()
        now = datetime.now(CENTRAL)
        sleep_seconds = (next_run - now).total_seconds()

        logger.info(
            f"Send batch: next run {next_run.strftime('%A %b %d %I:%M %p CT')} "
            f"(sleeping {sleep_seconds / 3600:.1f}h)"
        )
        await asyncio.sleep(sleep_seconds)

        # One final reply scan before sending — catches overnight replies
        logger.info("Send batch: pre-send reply scan.")
        try:
            await campaign.scan_replies()
        except Exception as e:
            logger.warning(f"Pre-send reply scan failed (continuing anyway): {e}")

        logger.info("Send batch: starting daily outreach.")
        try:
            stats = await campaign.run_batch()
            logger.info(f"Send batch complete: {stats}")
        except Exception as e:
            logger.error(f"Send batch failed: {e}", exc_info=True)


async def run_email_cron() -> None:
    """
    Entry point. Launches reply_scan_loop and send_batch_loop concurrently.
    Add this to asyncio.gather() in run_bot.py.
    """
    campaign = DeanEmailCampaign()
    await asyncio.gather(
        reply_scan_loop(campaign),
        send_batch_loop(campaign),
    )
