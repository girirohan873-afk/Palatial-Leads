import os
import json
from twilio.rest import Client

ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
VOICE_FROM = os.environ.get("TWILIO_VOICE_FROM", "")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

TEXTS = {
    "instant": "Hi {name}, thanks for your interest with Palatial Realtors! Our team will reach out shortly. Feel free to reply here with any questions.",
    "day3": "Hi {name}, just checking in - still exploring options? Happy to share more listings or set up a site visit.",
    "day7": "Hi {name}, following up one last time on your enquiry - let us know if you'd like to continue, or we'll pause outreach for now.",
}


def send_whatsapp(to_number: str, kind: str, name: str):
    """kind is 'instant', 'day3' or 'day7'. to_number like '+9198XXXXXXXX'."""
    sid = os.environ.get("TWILIO_TEMPLATE_" + kind.upper(), "").strip()
    if sid:
        return client.messages.create(
            from_=WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=sid,
            content_variables=json.dumps({"1": name}),
        )
    return client.messages.create(
        from_=WHATSAPP_FROM,
        to=f"whatsapp:{to_number}",
        body=TEXTS[kind].format(name=name),
    )


def make_call(to_number: str, twiml_url: str):
    return client.calls.create(to=to_number, from_=VOICE_FROM, url=twiml_url)


def on_new_lead(lead: dict):
    send_whatsapp(lead["phone"], "instant", lead["name"])
