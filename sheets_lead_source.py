"""
Google Sheets lead store
--------------------------
Single source of truth for leads and their 3-step follow-up status.
Both webhook_server.py (writes new leads) and run_followups.py
(reads/marks follow-ups) use this module.

SETUP
1. Create a Google Sheet with one tab named exactly "Leads" and this
   header row in row 1 (copy-paste these exact column names):

   Name | Phone | Email | Source | Added Date | Call Due | Call Done | WA3 Due | WA3 Done | WA7 Due | WA7 Done

2. Create a Google Cloud project (console.cloud.google.com) if you
   don't have one, enable the "Google Sheets API", then create a
   Service Account under IAM & Admin -> Service Accounts. Add a JSON
   key to it and download the file.

3. Open the downloaded JSON, copy the "client_email" value (looks
   like xxxx@xxxx.iam.gserviceaccount.com). Share your Google Sheet
   with that email address, giving it Editor access.

4. Set two environment variables:
     GOOGLE_SHEET_ID              -> the long id in your sheet's URL,
                                      e.g. docs.google.com/spreadsheets/d/<THIS PART>/edit
     GOOGLE_SERVICE_ACCOUNT_JSON  -> the ENTIRE contents of the JSON
                                      key file, pasted as one string

5. pip install gspread google-auth
"""

import os
import json
from datetime import date, timedelta

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
TAB_NAME = "Leads"

HEADERS = [
    "Name", "Phone", "Email", "Source", "Added Date",
    "Call Due", "Call Done", "WA3 Due", "WA3 Done", "WA7 Due", "WA7 Done",
]


def _client():
    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


def _sheet():
    gc = _client()
    return gc.open_by_key(SHEET_ID).worksheet(TAB_NAME)


def add_lead(name: str, phone: str, email: str = "", source: str = ""):
    """Call this the moment a new lead comes in (from webhook_server.py)."""
    ws = _sheet()
    today = date.today()
    row = [
        name, phone, email, source,
        today.isoformat(),
        (today + timedelta(days=1)).isoformat(), "",  # Call due / done
        (today + timedelta(days=3)).isoformat(), "",   # WA3 due / done
        (today + timedelta(days=7)).isoformat(), "",   # WA7 due / done
    ]
    ws.append_row(row)


def get_due_leads() -> list[dict]:
    """
    Returns one entry per lead per due, not-yet-done step:
      {"row": 5, "name": "...", "phone": "...", "step": "call"}
    step is one of: call, whatsapp_day3, whatsapp_day7
    """
    ws = _sheet()
    records = ws.get_all_records()  # list of dicts keyed by the header row
    today = date.today().isoformat()
    due = []
    for i, r in enumerate(records, start=2):  # row 1 is the header
        if r.get("Call Due") and not r.get("Call Done") and r["Call Due"] <= today:
            due.append({"row": i, "name": r["Name"], "phone": r["Phone"], "step": "call"})
        if r.get("WA3 Due") and not r.get("WA3 Done") and r["WA3 Due"] <= today:
            due.append({"row": i, "name": r["Name"], "phone": r["Phone"], "step": "whatsapp_day3"})
        if r.get("WA7 Due") and not r.get("WA7 Done") and r["WA7 Due"] <= today:
            due.append({"row": i, "name": r["Name"], "phone": r["Phone"], "step": "whatsapp_day7"})
    return due


def mark_done(row: int, step: str):
    ws = _sheet()
    today = date.today().isoformat()
    col = {"call": "Call Done", "whatsapp_day3": "WA3 Done", "whatsapp_day7": "WA7 Done"}[step]
    col_index = HEADERS.index(col) + 1
    ws.update_cell(row, col_index, today)
