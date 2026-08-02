from datetime import datetime
from db.client import supabase
from datetime import datetime, timedelta


# ---------------- ADD EXPENSE ----------------
def add_expense(
    user_id: str,
    amount: float,
    category: str,
    raw_text: str,
    expense_time: str | None = None,
) -> str:

    if amount is None or amount <= 0:
        return "❌ Please enter a valid amount"

    if not expense_time:
        expense_time = datetime.now().isoformat()

    try:
        supabase.table("expenses").insert({
            "user_id": user_id,
            "amount": amount,
            "category": category or "general",
            "raw_text": raw_text,
            "note": raw_text,
            "expense_time": expense_time
        }).execute()

        return f"✅ Added Rs.{int(amount)} for {category}"

    except Exception as e:
        print("DB ERROR (add_expense):", e)
        return "⚠️ Failed to save expense. Try again."


# ---------------- Add Income ----------------

def add_income(
    user_id: str,
    amount: float,
    category: str,
    raw_text: str,
    time: str | None = None,
) -> str:

    if amount is None or amount <= 0:
        return "❌ Please enter a valid amount"

    if not time:
        time = datetime.now().isoformat()

    try:
        supabase.table("incomes").insert({
            "user_id": user_id,
            "amount": amount,
            "category": category or "income",
            "raw_text": raw_text,
            "note": raw_text,
            "income_time": time
        }).execute()

        return f"✅ Added Rs.{int(amount)} for {category}"

    except Exception as e:
        print("DB ERROR (add_income):", e)
        return "⚠️ Failed to save income. Try again."


# ---------------- SUMMARY ----------------
# ---------------- SUMMARY ----------------


def get_summary(user_id: str, days: int = 30, label: str = "1 Month") -> str:
    try:
        res_exp = (
            supabase.table("expenses")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        res_inc = (
            supabase.table("incomes")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        expenses = res_exp.data or []
        incomes = res_inc.data or []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        def filter_data(data, key):
            result = []
            for item in data:
                try:
                    dt = datetime.fromisoformat(item[key].replace("Z", "+00:00")).replace(tzinfo=None)
                    if start_date <= dt <= end_date:
                        result.append(item)
                except:
                    pass
            return result

        expenses = filter_data(expenses, "expense_time")
        incomes = filter_data(incomes, "income_time")

        if not expenses and not incomes:
            return "📭 No transactions found for this period."

        total_exp = sum(float(x["amount"]) for x in expenses)
        total_inc = sum(float(x["amount"]) for x in incomes)
        balance = total_inc - total_exp

        exp_categories = {}
        for e in expenses:
            cat = (e.get("category") or "General").title()
            exp_categories[cat] = exp_categories.get(cat, 0) + float(e["amount"])

        inc_categories = {}
        for i in incomes:
            cat = (i.get("category") or "Income").title()
            inc_categories[cat] = inc_categories.get(cat, 0) + float(i["amount"])

        # Summary header with month name
        month_name = end_date.strftime("%B")
        text = f"Summary [ {month_name} ]\n\n"

        if incomes:
            text += f"💵 Balance: Rs.{int(balance)}\n"
            text += f"💰 Total Income: Rs.{int(total_inc)}\n"

        if expenses:
            text += f"🪙 Total Expenses: Rs.{int(total_exp)}\n"

        if incomes:
            text += "\n💰 Income Categories\n"
            for idx, (cat, amount) in enumerate(
                sorted(inc_categories.items(), key=lambda x: x[1], reverse=True), 1
            ):
                text += f"({idx}) {cat}: Rs.{int(amount)}\n"

        if expenses:
            text += "\n🪙 Expense Categories\n"
            for idx, (cat, amount) in enumerate(
                sorted(exp_categories.items(), key=lambda x: x[1], reverse=True), 1
            ):
                text += f"({idx}) {cat}: Rs.{int(amount)}\n"

        return text.strip()

    except Exception as e:
        print("DB ERROR:", e)
        return "⚠️ Could not fetch summary."
    
# ---------------- DELETE LAST ----------------
# ---------------- DELETE LAST TRANSACTION (Fixed) ----------------
def delete_last_transaction(user_id: str) -> str:
    try:
        # Get the most recent expense
        expenses = (
            supabase.table("expenses")
            .select("*")
            .eq("user_id", user_id)
            .order("expense_time", desc=True)
            .limit(1)
            .execute()
        )

        # Get the most recent income
        incomes = (
            supabase.table("incomes")
            .select("*")
            .eq("user_id", user_id)
            .order("income_time", desc=True)
            .limit(1)
            .execute()
        )

        last_expense = expenses.data[0] if expenses.data else None
        last_income = incomes.data[0] if incomes.data else None

        if not last_expense and not last_income:
            return "📭 No transactions found to delete."

        # Determine which is the most recent (expense or income)
        if last_expense and last_income:
            # Compare timestamps
            exp_time = datetime.fromisoformat(last_expense["expense_time"].replace("Z", "+00:00"))
            inc_time = datetime.fromisoformat(last_income["income_time"].replace("Z", "+00:00"))
            
            if exp_time >= inc_time:
                latest = last_expense
                table_name = "expenses"
            else:
                latest = last_income
                table_name = "incomes"
        elif last_expense:
            latest = last_expense
            table_name = "expenses"
        else:
            latest = last_income
            table_name = "incomes"

        # Delete the record
        result = (
            supabase.table(table_name)
            .delete()
            .eq("id", latest["id"])
            .execute()
        )

        if result.data:
            return f"🗑️ Deleted last transaction: {latest.get('category')} - Rs.{int(latest.get('amount', 0))}"
        else:
            return "⚠️ Failed to delete transaction."

    except Exception as e:
        print("DB ERROR (delete_last_transaction):", e)
        return "⚠️ Failed to delete last transaction. Try again."


# ---------------- UPDATE LAST ----------------
def update_last_expense(user_id: str, new_amount: float) -> str:
    if new_amount is None or new_amount <= 0:
        return "❌ Please enter a valid amount"

    try:
        res = (
            supabase.table("expenses")
            .select("*")
            .eq("user_id", user_id)
            .order("expense_time", desc=True)
            .limit(1)
            .execute()
        )

        if not res.data:
            return "📭 No expenses to update."

        expense_id = res.data[0]["id"]

        supabase.table("expenses")\
            .update({"amount": new_amount})\
            .eq("id", expense_id)\
            .execute()

        return f"✏️ Updated last expense to Rs.{int(new_amount)}"

    except Exception as e:
        print("DB ERROR (update):", e)
        return "⚠️ Failed to update expense."


# ---------------- MONTHLY REPORT ----------------
def generate_monthly_report(user_id: str) -> str:
    try:
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1).isoformat()

        res = (
            supabase.table("expenses")
            .select("*")
            .eq("user_id", user_id)
            .gte("expense_time", start_of_month)
            .execute()
        )

        data = res.data or []

        if not data:
            return "📭 No expenses this month."

        total = sum(float(x["amount"]) for x in data)

        by_cat = {}
        for x in data:
            category = x.get("category") or "general"
            by_cat[category] = by_cat.get(category, 0) + float(x["amount"])

        most = max(by_cat, key=by_cat.get)
        avg = total / len(data)

        report = (
            "📊 Monthly Expense Report\n\n"
            f"💰 Total: Rs.{int(total)}\n\n"
            "📂 Breakdown:\n"
        )

        for category, value in by_cat.items():
            report += f"• {category}: Rs.{int(value)}\n"

        # 🔥 recent entries (UX boost)
        report += "\n📝 Recent:\n"
        for x in data[-5:]:
            note = x.get("note") or ""
            amount = int(x.get("amount", 0))
            report += f"• Rs.{amount} → {note}\n"

        report += (
            "\n📅 Insights:\n"
            f"• Top: {most}\n"
            f"• Avg: Rs.{int(avg)}\n"
            f"• Entries: {len(data)}"
        )

        return report.strip()

    except Exception as e:
        print("DB ERROR (report):", e)
        return "⚠️ Could not generate report."