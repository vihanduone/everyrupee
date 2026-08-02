import os
import resend
import re
import base64

from tools.expenses import generate_monthly_report
from tools.report_generator import generate_excel_report


resend.api_key = os.getenv("RESEND_API_KEY")


def send_email(user_id, to_email):

    print("📧 Sending via Resend:", to_email)

    report_text = generate_monthly_report(user_id)
    file_path = generate_excel_report(user_id)

    if not file_path:
        return "No data to generate report"

    try:
        # 🔥 READ FILE
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        print("EMAIL 1 - file loaded")

        # 🔥 CONVERT TO BASE64 (IMPORTANT FIX)
        file_base64 = base64.b64encode(file_bytes).decode()

        # 🔥 SEND EMAIL
        response = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": "Your Monthly Expense Report",
            "text": f"""
Hello 👋

Here is your monthly expense report.

Summary:
{report_text}

📎 Full Excel report attached.
""",
            "attachments": [
                {
                    "filename": "expense_report.xlsx",
                    "content": file_base64   # ✅ FIXED
                }
            ]
        })

        print("EMAIL 2 - sent:", response)

        return "📧 Report sent successfully!"

    except Exception as e:
        print("Resend error:", e)
        return "❌ Failed to send email"


def extract_email(user_input):
    match = re.search(r"[\w\.-]+@[\w\.-]+", user_input)
    return match.group() if match else None


# ---------------- EXTRACT EMAIL ----------------
def extract_email(user_input):
    match = re.search(r"[\w\.-]+@[\w\.-]+", user_input)
    return match.group() if match else None