"""
Palatial Realtors — new-lead webhook
-------------------------------------
Point your website form, landing page, or portal integration (Zapier/Make,
if the property portal supports it) at this endpoint's URL as its
"submit" or "webhook" target. The moment a lead posts here, the instant
WhatsApp goes out via twilio_lead_followup.on_new_lead().

SETUP
1. pip install flask twilio
2. Same env vars as twilio_lead_followup.py (TWILIO_ACCOUNT_SID etc.)
3. Run: python webhook_server.py
4. Deploy this somewhere reachable from the internet (Render, Railway,
   a small VPS, etc.) and use that public URL as your form's action /
   webhook target. Locally you can test it with a tool like ngrok.
5. Wire storage: the TODO in save_lead() below is where you'd also
   write the lead into whatever your dashboard reads from (the
   leads-app.html page's own store, a spreadsheet, or your CRM) so
   it shows up there too, not just in Twilio.

EXAMPLE test call (from your terminal, once running):
  curl -X POST http://localhost:5000/new-lead \
    -H "Content-Type: application/json" \
    -d '{"name":"Asha Mehta","phone":"+919812345678","email":"asha@example.com","source":"Website"}'
"""
   import os
from flask import Flask, request, jsonify
from twilio_lead_followup import on_new_lead
from sheets_lead_source import add_lead

app = Flask(__name__)


def save_lead(lead: dict):
    add_lead(lead["name"], lead["phone"], lead.get("email", ""), lead.get("source", ""))


@app.route("/new-lead", methods=["POST"])
def new_lead():
    data = request.get_json(force=True) or {}
    name = data.get("name")
    phone = data.get("phone")  # must be E.164, e.g. +9198XXXXXXXX

    if not name or not phone:
        return jsonify({"error": "name and phone are required"}), 400

    lead = {
        "name": name,
        "phone": phone,
        "email": data.get("email", ""),
        "source": data.get("source", "Website"),
    }

    save_lead(lead)
    on_new_lead(lead)  # sends the instant WhatsApp

    return jsonify({"status": "ok", "lead": lead}), 200


if __name__ == "__main__":
       app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
