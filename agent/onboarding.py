import re

from db.beta import (
    get_beta_application,
    create_beta_application,
    update_beta_step,
    update_beta_field
)

from db.users import create_user_from_beta, get_user_from_db


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# =========================
# QUESTION BANK
# =========================

def get_name_question():
    return {"output": "👋 Welcome to EveryRupee!\n\nWhat's your name?"}


def get_name_error():
    return {"output": "Hmm, that doesn't look like a name 🙂\n\nWhat should I call you?"}


def get_email_question():
    return {
        "output": (
            "📧 What's your email address?\n\n"
            "We'll use it only to send your weekly expense reports."
        )
    }


def get_email_error():
    return {
        "output": (
            "That doesn't look like a valid email 🙁\n\n"
            "Please send a valid email address (e.g. name@example.com)."
        )
    }


def get_activation_error():
    return {
        "output": (
            "⚠️ Something went wrong activating your account.\n\n"
            "Please send any message to try again."
        )
    }


def get_welcome_message():
    return {
        "output": (
            "🎉 You're all set!\n\n"
            "Welcome to EveryRupee 💸\n\n"
            "Start logging expenses like:\n"
            "👉 Food 500\n"
            "👉 Fuel 2000\n\n"
            "Type \"summary\" anytime to see your totals. "
            "Let's build better money habits together 💪"
        )
    }


# =========================
# STEP FLOW ENGINE
# =========================

def start_application(whatsapp_id: str):
    create_beta_application(whatsapp_id)
    return get_name_question()


def process_onboarding(whatsapp_id: str, user_input: str, app: dict):
    step = app.get("step", "name")
    text = user_input.strip()

    # ================= NAME =================
    if step == "name":
        if not text or len(text) < 2:
            return get_name_error()

        update_beta_field(whatsapp_id, "name", text[:100])
        update_beta_step(whatsapp_id, "email")
        return get_email_question()

    # ================= EMAIL =================
    if step == "email":
        email = text.lower()

        if not EMAIL_RE.match(email):
            return get_email_error()

        update_beta_field(whatsapp_id, "email", email)
        update_beta_step(whatsapp_id, "activating")

        fresh_app = get_beta_application(whatsapp_id) or app
        return _activate_user(whatsapp_id, fresh_app)

    # ================= ACTIVATING (retry point) =================
    if step == "activating":
        fresh_app = get_beta_application(whatsapp_id) or app
        return _activate_user(whatsapp_id, fresh_app)

    # ================= COMPLETED (shouldn't normally hit — user exists by now) =================
    if step == "completed":
        return get_welcome_message()

    return {"output": "Something went wrong in onboarding. Please try again."}


# =========================
# ACTIVATION
# =========================

def _activate_user(whatsapp_id: str, app: dict):
    """
    Creates the real user row and marks onboarding complete.
    Idempotent: safe to call more than once in case of retries
    or duplicate/concurrent messages.
    """
    try:
        existing = get_user_from_db(whatsapp_id)
        if existing:
            update_beta_field(whatsapp_id, "status", "converted")
            update_beta_step(whatsapp_id, "completed")
            return get_welcome_message()

        user = create_user_from_beta(app)

        if not user:
            print(f"ACTIVATION FAILED (no row returned): {whatsapp_id}")
            return get_activation_error()

        update_beta_field(whatsapp_id, "status", "converted")
        update_beta_step(whatsapp_id, "completed")
        return get_welcome_message()

    except Exception as e:
        print("ACTIVATION ERROR:", e)
        return get_activation_error()