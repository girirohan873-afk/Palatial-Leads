"""
Daily follow-up runner
-----------------------
Run this once a day (via the GitHub Actions workflow already set up,
or any cron). It reads the Google Sheet for leads due today, sends
the right message or call, and marks each step done in the sheet.
"""

import os

from twilio_lead_followup import make_call, send_whatsapp
from sheets_lead_source import get_due_leads, mark_done

# A TwiML Bin URL for the day-1 call script. Create one free at
# twilio.com/console -> TwiML Bins, e.g.:
# <Response><Say>Hi, this is Palatial Realtors following up on your enquiry...</Say></Response>
TWIML_URL = os.environ.get("TWILIO_FOLLOWUP_TWIML_URL", "")


def main():
    due = get_due_leads()
    if not due:
        print("No follow-ups due today.")
        return

    for lead in due:
        if lead["step"] == "call":
            make_call(lead["phone"], TWIML_URL)
        elif lead["step"] == "whatsapp_day3":
            send_whatsapp(
                lead["phone"],
                f"Hi {lead['name']}, just checking in — still exploring options? "
                f"Happy to share more listings or set up a site visit.",
            )
        elif lead["step"] == "whatsapp_day7":
            send_whatsapp(
                lead["phone"],
                f"Hi {lead['name']}, following up one last time on your enquiry — "
                f"let us know if you'd like to continue, or we'll pause outreach for now.",
            )
        mark_done(lead["row"], lead["step"])
        print(f"Processed '{lead['step']}' for {lead['name']}")


if __name__ == "__main__":
    main()
