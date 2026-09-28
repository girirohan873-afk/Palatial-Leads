"""
Daily follow-up runner: reads the Google Sheet, sends what's due, marks it done.
"""

import os

from twilio_lead_followup import make_call, send_whatsapp
from sheets_lead_source import get_due_leads, mark_done

TWIML_URL = os.environ.get("TWILIO_FOLLOWUP_TWIML_URL", "")


def main():
    due = get_due_leads()
    if not due:
        print("No follow-ups due today.")
        return

    for lead in due:
        try:
            if lead["step"] == "call":
                make_call(lead["phone"], TWIML_URL)
            elif lead["step"] == "whatsapp_day3":
                send_whatsapp(lead["phone"], "day3", lead["name"])
            elif lead["step"] == "whatsapp_day7":
                send_whatsapp(lead["phone"], "day7", lead["name"])
            mark_done(lead["row"], lead["step"])
            print(f"Processed '{lead['step']}' for {lead['name']}")
        except Exception as e:
            print(f"FAILED '{lead['step']}' for {lead['name']}: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()

