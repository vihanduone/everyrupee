# services/whatsapp_service.py

import requests

def send_whatsapp_message(to: str, message: str, token: str, phone_id: str):
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()