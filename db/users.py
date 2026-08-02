from datetime import datetime
from db.client import supabase


# ---------------- GET USER ----------------
def get_user_from_db(whatsapp_id: str):
    """
    Fetch user by WhatsApp ID
    """

    if not whatsapp_id:
        return None

    try:
        res = (
            supabase.table("users")
            .select("*")
            .eq("whatsapp_id", whatsapp_id)
            .execute()
        )

        return res.data[0] if res.data else None

    except Exception as e:
        print("❌ Get user error:", str(e))
        return None



# ---------------- GET OR CREATE ----------------
# Compatible with your existing webhook
def get_or_create_user(whatsapp_id: str):
    """
    Returns:
    user, False  -> user exists
    None, True   -> user needs approval
    """

    user = get_user_from_db(whatsapp_id)

    if user:
        print(f"✅ Existing approved user: {whatsapp_id}")
        return user, False

    print(f"⚠️ User waiting for approval: {whatsapp_id}")
    return None, True



# ---------------- CREATE USER AFTER APPROVAL ----------------
def create_user_from_beta(beta_user: dict):
    """
    Create approved user
    """

    data = {
        "whatsapp_id": beta_user["whatsapp_id"],
        "name": beta_user.get("name"),
        "email": beta_user.get("email"),
        "onboarding_step": "active",
        "last_message_time": datetime.utcnow().isoformat()
    }

    try:
        res = (
            supabase.table("users")
            .insert(data)
            .execute()
        )

        print(
            f"✅ User created: {beta_user['whatsapp_id']}"
        )

        return res.data[0] if res.data else None

    except Exception as e:
        print("❌ User creation error:", str(e))
        return None



# ---------------- UPDATE NAME ----------------
def update_user_name(whatsapp_id: str, name: str):

    supabase.table("users")\
        .update({"name": name})\
        .eq("whatsapp_id", whatsapp_id)\
        .execute()



# ---------------- UPDATE OCCUPATION ----------------
def update_user_occupation(whatsapp_id: str, occupation: str):

    supabase.table("users")\
        .update({"occupation": occupation})\
        .eq("whatsapp_id", whatsapp_id)\
        .execute()



# ---------------- SAVE FEEDBACK ----------------
def put_feedback(whatsapp_id: str, feedback_text: str):

    supabase.table("users")\
        .update({"feedbacks": feedback_text})\
        .eq("whatsapp_id", whatsapp_id)\
        .execute()