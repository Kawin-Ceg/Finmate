import calendar
import math
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.transaction import Transaction

# Categories where monthly spend is front-loaded (paid as lump sum in days 1-3).
# Linear daily-rate projection catastrophically overestimates these categories
# early in the month (day-7 MAPE = 334% vs ~6% for historical prior).
# See FORECAST_BENCHMARK_REPORT.md, Phase 7.
_LUMP_SUM_CATEGORIES = {"Rent", "Insurance"}

# Months of history to use for the historical prior
_HISTORY_MONTHS = 3


def _risk_level(pct: float) -> str:
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


def _historical_monthly_totals(
    category: str,
    transactions: List[Transaction],
    n_months: int = _HISTORY_MONTHS,
) -> List[float]:
    """
    Return per-month spending totals for the last `n_months` complete months,
    excluding the current (incomplete) month.
    """
    today = date.today()
    totals = []
    for m in range(1, n_months + 1):
        ref = (today.replace(day=1) - timedelta(days=m * 28)).replace(day=1)
        month_total = sum(
            t.amount
            for t in transactions
            if t.category.lower() == category.lower()
            and t.transaction_type == "debit"
            and t.date.year == ref.year
            and t.date.month == ref.month
        )
        totals.append(month_total)
    return totals


def _daily_spend_variance(category: str, transactions: List[Transaction]) -> float:
    """Std dev of daily spend so far this month — used for within-month CI."""
    today = date.today()
    by_day: dict[int, float] = {}
    for t in transactions:
        if (
            t.category.lower() == category.lower()
            and t.transaction_type == "debit"
            and t.date.year == today.year
            and t.date.month == today.month
        ):
            by_day[t.date.day] = by_day.get(t.date.day, 0) + t.amount

    values = list(by_day.values())
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))


def compute_budget_progress(budget: Budget, transactions: List[Transaction]) -> dict:
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
    """
    Project end-of-month spend using a hybrid algorithm:

    - Lump-sum categories (Rent, Insurance): use 3-month historical average.
      Linear daily rate catastrophically overestimates these early in the month
      (day-7 MAPE 334% vs 28% for historical prior — Phase 7 benchmark).
    - All others, days_elapsed < 15: blended (60% linear + 40% historical prior).
      Prevents over-extrapolation from early-month high/low spend days.
    - All others, days_elapsed >= 15: linear daily rate.
      Once half the month has elapsed the daily rate is already ~3-5% MAPE.

    Phase 8: confidence intervals computed as
      std = sqrt(historical_std² + future_variance)
      lower = projected - 1.645 × std  (90% CI)
      upper = projected + 1.645 × std

    Phase 9: exceed probability via normal CDF
      P(total > limit) = 1 - Φ((limit - projected) / std)
    """
    import scipy.stats as stats

    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(today.day, 1)
    days_remaining = days_in_month - today.day

    spend = _current_month_spend(budget.category, transactions)
    daily_rate = spend / days_elapsed
    linear_proj = daily_rate * days_in_month

    history = _historical_monthly_totals(budget.category, transactions)
    hist_mean = sum(history) / len(history) if history else linear_proj
    hist_std = (
        math.sqrt(sum((h - hist_mean) ** 2 for h in history) / len(history))
        if len(history) > 1 else hist_mean * 0.20
    )

    # --- Select projection algorithm ---
    category = budget.category
    if category in _LUMP_SUM_CATEGORIES:
        projected = hist_mean
        method = "historical_prior"
    elif days_elapsed < 15:
        projected = 0.6 * linear_proj + 0.4 * hist_mean
        method = "blended"
    else:
        projected = linear_proj
        method = "linear_daily_rate"

    # --- Confidence interval (Phase 8) ---
    daily_std = _daily_spend_variance(budget.category, transactions)
    future_variance = (daily_std ** 2) * days_remaining
    combined_std = math.sqrt(hist_std ** 2 + future_variance)

    z90 = 1.645
    lower_bound = max(0.0, projected - z90 * combined_std)
    upper_bound = projected + z90 * combined_std

    # --- Exceed probability (Phase 9) ---
    limit = budget.monthly_limit
    if combined_std > 0 and limit > 0:
        exceed_probability = float(1 - stats.norm.cdf(limit, loc=projected, scale=combined_std))
    elif projected > limit:
        exceed_probability = 1.0
    else:
        exceed_probability = 0.0

    overrun = max(0.0, projected - limit)
    pct_projected = (projected / limit * 100) if limit > 0 else 0.0

    # --- Explainability driver (Phase 10) ---
    driver = _explain_driver(
        category, spend, days_elapsed, daily_rate, hist_mean, projected, method
    )

    return {
        "category": category,
        "budget": round(limit, 2),
        "current_spend": round(spend, 2),
        "projected_spend": round(projected, 2),
        "lower_bound": round(lower_bound, 2),
        "upper_bound": round(upper_bound, 2),
        "exceed_probability": round(exceed_probability, 3),
        "expected_overrun": round(overrun, 2),
        "risk": _risk_level(pct_projected),
        "daily_rate": round(daily_rate, 2),
        "days_remaining": days_remaining,
        "forecast_method": method,
        "explanation": driver,
    }


def _explain_driver(
    category: str,
    spend_so_far: float,
    days_elapsed: int,
    daily_rate: float,
    hist_mean: float,
    projected: float,
    method: str,
) -> str:
    """One-sentence natural-language explanation of what's driving the forecast."""
    if method == "historical_prior":
        return f"Using your {_HISTORY_MONTHS}-month average because {category} is typically a fixed monthly payment."

    if hist_mean > 0:
        pct_above = ((daily_rate * 30) - hist_mean) / hist_mean * 100
    else:
        pct_above = 0.0

    if abs(pct_above) < 5:
        pace = "at your historical average pace"
    elif pct_above > 0:
        pace = f"{abs(pct_above):.0f}% above your historical average"
    else:
        pace = f"{abs(pct_above):.0f}% below your historical average"

    return f"Day {days_elapsed}: spending {pace} — projecting ₹{projected:,.0f} by end of month."


def generate_alerts(forecasts: List[dict]) -> List[str]:
    alerts = []
    for f in forecasts:
        pct_now = (f["current_spend"] / f["budget"] * 100) if f["budget"] > 0 else 0.0
        if f["risk"] == "exceeded":
            alerts.append(
                f"{f['category']} budget exceeded by ₹{f['expected_overrun']:,.0f}"
            )
        elif f["risk"] == "high" and f.get("exceed_probability", 0) > 0.70:
            alerts.append(
                f"{f['category']} has a {f['exceed_probability']*100:.0f}% chance of exceeding budget "
                f"(projected ₹{f['projected_spend']:,.0f} vs limit ₹{f['budget']:,.0f})"
            )
        elif f["risk"] == "watch" and pct_now > 65:
            alerts.append(
                f"{f['category']} is at {pct_now:.0f}% of budget — spending pace is elevated"
            )
    return alerts
