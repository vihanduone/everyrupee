import pandas as pd
from db.client import supabase
from datetime import datetime


def generate_excel_report(user_id: str) -> str:

    try:
        # ---------------- FETCH DATA ----------------
        res = (
            supabase.table("expenses")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        data = res.data or []

        if not data:
            return "📭 No expenses found to generate report."

        # ---------------- DATAFRAME ----------------
        df = pd.DataFrame(data)

        df["amount"] = df["amount"].astype(float)
        df["category"] = df["category"].fillna("general")

        summary = df.groupby("category")["amount"].sum().reset_index()
        total = df["amount"].sum()

        # ---------------- FILE NAME ----------------
        filename = f"report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # ---------------- WRITE FILE ----------------
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="All Expenses", index=False)
            summary.to_excel(writer, sheet_name="Summary", index=False)

            # add total
            worksheet = writer.sheets["Summary"]
            worksheet["D2"] = "Total"
            worksheet["E2"] = float(total)

        # ---------------- RETURN ----------------
        return f"📄 Report generated successfully.\nFile: {filename}"

    except Exception as e:
        print("ERROR (excel report):", e)
        return "⚠️ Failed to generate report."