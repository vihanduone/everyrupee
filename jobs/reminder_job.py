from datetime import datetime, timedelta
from db.client import supabase
from services.whatsapp import send_template_message


def run_reminders():
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)

    users = supabase.table("users").select("*").execute().data

    print(f"🚀 Running reminder job for {len(users)} users")

    for user in users:
        last = user.get("last_message_time")

        should_send = False

        # CASE 1: Never messaged
        if not last:
            should_send = True

        else:
            try:
                last_time = datetime.fromisoformat(last.replace("Z", "+00:00"))
                if last_time < cutoff:
                    should_send = True
            except Exception:
                should_send = True

        if should_send:
            print(f"📨 Sending reminder to {user['whatsapp_id']}...")

            response = send_template_message(
                user["whatsapp_id"],
                "expense_reminder"
            )

            if response and "messages" in response:
                print(f"✅ Reminder sent successfully to {user['whatsapp_id']}")
                print(f"🆔 Message ID: {response['messages'][0]['id']}")
            else:
                print(f"❌ Failed to send reminder to {user['whatsapp_id']}")
                print(f"Response: {response}")

        else:
            print(f"⏭️ Skipping {user['whatsapp_id']} (active within last 24 hours)")