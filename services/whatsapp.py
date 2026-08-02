import requests
import os
from db.users import get_user_from_db
from services.whatsapp_service import send_whatsapp_message

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


def send_template_message(to, template_name):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"}
        }
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        data = res.json()

        if res.status_code == 200:
            print(f"✅ Reminder sent to {to}")
            print(data)
        else:
            print(f"❌ Failed to send reminder to {to}")
            print(data)

        return data

    except Exception as e:
        print(f"❌ WhatsApp error for {to}: {e}")
        return None
    
def handle_message(whatsapp_number, message):

    user = get_user_from_db(whatsapp_number)

    # 🚫 BLOCK UNAPPROVED USERS
    if not user or user["status"] != "approved":
        send_whatsapp_message(
            whatsapp_number,
            "⏳ You are still waiting for admin approval."
        )
        return