from db.client import supabase
from db.users import create_user_from_beta
from db.beta import update_beta_field
from services.user_status_service import update_user_status


# =========================
# GET PENDING USERS
# =========================
def get_pending_applications():
    res = (
        supabase.table("beta_applications")
        .select("*")
        .eq("status", "pending")
        .execute()
    )
    return res.data or []


# =========================
# APPROVE USER
# =========================
def approve_user(whatsapp_id: str):

    res = (
        supabase.table("beta_applications")
        .select("*")
        .eq("whatsapp_id", whatsapp_id)
        .execute()
    )

    if not res.data:
        return {"error": "Application not found"}

    app = res.data[0]

    if app.get("status") == "approved":
        return {"message": "Already approved"}

    # 1. update beta table
    update_beta_field(whatsapp_id, "status", "approved")

    # 2. create real user
    user = create_user_from_beta(app)

    # 3. SEND MESSAGE + UPDATE STATUS (SAFE CENTRAL SYSTEM)
    update_user_status(
        user_id=user["id"],
        whatsapp_number=whatsapp_id,
        new_status="approved"
    )

    return {
        "message": "User approved successfully",
        "user": user
    }


# =========================
# REJECT USER
# =========================
def reject_user(whatsapp_id: str):

    # update beta table
    update_beta_field(whatsapp_id, "status", "rejected")

    # send message
    update_user_status(
        user_id=None,
        whatsapp_number=whatsapp_id,
        new_status="rejected"
    )

    return {
        "message": "User rejected"
    }