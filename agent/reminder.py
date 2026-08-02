from datetime import datetime, timedelta
from db.client import supabase


def send_morning_reminder(user):
    name = user.get("name") or "there"
    msg = (
        f"🌅 Good morning {name} 👋\n\n"
        "Every rupee you track today builds your future 💰\n"
        "Don’t skip it."
    )
    return msg


def send_evening_reminder(user):
    name = user.get("name") or "there"
    msg = (
        f"🌙 Good evening {name} 👋\n\n"
        "Take a minute to log today’s expenses 💰\n"
        "Your future self will thank you."
    )
    return msg


from datetime import datetime, timedelta, timezone

def send_inactivity_reminder():
    """Send inactivity reminder only to users still inside the 24h WhatsApp window"""
    
    now = datetime.now(timezone.utc)
    
    # === Adjust these two for testing / production ===
    min_inactive = now - timedelta(hours=10)   # last message older than 1 minute
    window_start = now - timedelta(hours=24)    # still inside 24h window
    # ================================================

    print("🔍 Looking for inactive users...")
    print(f"   Now: {now.isoformat()}")
    print(f"   Must have messaged after: {window_start.isoformat()}")
    print(f"   Must have messaged before: {min_inactive.isoformat()}")

    res = supabase.table("users").select(
        "whatsapp_id, name, last_message_time, status"
    ).eq("status", "active").execute()

    users = res.data or []
    print(f"📋 Found {len(users)} active users")

    sent = 0

    for user in users:
        whatsapp_id = user.get("whatsapp_id")
        name = user.get("name", "there")

        if not whatsapp_id:
            print(f"⏭️  Skip {name}: no whatsapp_id")
            continue

        last_msg = user.get("last_message_time")
        if not last_msg:
            print(f"⏭️  Skip {name}: no last_message_time")
            continue

        try:
            last_msg_clean = last_msg.replace("Z", "+00:00")
            last_dt = datetime.fromisoformat(last_msg_clean)

            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)

            # Must still be inside 24h WhatsApp window
            if last_dt < window_start:
                print(f"⏭️  Skip {name}: last message too old ({last_dt})")
                continue

            # Must be inactive for at least 1 minute
            if last_dt > min_inactive:
                print(f"⏭️  Skip {name}: messaged too recently ({last_dt})")
                continue

        except Exception as e:
            print(f"⏭️  Skip {name}: bad last_message_time → {e}")
            continue

        # User passed all checks → send reminder
        msg = f"""👋 Hey {name}!

It's been a while since your last transaction. 
Don’t break the streak! 💪

Send your expense like:
• "Spent 150 on petrol"
• "Earned 5000 salary"

I'm here to help track every rupee."""

        from agent.core import send_whatsapp_message
        if send_whatsapp_message(whatsapp_id, msg):
            sent += 1
            print(f"📤 Sent to {name} ({whatsapp_id})")
        else:
            print(f"❌ Failed to send to {name}")

    print(f"✅ Inactivity reminders sent: {sent}")
    return {"status": "done", "sent": sent}

def test_inactivity_reminder_on_number(whatsapp_id: str):
    """Force send inactivity reminder to one specific number"""
    msg = """👋 Test Inactivity Reminder

This is a test reminder.

It's been a while since your last transaction. 
Don’t break the streak! 💪

Send any expense like:
• "Spent 150 on petrol"
• "Earned 5000 salary"

I'm here to help track every rupee."""

    from agent.core import send_whatsapp_message
    success = send_whatsapp_message(whatsapp_id, msg)
    
    print(f"Test reminder sent to {whatsapp_id}: {'✅ Success' if success else '❌ Failed'}")
    return success