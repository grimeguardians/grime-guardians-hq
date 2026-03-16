"""
Gmail OAuth Setup — run this ONCE per Gmail account to get a refresh token.
The refresh token never expires (unless revoked), so you only need to do this once.

Usage:
    python src/tools/gmail_oauth_setup.py

Requirements:
    - GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be in .env
    - You'll be prompted to open a URL and paste back the auth code

After running for both accounts, add to .env:
    GMAIL_ACCOUNT_1_EMAIL=you@gmail.com
    GMAIL_ACCOUNT_1_REFRESH_TOKEN=<printed below>
    GMAIL_ACCOUNT_2_EMAIL=other@gmail.com
    GMAIL_ACCOUNT_2_REFRESH_TOKEN=<printed below>
"""

import sys
import urllib.parse
import urllib.request
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv
load_dotenv()

from src.config.settings import get_settings
settings = get_settings()

SCOPES = " ".join([
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
])
AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"  # Desktop/manual flow


def get_refresh_token():
    client_id = settings.gmail_client_id
    client_secret = settings.gmail_client_secret

    if not client_id or not client_secret:
        print("❌ GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",  # Forces refresh_token even if previously granted
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("\n" + "=" * 60)
    print("Step 1: Open this URL in a browser and sign in with the Gmail account you want to authorize:")
    print(f"\n{url}\n")
    print("Step 2: After granting access, Google will show you an authorization code.")
    print("=" * 60)

    code = input("\nPaste the authorization code here: ").strip()

    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read())
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")
        sys.exit(1)

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        print("❌ No refresh_token in response. Make sure 'prompt=consent' is in the URL.")
        print(f"Full response: {token_data}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ SUCCESS! Add these to your .env:\n")
    print(f"GMAIL_ACCOUNT_X_EMAIL=<the gmail address you just signed in with>")
    print(f"GMAIL_ACCOUNT_X_REFRESH_TOKEN={refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    get_refresh_token()
