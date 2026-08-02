from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import os

from agent.core import run_system
from agent.reminder import send_morning_reminder, send_evening_reminder
from db.client import supabase
from scheduler.weekly_email import send_weekly_reports,test_send_weekly_reports

app = FastAPI()

VERIFY_TOKEN = "my_token"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


# 🔹 STEP 1 — VERIFY WEBHOOK
@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params

    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))

    return {"error": "Verification failed"}


# 🔹 STEP 2 — RECEIVE MESSAGE
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        # 🔥 IGNORE non-message events
        if "messages" not in value:
            return {"status": "ignored"}

        message = value["messages"][0]
        user_number = message["from"]

        # 🔥 HANDLE NON-TEXT
        if "text" not in message:
            send_whatsapp_message(user_number, "Please send text only for now.")
            return {"status": "ok"}

        text = message["text"]["body"]

        print("Incoming:", text)
        print("User:", user_number)

        # 🔥 YOUR SYSTEM
        result = run_system(user_number, text)

        message_text = result.get("output", "Something went wrong")

        if not isinstance(message_text, str) or not message_text.strip():
            message_text = "Something went wrong"

        send_whatsapp_message(user_number, message_text)

    except Exception as e:
        print("ERROR:", e)

    return JSONResponse(content={"status": "ok"})


# 🔹 STEP 3 — SEND MESSAGE
def send_whatsapp_message(to, message):
    if not to:
        print("❌ Missing phone number")
        return

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": str(message)
        }
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        print("SEND STATUS:", res.text)
    except Exception as e:
        print("SEND ERROR:", e)


# 🔹 STEP 4 — REMINDER API
@app.post("/send-reminder")
def send_reminder(data: dict):
    type_ = data.get("type")

    if type_ not in ["morning", "evening"]:
        return {"error": "Invalid type. Use 'morning' or 'evening'"}

    res = supabase.table("users").select("*").execute()
    users = res.data or []

    sent = 0

    for user in users:
        number = user.get("whatsapp_id")

        if not number:
            continue

        if type_ == "morning":
            msg = send_morning_reminder(user)
        else:
            msg = send_evening_reminder(user)

        send_whatsapp_message(number, msg)
        sent += 1

    return {
        "status": "done",
        "type": type_,
        "users_count": len(users),
        "sent": sent
    }


@app.post("/send-inactivity-reminders")
def trigger_inactivity():
    print("🚀 Inactivity reminder endpoint called", flush=True)

    from agent.reminder import send_inactivity_reminder

    try:
        result = send_inactivity_reminder()

        print("✅ Function completed:", result, flush=True)

        return result

    except Exception as e:
        print("❌ ERROR:", str(e), flush=True)
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/send-weekly-reports")

def weekly():

    send_weekly_reports()

    return {"status": "done"}


@app.get("/test-email")
async def test_email():

    result = test_send_weekly_reports(
        "vihandu.wan@gmail.com",
        "Vihandu",
        """
        🚀 EveryRupee Test Email

        This is a test email sent from Railway.

        Total spending: Rs. 25,000
        Top category: Food

        Keep tracking your money!
        """
    )

    return {
        "success": result
    }

@app.post("/notify-upgrade")
async def notify_upgrade():
    users = [
        "94707559308",
    ]

    message = (
        "📢 EveryRupee Update\n\n"
        "We've made a small change to how you add transactions to improve accuracy.\n\n"
        "📝 New format:\n"
        "Expense: 100 food\n"
        "Income: 50000 salary\n\n"
        "Simply enter the amount first, followed by the category.\n\n"
        "Examples:\n"
        "• 350 transport\n"
        "• 1200 groceries\n"
        "• 50000 salary\n"
        "• 15000 freelance\n\n"
        "This new format helps EveryRupee record your transactions faster and more accurately.\n\n"
        "Thanks for being an early tester! 😊"
    )

    for phone in users:
        send_whatsapp_message(phone, message)

    return {"success": True}