from db.client import supabase


def save_feedback(whatsapp_id: str, feedback_text: str):
    """Save user feedback safely"""
    try:
        # Try to update existing user
        res = supabase.table("users").update({
            "feedbacks": feedback_text
        }).eq("whatsapp_id", whatsapp_id).execute()
        
        if res.data:
            return "Thank you for your feedback! 💙"
        else:
            # If no user found, insert as new feedback record (fallback)
            supabase.table("users").insert({
                "whatsapp_id": whatsapp_id,
                "feedbacks": feedback_text
            }).execute()
            return "Thank you for your feedback! 💙"
            
    except Exception as e:
        print("Feedback save error:", e)
        return "Thank you for your feedback! 💙"