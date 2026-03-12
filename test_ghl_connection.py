"""
GHL Connection Test
Run with: python test_ghl_connection.py

Verifies:
1. Auth + location lookup
2. All 3 calendars (today's appointments)
3. Contact search
4. Conversations (for Emma/CXO)
"""

import asyncio
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()


def _load_direct(rel_path: str):
    """Load a module by file path, bypassing package __init__.py chains."""
    full = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(rel_path.replace("/", ".").replace(".py", ""), full)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Load settings first (no problematic deps)
settings_mod = _load_direct("src/config/settings.py")
GHL_CALENDARS = settings_mod.GHL_CALENDARS

# Load GHL integration directly (skips discord/db imports in __init__.py)
ghl_mod = _load_direct("src/integrations/gohighlevel_integration.py")
GoHighLevelIntegration = ghl_mod.GoHighLevelIntegration


async def main():
    print("\n" + "=" * 60)
    print("  GHL v2 Connection Test — Grime Guardians")
    print("=" * 60)

    async with GoHighLevelIntegration() as ghl:

        # ── 1. Location ──────────────────────────────────────────────
        print("\n[1] Location lookup...")
        loc = await ghl._request("GET", f"/locations/{ghl.location_id}")
        if "error" in loc:
            print(f"  ❌ FAILED: {loc['error']}")
            print("     → Check HIGHLEVEL_API_KEY and HIGHLEVEL_LOCATION_ID in .env")
        else:
            name = loc.get("location", loc).get("name", "Unknown")
            print(f"  ✅ Location: {name}")

        # ── 2. Calendars ─────────────────────────────────────────────
        print(f"\n[2] Calendar check ({len(GHL_CALENDARS)} calendars configured)...")
        for key, cal in GHL_CALENDARS.items():
            print(f"  Querying '{cal['name']}' (ID: {cal['id']})...")
            apts = await ghl.get_todays_schedule()
            # Already logged per-calendar inside get_todays_schedule; just show total
            break  # get_todays_schedule queries all calendars in one call

        print("\n  Fetching today's schedule across all calendars...")
        today_apts = await ghl.get_todays_schedule()
        if today_apts:
            print(f"  ✅ {len(today_apts)} appointment(s) today:")
            for apt in today_apts:
                print(f"     • {apt.start_time.strftime('%I:%M %p')} — {apt.title} | {apt.contact_name} | {apt.calendar_name}")
        else:
            print("  ℹ️  No appointments today (calendar accessible, just empty)")

        # ── 3. Contacts ──────────────────────────────────────────────
        print("\n[3] Contact search...")
        contacts = await ghl.search_contacts(query="a")
        if contacts:
            print(f"  ✅ {len(contacts)} contact(s) returned (sample query)")
            print(f"     First: {contacts[0].name} | {contacts[0].phone}")
        else:
            print("  ⚠️  No contacts returned — check HIGHLEVEL_LOCATION_ID or API scopes")

        # ── 4. Conversations ─────────────────────────────────────────
        print("\n[4] Conversations (for Emma/CXO)...")
        convs = await ghl.get_conversations(limit=5)
        if convs:
            print(f"  ✅ {len(convs)} conversation(s) fetched")
            for c in convs[:3]:
                print(f"     • {c.contact_name} [{c.type}] — \"{c.last_message[:60]}\"")
        else:
            print("  ⚠️  No conversations returned")

        # ── Summary ──────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  Done. If location + calendar show ✅, Ava is connected.")
        print("  If you see ❌, check your API key / OAuth token in .env")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
