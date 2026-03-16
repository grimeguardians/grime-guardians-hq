"""Quick test — confirms service account can read the GG leads sheet."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv; load_dotenv()

import json
import urllib.request
from google.oauth2 import service_account
from google.auth.transport.requests import Request

SPREADSHEET_ID = "1HHH4A-jJOeoO1zztc2JoVMVPCGo-3iXLM5drOxmLoNw"
RANGE = "Contacts!A1:R5"
SA_FILE = "/opt/grime-guardians/service_account.json"

creds = service_account.Credentials.from_service_account_file(
    SA_FILE,
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
creds.refresh(Request())

url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{RANGE}"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {creds.token}"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

rows = data.get("values", [])
print(f"✅ Sheet access confirmed. Found {len(rows)} rows.")
print(f"Headers: {rows[0] if rows else 'none'}")
print(f"First contact: {rows[1] if len(rows) > 1 else 'none'}")
