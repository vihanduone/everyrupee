from db.client import supabase
from db.users import create_user_from_beta


# ---------------- CREATE APPLICATION ----------------
def create_beta_application(whatsapp_id: str):
    res = (
        supabase.table("beta_applications")
        .insert({
            "whatsapp_id": whatsapp_id,
            "status": "pending",
            "step": "name"
        })
        .execute()
    )
    return res.data[0] if res.data else None


# ---------------- GET APPLICATION ----------------
def get_beta_application(whatsapp_id: str):
    res = (
        supabase.table("beta_applications")
        .select("*")
        .eq("whatsapp_id", whatsapp_id)
        .execute()
    )
    return res.data[0] if res.data else None


# ---------------- UPDATE STEP ----------------
def update_beta_step(whatsapp_id: str, step: str):
    supabase.table("beta_applications")\
        .update({"step": step})\
        .eq("whatsapp_id", whatsapp_id)\
        .execute()


# ---------------- SAVE FIELDS ----------------
def update_beta_field(whatsapp_id: str, field: str, value):
    supabase.table("beta_applications")\
        .update({field: value})\
        .eq("whatsapp_id", whatsapp_id)\
        .execute()


# ---------------- APPROVE USER ----------------
def approve_beta_user(whatsapp_id: str):
    """Approve user and send welcome message"""
    # Update beta status + set approved_at in one query
    supabase.table("beta_applications").update({
        "status": "approved",
        "approved_at": "now()"   # Supabase will handle current timestamp
    }).eq("whatsapp_id", whatsapp_id).execute()

    # Get the application and create user
    app = get_beta_application(whatsapp_id)
    if app:
        create_user_from_beta(app)

        # Send welcome message
        from agent.core import send_whatsapp_message
        welcome_msg = """🎉 Welcome to EveryRupee!

You are now approved! 

You can start tracking expenses right away.

Just send messages like:
• "Spent 250 on food"
• "summary"
• "undo"

Let's build better money habits together 💪"""

        send_whatsapp_message(whatsapp_id, welcome_msg)
        print(f"✅ Approved and welcomed: {whatsapp_id}")
        return True
    else:
        print(f"❌ No beta application found for {whatsapp_id}")
        return False


# ---------------- REJECT USER ----------------
def reject_beta_user(whatsapp_id: str):
    supabase.table("beta_applications")\
        .update({"status": "rejected"})\
        .eq("whatsapp_id", whatsapp_id)\
        .execute()