"""
Quick test — sends one email from Account 1 to a specified address.
Usage: python test_email.py your@personalemail.com
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

import aiohttp
from src.config.settings import get_settings
from src.integrations.gmail_sender import GmailSender

async def main():
    to = sys.argv[1] if len(sys.argv) > 1 else input("Send test email to: ").strip()
    settings = get_settings()

    sender = GmailSender(
        email=settings.gmail_account_1_email,
        refresh_token=settings.gmail_account_1_refresh_token,
    )

    async with aiohttp.ClientSession() as session:
        ok = await sender.send(
            session=session,
            to=to,
            subject="Test — Grime Guardians Email Pipeline",
            body=(
                f"This is a test email from Dean's outreach pipeline.\n\n"
                f"Sent from: {settings.gmail_account_1_email}\n"
                f"If you're reading this, the Gmail integration is working.\n\n"
                f"— Dean\nGrime Guardians"
            ),
        )

    print("✅ Sent successfully!" if ok else "❌ Send failed — check logs above.")

asyncio.run(main())
