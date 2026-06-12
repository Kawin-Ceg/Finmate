import calendar
from datetime import date
from typing import List

from app.models.budget import Budget
from app.models.transaction import Transaction


def _risk_level(pct: float) -> str:
    """Map a 0-100 percentage to a risk label."""
    if pct < 60:
        return "safe"
    if pct < 85:
        return "watch"
    if pct < 100:
        return "high"
    return "exceeded"


def _current_month_spend(category: str, transactions: List[Transaction]) -> float:
    today = date.today()
    return sum(
        t.amount
        for t in transactions
        if t.category.lower() == category.lower()
        and t.transaction_type == "debit"
        and t.date.year == today.year
        and t.date.month == today.month
    )


def compute_budget_progress(budget: Budget, transactions: List[Transaction]) -> dict:
    """Return real-time progress for one budget (used in list endpoint)."""
    spend = _current_month_spend(budget.category, transactions)
    remaining = budget.monthly_limit - spend
    pct = (spend / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0.0

    return {
        "id": budget.id,
        "category": budget.category,
        "monthly_limit": budget.monthly_limit,
        "current_spend": round(spend, 2),
        "remaining": round(remaining, 2),
        "pct_used": round(pct, 1),
        "risk": _risk_level(pct),
        "created_at": budget.created_at,
    }


def compute_forecast(budget: Budget, transactions: List[Transaction]) -> dict:
    """Project end-of-month spend using current daily rate."""
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(today.day, 1)  # avoid div-by-zero on day 0
    days_remaining = days_in_month - today.day

    spend = _current_month_spend(budget.category, transactions)
    daily_rate = spend / days_elapsed
    projected = daily_rate * days_in_month
    overrun = max(0.0, projected - budget.monthly_limit)

    pct_projected = (projected / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0.0

    return {
        "category": budget.category,
        "budget": budget.monthly_limit,
        "current_spend": round(spend, 2),
        "projected_spend": round(projected, 2),
        "expected_overrun": round(overrun, 2),
        "risk": _risk_level(pct_projected),
        "daily_rate": round(daily_rate, 2),
        "days_remaining": days_remaining,
    }


def generate_alerts(forecasts: List[dict]) -> List[str]:
    """Produce human-readable alert strings from forecast data."""
    alerts = []
    for f in forecasts:
        pct_now = (f["current_spend"] / f["budget"] * 100) if f["budget"] > 0 else 0.0
        if f["risk"] == "exceeded":
            alerts.append(
                f"{f['category']} budget exceeded by "
                f"₹{f['expected_overrun']:,.0f}"
            )
        elif f["risk"] == "high" and f["expected_overrun"] > 0:
            alerts.append(
                f"{f['category']} budget likely to exceed by "
                f"₹{f['expected_overrun']:,.0f} this month"
            )
        elif f["risk"] == "watch" and pct_now > 65:
            alerts.append(
                f"{f['category']} is at {pct_now:.0f}% of budget — "
                f"spending pace is elevated"
            )
    return alerts
