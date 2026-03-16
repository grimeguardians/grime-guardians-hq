"""
Gmail OAuth Setup — run this ONCE per Gmail account to get a refresh token.
Uses a localhost redirect (replaces deprecated OOB flow).

Usage:
    python3 src/tools/gmail_oauth_setup.py

Requirements:
    - GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be in .env
    - http://localhost:8080 must be in your OAuth client's authorized redirect URIs
      (Google Cloud Console → APIs & Services → Credentials → your OAuth client)

After running for both accounts, update on server:
    GMAIL_ACCOUNT_1_REFRESH_TOKEN=<token for brandonr@grimeguardians.com>
    GMAIL_ACCOUNT_2_REFRESH_TOKEN=<token for grimeguardianscleaning@gmail.com>
"""

import json
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv
load_dotenv()

from src.config.settings import get_settings
settings = get_settings()

SCOPES = " ".join([
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
])
AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost:8080"

# Shared storage for the auth code caught by the local server
_auth_code: dict = {}


class _CallbackHandler(BaseHTTPRequestHandler):
    """Catches the OAuth redirect and extracts the auth code."""

    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params:
            _auth_code["value"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family:sans-serif;padding:40px">
                <h2>&#10003; Authorization successful!</h2>
                <p>You can close this tab and return to the terminal.</p>
                </body></html>
            """)
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body>Error: {error}</body></html>".encode())

    def log_message(self, format, *args):
        pass  # suppress server request logs


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
        "prompt": "consent",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("\n" + "=" * 60)
    print("Opening browser for Google sign-in...")
    print("Sign in with the Gmail account you want to authorize.")
    print("=" * 60 + "\n")

    webbrowser.open(url)

    # Start local server and wait for the redirect
    server = HTTPServer(("localhost", 8080), _CallbackHandler)
    print("Waiting for Google to redirect back... (do not close this terminal)\n")
    server.handle_request()  # handles exactly one request then stops

    code = _auth_code.get("value")
    if not code:
        print("❌ No authorization code received.")
        sys.exit(1)

    # Exchange auth code for tokens
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
        print("❌ No refresh_token returned. Try revoking access at")
        print("   https://myaccount.google.com/permissions and running again.")
        sys.exit(1)

    print("=" * 60)
    print("✅ Success! Copy the token below and update your server .env:\n")
    print(f"GMAIL_ACCOUNT_X_REFRESH_TOKEN={refresh_token}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    get_refresh_token()
