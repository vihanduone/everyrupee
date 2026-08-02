def create_user_from_beta(beta_user: dict):
    """Create user safely without requiring 'occupation' column"""
    data = {
        "whatsapp_id": beta_user.get("whatsapp_id"),
        "name": beta_user.get("name"),
        "email": beta_user.get("email"),
        "onboarding_step": "active",
        "last_message_time": datetime.utcnow().isoformat()
    }

    try:
        res = supabase.table("users").insert(data).execute()
        print(f"✅ User created successfully: {beta_user.get('whatsapp_id')}")
        return res.data[0] if res.data else None
    except Exception as e:
        print("User creation error:", str(e))
        # Fallback if 'email' (or another new column) doesn't exist yet
        try:
            minimal = {
                "whatsapp_id": beta_user.get("whatsapp_id"),
                "name": beta_user.get("name")
            }
            res = supabase.table("users").insert(minimal).execute()
            print("⚠️ Minimal user created WITHOUT email — add an 'email' column to users table")
            return res.data[0] if res.data else None
        except Exception as e2:
            print("Minimal user creation also failed:", str(e2))
            return None