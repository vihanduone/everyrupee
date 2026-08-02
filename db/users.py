from datetime import datetime
from database import supabase


def get_or_create_user(beta_user: dict):
    """
    Get existing user by WhatsApp ID.
    If user does not exist, create a new user.
    """

    whatsapp_id = beta_user.get("whatsapp_id")

    if not whatsapp_id:
        print("❌ WhatsApp ID missing")
        return None

    try:
        # Check if user already exists
        res = (
            supabase.table("users")
            .select("*")
            .eq("whatsapp_id", whatsapp_id)
            .execute()
        )

        if res.data:
            print(f"✅ Existing user found: {whatsapp_id}")
            return res.data[0]

    except Exception as e:
        print("User lookup error:", str(e))

    # User does not exist -> create new user
    return create_user_from_beta(beta_user)



def create_user_from_beta(beta_user: dict):
    """
    Create user safely without requiring optional columns.
    """

    data = {
        "whatsapp_id": beta_user.get("whatsapp_id"),
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
            f"✅ User created successfully: {beta_user.get('whatsapp_id')}"
        )

        return res.data[0] if res.data else None


    except Exception as e:
        print("User creation error:", str(e))

        # Fallback if email or new columns do not exist
        try:
            minimal = {
                "whatsapp_id": beta_user.get("whatsapp_id"),
                "name": beta_user.get("name")
            }

            res = (
                supabase.table("users")
                .insert(minimal)
                .execute()
            )

            print(
                "⚠️ Minimal user created WITHOUT optional columns"
            )

            return res.data[0] if res.data else None


        except Exception as e2:
            print(
                "❌ Minimal user creation also failed:",
                str(e2)
            )

            return None