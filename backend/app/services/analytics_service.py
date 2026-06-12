from datetime import datetime


def get_overview(transactions):
    income = sum(t.amount for t in transactions if t.transaction_type == "credit")
    expense = sum(t.amount for t in transactions if t.transaction_type == "debit")
    savings = income - expense
    savings_rate = round(savings / income * 100, 1) if income > 0 else 0.0
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "savings": round(savings, 2),
        "savings_rate": savings_rate,
    }


def get_monthly_trend(transactions):
    monthly: dict[str, float] = {}
    for t in transactions:
        if t.transaction_type == "debit":
            key = t.date.strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0.0) + t.amount

    result = []
    for key in sorted(monthly.keys())[-12:]:
        label = datetime.strptime(key, "%Y-%m").strftime("%b %y")
        result.append({"month": label, "spending": round(monthly[key], 2)})
    return result


def get_category_breakdown(transactions):
    cat_totals: dict[str, float] = {}
    cat_counts: dict[str, int] = {}
    for t in transactions:
        if t.transaction_type == "debit":
            cat_totals[t.category] = cat_totals.get(t.category, 0.0) + t.amount
            cat_counts[t.category] = cat_counts.get(t.category, 0) + 1

    total = sum(cat_totals.values())
    result = []
    for cat, amount in sorted(cat_totals.items(), key=lambda x: -x[1]):
        pct = round(amount / total * 100, 1) if total > 0 else 0.0
        result.append({
            "category": cat,
            "amount": round(amount, 2),
            "percentage": pct,
            "count": cat_counts[cat],
        })
    return result


def get_top_merchants(transactions, limit: int = 5):
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for t in transactions:
        if t.transaction_type == "debit":
            totals[t.merchant] = totals.get(t.merchant, 0.0) + t.amount
            counts[t.merchant] = counts.get(t.merchant, 0) + 1

    top = sorted(totals.items(), key=lambda x: -x[1])[:limit]
    return [
        {
            "merchant": m,
            "total_amount": round(amt, 2),
            "transaction_count": counts[m],
        }
        for m, amt in top
    ]


def get_cashflow(transactions):
    monthly_income: dict[str, float] = {}
    monthly_expense: dict[str, float] = {}
    for t in transactions:
        key = t.date.strftime("%Y-%m")
        if t.transaction_type == "credit":
            monthly_income[key] = monthly_income.get(key, 0.0) + t.amount
        else:
            monthly_expense[key] = monthly_expense.get(key, 0.0) + t.amount

    all_keys = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))[-12:]
    result = []
    for key in all_keys:
        label = datetime.strptime(key, "%Y-%m").strftime("%b %y")
        result.append({
            "month": label,
            "income": round(monthly_income.get(key, 0.0), 2),
            "expense": round(monthly_expense.get(key, 0.0), 2),
        })
    return result


def get_heatmap(transactions):
    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_totals = [0.0] * 7
    day_counts = [0] * 7

    for t in transactions:
        if t.transaction_type == "debit":
            dow = t.date.weekday()  # 0=Mon, 6=Sun
            day_totals[dow] += t.amount
            day_counts[dow] += 1

    result = []
    for i, day in enumerate(DAYS):
        avg = day_totals[i] / day_counts[i] if day_counts[i] > 0 else 0.0
        result.append({
            "day": day,
            "average_spending": round(avg, 2),
            "total_spending": round(day_totals[i], 2),
            "transaction_count": day_counts[i],
        })
    return result
