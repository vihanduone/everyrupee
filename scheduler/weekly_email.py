from db.client import supabase

from reports.weekly_report import build_weekly_report

from services.email import send_email


def send_weekly_reports():

    users = (
        supabase.table("users")
        .select("*")
        .eq("status", "approved")
        .execute()
    ).data

    for user in users:

        email = user.get("email")

        if not email:

            continue

        html = build_weekly_report(user)

        send_email(

            email,

            "📊 Your Weekly EveryRupee Report",

            html

        )
        print("email send ", email)

    print("Finished.")


def test_send_weekly_reports(
    user_email,
    user_name,
    insight
):

    try:
        response = resend.Emails.send(
            {
                "from": FROM_EMAIL,
                "to": [user_email],
                "subject": "Your Weekly Expense Insight 📊",
                "html": f"""
                <h2>Hello {user_name} 👋</h2>

                <p>{insight}</p>

                <br>

                <p>
                EveryRupee Team 🚀
                </p>
                """
            }
        )

        print("Resend response:", response)

        return True

    except Exception as e:
        print("Resend error:", e)
        return False