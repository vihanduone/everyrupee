from db.client import supabase
from services.whatsapp_service import send_whatsapp_message


def update_user_status(user_id: str | None, whatsapp_number: str, new_status: str):
    """
    Central place for:
    - updating status
    - sending WhatsApp notification
    """

    # 1. Update users table ONLY if user exists
    if user_id:
        supabase.table("users").update({
            "status": new_status
        }).eq("id", user_id).execute()

    # 2. Always send WhatsApp message
    if new_status == "approved":
        send_whatsapp_message(
            whatsapp_number,
            "🎉 You are approved! You can now use the expense tracker."
        )

    elif new_status == "rejected":
        send_whatsapp_message(
            whatsapp_number,
            "❌ Sorry, your request was not approved."
        )

    elif new_status == "pending":
        send_whatsapp_message(
            whatsapp_number,
            "⏳ Your request is under review."
        )