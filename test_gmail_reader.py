"""
Quick test — confirms GmailReader can authenticate and read both inboxes.
Prints the last 3 messages from each account (sender, subject, snippet).
Usage: python test_gmail_reader.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

import aiohttp
from src.config.settings import get_settings
from src.integrations.gmail_reader import GmailReader

PREVIEW_COUNT = 3


async def preview_inbox(reader: GmailReader, session: aiohttp.ClientSession):
    print(f"\n{'=' * 55}")
    print(f"Account: {reader.email}")
    print(f"{'=' * 55}")

    try:
        message_ids = await reader._list_message_ids(session, since_days=30)
        print(f"Total inbox messages (last 30 days): {len(message_ids)}")

        for msg_id in message_ids[:PREVIEW_COUNT]:
            meta = await reader._get_message_meta(session, msg_id)
            if not meta:
                continue

            headers = {
                h["name"].lower(): h["value"]
                for h in meta.get("payload", {}).get("headers", [])
            }
            from_h = headers.get("from", "(unknown)")
            subject = headers.get("subject", "(no subject)")
            snippet = meta.get("snippet", "")[:100]

            import datetime
            ts = int(meta.get("internalDate", 0)) / 1000
            date_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

            print(f"\n  [{date_str}]")
            print(f"  From:    {from_h}")
            print(f"  Subject: {subject}")
            print(f"  Snippet: {snippet}...")

        print(f"\n✅ {reader.email} — reader confirmed working.")

    except Exception as e:
        print(f"\n❌ Failed for {reader.email}: {e}")


async def main():
    settings = get_settings()
    readers = []

    if settings.gmail_account_1_email and settings.gmail_account_1_refresh_token:
        readers.append(GmailReader(
            email=settings.gmail_account_1_email,
            refresh_token=settings.gmail_account_1_refresh_token,
        ))
    if settings.gmail_account_2_email and settings.gmail_account_2_refresh_token:
        readers.append(GmailReader(
            email=settings.gmail_account_2_email,
            refresh_token=settings.gmail_account_2_refresh_token,
        ))

    if not readers:
        print("❌ No Gmail accounts configured in .env")
        return

    async with aiohttp.ClientSession() as session:
        for reader in readers:
            await preview_inbox(reader, session)

    print("\nDone.")


asyncio.run(main())
