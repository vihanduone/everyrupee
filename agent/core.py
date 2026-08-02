import json
import time
from datetime import datetime
from db.client import supabase
from db.users import get_or_create_user
from db.beta import get_beta_application, create_beta_application

from memory.conversation import conversation_memory, update_memory
from agent.parser import ai_parse_user_input

from agent.onboarding import (
    start_application,
    process_onboarding
)

from tools.expenses import (
    add_expense,
    get_summary,
    delete_last_transaction,
    add_income
)

from tools.feedback import save_feedback

from agent.chat import generate_general_reply
from agent.reminder import send_inactivity_reminder  # NEW


# =========================
# IN-MEMORY SAFETY LAYERS
# =========================
last_seen = {}  # anti-duplicate

# =========================
# WHATSAPP SENDER (Safe - 24h Window)
# =========================
def send_whatsapp_message(to: str, message: str):
    """Safe sender respecting 24-hour WhatsApp Cloud API window"""
    if not to or not message:
        return False

    import requests
    import os
    from datetime import datetime, timedelta

    # Check 24h window
    try:
        user_check = supabase.table("users").select("last_message_time").eq("whatsapp_id", to).execute()
        if user_check.data:
            last_time = user_check.data[0].get("last_message_time")
            if last_time:
                last_dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                if datetime.utcnow() - last_dt > timedelta(hours=24):
                    print(f"⛔ 24h window closed for {to}")
                    return False
    except:
        pass

    # Send
    url = f"https://graph.facebook.com/v18.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": str(message)}
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        print(f"WhatsApp send to {to}: {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        print("SEND ERROR:", e)
        return False

def is_duplicate(user_id, message):
    key = f"{user_id}:{message}"
    if last_seen.get(key):
        return True
    last_seen[key] = time.time()
    return False


def safe_output(reply):
    if isinstance(reply, dict) and "output" in reply:
        return reply
    return {"output": str(reply)}


# =========================
# WHATSAPP SENDER (24h Window Safe)
# =========================
def send_whatsapp_message(to: str, message: str):
    """Safe sender respecting 24-hour WhatsApp Cloud API window"""
    if not to or not message:
        return False

    # Check if 24h window is open using last_message_time
    try:
        user_check = supabase.table("users").select("last_message_time").eq("whatsapp_id", to).execute()
        if user_check.data:
            last_time = user_check.data[0].get("last_message_time")
            if last_time:
                last_dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                if datetime.utcnow() - last_dt > timedelta(hours=24):
                    print(f"⛔ 24h window closed for {to}")
                    return False
    except:
        pass  # If check fails, still try to send (fail-safe)

    # Send message
    import requests
    import os

    url = f"https://graph.facebook.com/v18.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": str(message)}
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        print(f"WhatsApp send to {to}: {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        print("SEND ERROR:", e)
        return False


# =========================
# MAIN SYSTEM (Unchanged logic + new imports)
# =========================
def run_system(user_id, user_input):

    print("User input:", user_input)

    if not user_input or not user_input.strip():
        return safe_output("Please send a valid message 🙂")

    user_input = user_input.strip()

    if is_duplicate(user_id, user_input):
        return safe_output("⏳ Processing...")

    if user_id not in conversation_memory:
        conversation_memory[user_id] = {
            "history": [],
            "pending": None
        }

    history = conversation_memory[user_id]["history"]

    # =========================================================
    # 1. CHECK ACTIVE USER
    # =========================================================
    user, exists = get_or_create_user(user_id)

    if user:
        return handle_active_user(user, user_input, history)

    # =========================================================
    # 2. CHECK BETA APPLICATION
    # =========================================================
    app = get_beta_application(user_id)

    if not app:
        reply = start_application(user_id)
        update_memory(user_id, user_input, reply)
        conversation_memory[user_id]["history"].append({
            "user": user_input,
            "bot": reply
        })
        return safe_output(reply)

    # =========================================================
    # 3. ONBOARDING FLOW
    # =========================================================
    try:
        reply = process_onboarding(user_id, user_input, app)
    except Exception as e:
        print("ONBOARDING ERROR:", e)
        reply = {"output": "Something went wrong in onboarding. Please try again."}

    update_memory(user_id, user_input, reply)
    conversation_memory[user_id]["history"].append({
        "user": user_input,
        "bot": reply
    })

    return safe_output(reply)


# =========================================================
# ACTIVE USER FLOW (Unchanged)
# =========================================================
def handle_active_user(user, user_input, history):

    user_memory = conversation_memory[user["whatsapp_id"]]
    
    # Update last message time
    supabase.table("users").update({
        "last_message_time": datetime.utcnow().isoformat()
    }).eq("id", user["id"]).execute()

    # ---------------- AI PARSE ----------------
    try:
        decision = ai_parse_user_input(user_input, history[-10:])
    except Exception as e:
        print("AI ERROR:", e)
        decision = {"intent": "unknown", "entity": {}}

    # ---------------- NORMALIZE ----------------
    if isinstance(decision, str):
        try:
            decision = json.loads(decision)
        except:
            return safe_output("Sorry, I didn't understand that.")

    intent = decision.get("intent", "unknown")
    entity = decision.get("entity") or {}

    amount = entity.get("amount")
    category = entity.get("category")
    raw = entity.get("raw")

    # Manual overrides
    lower = user_input.lower()
    if "summary" in lower:
        intent = "get_summary"
    if "undo" in lower or "delete last" in lower:
        intent = "delete_last"
    if "report" in lower:
        intent = "send_report"

    # Followup
    if decision.get("needs_followup"):
        user_memory["pending"] = {"intent": intent, "entity": entity}
        reply = decision.get("question") or "Can you clarify?"
        update_memory(user["whatsapp_id"], user_input, reply)
        return safe_output(reply)

    # Router
    try:
        if intent == "add_expense":
            reply = add_expense(user["id"], amount, category or "general", user_input) if amount else "Please enter a valid amount"
        elif intent == "adding_income":
            reply = add_income(user["id"], amount, category or "income", user_input) if amount else "Please enter a valid amount"
        elif intent == "get_summary":
            reply = get_summary(user["id"])
        elif intent == "delete_last":
            reply = delete_last_transaction(user["id"])
        elif intent == "save_feedback":
            reply = save_feedback(user["whatsapp_id"], raw)
        elif intent == "send_report":
            reply = "Report feature coming soon 🚀"
        else:
            reply = generate_general_reply(user_input, user.get("name"), history)
    except Exception as e:
        print("ROUTER ERROR:", e)
        reply = "Something went wrong. Please try again."

    update_memory(user["whatsapp_id"], user_input, reply)
    return safe_output(reply)