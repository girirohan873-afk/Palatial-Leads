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

    try:
        save_lead(lead)
    except Exception as e:
        return jsonify({"failed_step": "google_sheet", "error": type(e).__name__, "detail": str(e)[:300]}), 500

    try:
        on_new_lead(lead)  # sends the instant WhatsApp
    except Exception as e:
        return jsonify({"failed_step": "twilio_whatsapp", "error": type(e).__name__, "detail": str(e)[:300]}), 500

    return jsonify({"status": "ok", "lead": lead}), 200


@app.route("/", methods=["GET", "HEAD"])
def health():
    return "Palatial Leads webhook is running", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
