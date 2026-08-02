from datetime import datetime, timedelta
from db.client import supabase


def build_weekly_report(user):

    end = datetime.now()

    start = end - timedelta(days=7)

    expenses = (
        supabase.table("expenses")
        .select("*")
        .eq("user_id", user["id"])
        .execute()
    ).data or []

    incomes = (
        supabase.table("incomes")
        .select("*")
        .eq("user_id", user["id"])
        .execute()
    ).data or []

    total_expense = 0

    total_income = 0

    category_totals = {}

    for e in expenses:

        try:

            dt = datetime.fromisoformat(
                e["expense_time"].replace("Z", "+00:00")
            )

            if dt >= start:

                amount = float(e["amount"])

                total_expense += amount

                cat = e["category"]

                category_totals[cat] = (
                    category_totals.get(cat, 0) + amount
                )

        except:

            pass

    for i in incomes:

        try:

            dt = datetime.fromisoformat(
                i["income_time"].replace("Z", "+00:00")
            )

            if dt >= start:

                total_income += float(i["amount"])

        except:

            pass

    balance = total_income - total_expense

    biggest = "None"

    if category_totals:

        biggest = max(category_totals, key=category_totals.get)

    html = f"""

<h2>📊 Weekly EveryRupee Report</h2>

<p>Income : Rs.{int(total_income)}</p>

<p>Expenses : Rs.{int(total_expense)}</p>

<p>Balance : Rs.{int(balance)}</p>

<h3>Top Category</h3>

<p>{biggest}</p>

"""

    return html