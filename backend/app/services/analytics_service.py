from datetime import datetime

from sqlalchemy import extract, func

from app.models.transaction import Transaction

# ---------------------------------------------------------------------------
# SQL-aggregated variants — used by routes/analytics.py to avoid loading every
# transaction row into memory. Produce the exact same output shape as the
# pure-Python functions below, which remain in use by the Mate context
# builder (it needs the raw Transaction rows for several different windows
# and downstream reasoning, so a full fetch there is unavoidable).
# ---------------------------------------------------------------------------


def get_overview_sql(user_id: int, db) -> dict:
    rows = (
        db.query(Transaction.transaction_type, func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id)
        .group_by(Transaction.transaction_type)
        .all()
    )
    totals = {ttype: float(total or 0) for ttype, total in rows}
    income = totals.get("credit", 0.0)
    expense = totals.get("debit", 0.0)
    savings = income - expense
    savings_rate = round(savings / income * 100, 1) if income > 0 else 0.0
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "savings": round(savings, 2),
        "savings_rate": savings_rate,
    }


def get_monthly_trend_sql(user_id: int, db) -> list:
    rows = (
        db.query(
            extract("year", Transaction.date).label("y"),
            extract("month", Transaction.date).label("m"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(Transaction.user_id == user_id, Transaction.transaction_type == "debit")
        .group_by("y", "m")
        .order_by("y", "m")
        .all()
    )
    result = []
    for y, m, total in rows[-12:]:
        label = datetime(int(y), int(m), 1).strftime("%b %y")
        result.append({"month": label, "spending": round(float(total or 0), 2)})
    return result


def get_category_breakdown_sql(user_id: int, db) -> list:
    rows = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount),
            func.count(Transaction.id),
        )
        .filter(Transaction.user_id == user_id, Transaction.transaction_type == "debit")
        .group_by(Transaction.category)
        .all()
    )
    total = sum(float(amount or 0) for _, amount, _ in rows)
    result = []
    for cat, amount, count in sorted(rows, key=lambda r: -(r[1] or 0)):
        amount = float(amount or 0)
        pct = round(amount / total * 100, 1) if total > 0 else 0.0
        result.append({
            "category": cat,
            "amount": round(amount, 2),
            "percentage": pct,
            "count": count,
        })
    return result


def get_top_merchants_sql(user_id: int, db, limit: int = 5) -> list:
    rows = (
        db.query(
            Transaction.merchant,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id),
        )
        .filter(Transaction.user_id == user_id, Transaction.transaction_type == "debit")
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "merchant": merchant,
            "total_amount": round(float(total or 0), 2),
            "transaction_count": count,
        }
        for merchant, total, count in rows
    ]


def get_cashflow_sql(user_id: int, db) -> list:
    rows = (
        db.query(
            extract("year", Transaction.date).label("y"),
            extract("month", Transaction.date).label("m"),
            Transaction.transaction_type,
            func.sum(Transaction.amount).label("total"),
        )
        .filter(Transaction.user_id == user_id)
        .group_by("y", "m", Transaction.transaction_type)
        .order_by("y", "m")
        .all()
    )
    monthly: dict = {}
    for y, m, ttype, total in rows:
        key = (int(y), int(m))
        monthly.setdefault(key, {"income": 0.0, "expense": 0.0})
        if ttype == "credit":
            monthly[key]["income"] = float(total or 0)
        else:
            monthly[key]["expense"] = float(total or 0)

    result = []
    for y, m in sorted(monthly.keys())[-12:]:
        label = datetime(y, m, 1).strftime("%b %y")
        result.append({
            "month": label,
            "income": round(monthly[(y, m)]["income"], 2),
            "expense": round(monthly[(y, m)]["expense"], 2),
        })
    return result


def get_heatmap_sql(user_id: int, db) -> list:
    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    # extract('dow', ...) is Sunday=0..Saturday=6 on both Postgres and SQLite;
    # (dow + 6) % 7 remaps it to Python's weekday() convention (Monday=0..Sunday=6).
    dow_expr = (extract("dow", Transaction.date) + 6) % 7
    rows = (
        db.query(
            dow_expr.label("wd"),
            func.sum(Transaction.amount),
            func.count(Transaction.id),
        )
        .filter(Transaction.user_id == user_id, Transaction.transaction_type == "debit")
        .group_by("wd")
        .all()
    )
    totals = {int(wd): (float(total or 0), count) for wd, total, count in rows}

    result = []
    for i, day in enumerate(DAYS):
        total, count = totals.get(i, (0.0, 0))
        avg = total / count if count > 0 else 0.0
        result.append({
            "day": day,
            "average_spending": round(avg, 2),
            "total_spending": round(total, 2),
            "transaction_count": count,
        })
    return result


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
