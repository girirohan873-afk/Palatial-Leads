"""
Palatial Realtors — Twilio lead automation
-------------------------------------------
Sends an instant WhatsApp message the moment a lead is added, then
runs the 3-step follow-up sequence (Call -> day 1, WhatsApp -> day 3,
WhatsApp -> day 7).

SETUP
1. pip install twilio
2. Set these environment variables (never hardcode them):
     TWILIO_ACCOUNT_SID
     TWILIO_AUTH_TOKEN
     TWILIO_WHATSAPP_FROM   e.g. "whatsapp:+14155238886" (your approved WA sender)
     TWILIO_VOICE_FROM      e.g. "+14155551234"           (your Twilio voice number)
3. Twilio WhatsApp requires an approved sender + pre-approved message
   templates for the FIRST message to a new contact (24h session
   window rules). Set up a template in the Twilio Console first —
   see https://www.twilio.com/docs/whatsapp/tutorial
4. Run this as a scheduled job (cron / Cloud Scheduler) once a day,
   pointed at whatever stores your lead data (a spreadsheet, your
   CRM, or the leads-app.html dashboard's data if you export it).

This script itself is a template: swap `fetch_due_leads()` for your
real lead source, and `mark_step_done()` for however you track state.
"""

import os
from twilio.rest import Client

ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
VOICE_FROM = os.environ["TWILIO_VOICE_FROM"]

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def send_whatsapp(to_number: str, body: str):
    """to_number like '+9198XXXXXXXX' (E.164, no 'whatsapp:' prefix needed here)."""
    return client.messages.create(
        from_=WHATSAPP_FROM,
        to=f"whatsapp:{to_number}",
        body=body,
    )


def make_call(to_number: str, twiml_url: str):
    """
    twiml_url must return TwiML telling the call what to say/do, e.g. a
    simple <Say> greeting, or a menu that connects to your sales team.
    Twilio's console lets you host a "Studio Flow" and get a URL for this.
    """
    return client.calls.create(
        to=to_number,
        from_=VOICE_FROM,
        url=twiml_url,
    )


def on_new_lead(lead: dict):
    """Call this the instant a lead is captured (webhook, form submit, etc.)"""
    send_whatsapp(
        lead["phone"],
        f"Hi {lead['name']}, thanks for your interest with Palatial Realtors! "
        f"Our team will be in touch shortly. Meanwhile, feel free to reply "
        f"here with any questions.",
    )


def run_daily_followups(due_leads: list[dict], twiml_url: str):
    """
    due_leads: leads whose next follow-up step is due today, each like:
      {"name": "...", "phone": "+91...", "step": "call" | "whatsapp_day3" | "whatsapp_day7"}
    """
    for lead in due_leads:
        if lead["step"] == "call":
            make_call(lead["phone"], twiml_url)
        elif lead["step"] == "whatsapp_day3":
            send_whatsapp(
                lead["phone"],
                f"Hi {lead['name']}, just checking in — still exploring options? "
                f"Happy to share more listings or schedule a site visit.",
            )
        elif lead["step"] == "whatsapp_day7":
            send_whatsapp(
                lead["phone"],
                f"Hi {lead['name']}, following up one last time — let us know "
                f"if you'd like to continue, or we'll pause outreach for now.",
            )
        mark_step_done(lead)


def mark_step_done(lead: dict):
    # TODO: wire this to wherever you track lead state
    # (your CRM, a spreadsheet, or the dashboard's stored data).
    print(f"Marked '{lead['step']}' done for {lead['name']}")


if __name__ == "__main__":
    # Example manual test — replace with your real lead source.
    example_lead = {"name": "Test Lead", "phone": "+919800000000"}
    on_new_lead(example_lead)
