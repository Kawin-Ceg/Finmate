"""
Financial Anomaly Detection Engine
===================================
Detects five categories of spending anomalies using statistical methods.
Persisted in DB; recomputed only after CSV upload or manual trigger.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.services.budget_service import compute_forecast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _severity_from_score(score: float) -> str:
    if score >= 76:
        return "critical"
    if score >= 51:
        return "high"
    if score >= 26:
        return "medium"
    return "low"


def _percentile(data: list[float], p: float) -> float:
    """Return the p-th percentile of a sorted list."""
    if not data:
        return 0.0
    data = sorted(data)
    k = (len(data) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(data) - 1)
    return data[lo] + (data[hi] - data[lo]) * (k - lo)


def _current_month_transactions(
    transactions: list[Transaction],
    today: Optional[date] = None,
) -> list[Transaction]:
    today = today or date.today()
    return [
        t for t in transactions
        if t.transaction_type == "debit"
        and t.date.year == today.year
        and t.date.month == today.month
    ]


def _historical_transactions(
    transactions: list[Transaction],
    today: Optional[date] = None,
) -> list[Transaction]:
    today = today or date.today()
    return [
        t for t in transactions
        if t.transaction_type == "debit"
        and not (t.date.year == today.year and t.date.month == today.month)
    ]


# ---------------------------------------------------------------------------
# 1. Transaction Anomaly — Z-score + IQR per merchant
# ---------------------------------------------------------------------------

def detect_transaction_anomalies(
    transactions: list[Transaction],
    today: Optional[date] = None,
) -> list[dict]:
    """Flag individual transactions that are statistical outliers per merchant."""
    today = today or date.today()
    historical = _historical_transactions(transactions, today)
    current = _current_month_transactions(transactions, today)

    # Build per-merchant history from previous months
    hist_by_merchant: dict[str, list[float]] = defaultdict(list)
    for t in historical:
        if t.merchant:
            hist_by_merchant[t.merchant.strip()].append(float(t.amount))

    anomalies: list[dict] = []
    seen_merchants: set[str] = set()

    for t in sorted(current, key=lambda x: x.amount, reverse=True):
        merchant = (t.merchant or "Unknown").strip()
        if merchant in seen_merchants:
            continue

        amounts = hist_by_merchant.get(merchant, [])
        if len(amounts) < 3:
            continue

        mu = statistics.mean(amounts)
        sigma = statistics.stdev(amounts) if len(amounts) >= 2 else 0.0

        if sigma == 0:
            continue

        amount = float(t.amount)
        z = (amount - mu) / sigma

        q1 = _percentile(amounts, 25)
        q3 = _percentile(amounts, 75)
        iqr = q3 - q1
        upper_fence = q3 + 1.5 * iqr

        is_zscore_outlier = z >= 2.5
        is_iqr_outlier = amount > upper_fence and amount > mu * 1.5

        if not (is_zscore_outlier or is_iqr_outlier):
            continue

        seen_merchants.add(merchant)

        score = min(100.0, abs(z) * 18 + 10)
        score = max(score, 26.0)  # minimum medium severity
        deviation_pct = round((amount - mu) / mu * 100) if mu > 0 else 0

        anomalies.append({
            "transaction_id": t.id,
            "type": "transaction",
            "score": round(score, 1),
            "title": f"Unusual {merchant} Transaction — {deviation_pct}% Above Normal",
            "description": (
                f"You spent ₹{amount:,.0f} at {merchant}, which is {deviation_pct}% higher "
                f"than your typical ₹{mu:,.0f}. Based on your last {len(amounts)} transactions "
                f"at this merchant, this amount is statistically unusual."
            ),
            "meta_data": {
                "merchant": merchant,
                "transaction_amount": round(amount, 2),
                "historical_mean": round(mu, 2),
                "historical_std": round(sigma, 2),
                "z_score": round(z, 2),
                "expected_range_min": round(max(0, mu - 2 * sigma), 2),
                "expected_range_max": round(mu + 2 * sigma, 2),
                "deviation_pct": deviation_pct,
                "sample_size": len(amounts),
            },
        })

    return anomalies


# ---------------------------------------------------------------------------
# 2. Category Anomaly — current month vs historical monthly average
# ---------------------------------------------------------------------------

def detect_category_anomalies(
    transactions: list[Transaction],
    today: Optional[date] = None,
) -> list[dict]:
    """Flag categories with ≥50% spending spike vs historical monthly average."""
    today = today or date.today()
    historical = _historical_transactions(transactions, today)
    current = _current_month_transactions(transactions, today)

    if not historical:
        return []

    # Determine unique past months
    past_months: set[tuple[int, int]] = {
        (t.date.year, t.date.month) for t in historical
    }
    if len(past_months) < 2:
        return []

    # Spend per category per past month
    category_monthly: dict[str, dict[tuple[int, int], float]] = defaultdict(lambda: defaultdict(float))
    for t in historical:
        key = (t.date.year, t.date.month)
        cat = (t.category or "Uncategorized").strip()
        category_monthly[cat][key] += float(t.amount)

    # Current month totals
    current_by_cat: dict[str, float] = defaultdict(float)
    for t in current:
        cat = (t.category or "Uncategorized").strip()
        current_by_cat[cat] += float(t.amount)

    anomalies: list[dict] = []

    for cat, current_spend in current_by_cat.items():
        if cat not in category_monthly:
            continue
        monthly_totals = list(category_monthly[cat].values())
        if len(monthly_totals) < 2:
            continue

        hist_avg = statistics.mean(monthly_totals)
        if hist_avg <= 0:
            continue

        increase_pct = round((current_spend - hist_avg) / hist_avg * 100)
        if increase_pct < 50:
            continue

        hist_std = statistics.stdev(monthly_totals) if len(monthly_totals) >= 2 else 0.0
        z = (current_spend - hist_avg) / hist_std if hist_std > 0 else 0.0

        score = min(100.0, increase_pct * 0.5 + abs(z) * 8)
        score = max(score, 26.0)

        anomalies.append({
            "transaction_id": None,
            "type": "category",
            "score": round(score, 1),
            "title": f"{cat} Spending Spike — {increase_pct}% Above Average",
            "description": (
                f"Your {cat} spending this month is ₹{current_spend:,.0f}, which is "
                f"{increase_pct}% higher than your historical average of ₹{hist_avg:,.0f}/month. "
                f"This pattern was calculated from {len(monthly_totals)} months of history."
            ),
            "meta_data": {
                "category": cat,
                "current_month_spend": round(current_spend, 2),
                "historical_avg": round(hist_avg, 2),
                "historical_std": round(hist_std, 2),
                "increase_pct": increase_pct,
                "z_score": round(z, 2),
                "months_analyzed": len(monthly_totals),
            },
        })

    anomalies.sort(key=lambda x: x["score"], reverse=True)
    return anomalies


# ---------------------------------------------------------------------------
# 3. Merchant Anomaly — new merchants + merchant spending spikes
# ---------------------------------------------------------------------------

_EXCLUDED_MERCHANTS = {"ATM", "ATM WITHDRAWAL", "CASH WITHDRAWAL", "TRANSFER"}


def detect_merchant_anomalies(
    transactions: list[Transaction],
    today: Optional[date] = None,
) -> list[dict]:
    """Flag first-time high-value merchants and merchants with spending spikes."""
    today = today or date.today()
    historical = _historical_transactions(transactions, today)
    current = _current_month_transactions(transactions, today)

    if not historical:
        return []

    historical_merchants: set[str] = {
        (t.merchant or "").strip().upper()
        for t in historical
        if t.merchant
    }

    # Historical spend per merchant
    hist_spend: dict[str, list[float]] = defaultdict(list)
    for t in historical:
        if t.merchant:
            hist_spend[(t.merchant or "").strip()].append(float(t.amount))

    # Current month total per merchant
    current_spend: dict[str, float] = defaultdict(float)
    current_first: dict[str, Transaction] = {}
    for t in sorted(current, key=lambda x: x.date):
        merchant = (t.merchant or "").strip()
        if not merchant:
            continue
        current_spend[merchant] += float(t.amount)
        if merchant not in current_first:
            current_first[merchant] = t

    anomalies: list[dict] = []
    flagged_new: set[str] = set()
    flagged_spike: set[str] = set()

    for merchant, total in sorted(current_spend.items(), key=lambda x: -x[1]):
        if merchant.upper() in _EXCLUDED_MERCHANTS:
            continue

        first_txn = current_first.get(merchant)
        amount = float(first_txn.amount) if first_txn else total

        # New merchant check
        if merchant.upper() not in historical_merchants and merchant not in flagged_new:
            if amount >= 300:
                score = min(100.0, 20 + amount / 200)
                score = min(score, 65.0)
                flagged_new.add(merchant)
                anomalies.append({
                    "transaction_id": first_txn.id if first_txn else None,
                    "type": "merchant",
                    "score": round(score, 1),
                    "title": f"New Merchant: {merchant}",
                    "description": (
                        f"₹{amount:,.0f} was charged by {merchant}, a merchant that has never "
                        f"appeared in your transaction history. Please verify you authorized this payment."
                    ),
                    "meta_data": {
                        "merchant": merchant,
                        "transaction_amount": round(amount, 2),
                        "is_new_merchant": True,
                        "category": first_txn.category if first_txn else None,
                    },
                })

        # Spending spike check
        hist_amounts = hist_spend.get(merchant, [])
        if len(hist_amounts) >= 2 and merchant not in flagged_spike:
            hist_mean = statistics.mean(hist_amounts)
            if hist_mean > 0 and total > 2.0 * hist_mean:
                ratio = total / hist_mean
                score = min(100.0, ratio * 15 + 10)
                increase_pct = round((total - hist_mean) / hist_mean * 100)
                flagged_spike.add(merchant)
                anomalies.append({
                    "transaction_id": first_txn.id if first_txn else None,
                    "type": "merchant",
                    "score": round(score, 1),
                    "title": f"{merchant} Spending Up {increase_pct}% This Month",
                    "description": (
                        f"You've spent ₹{total:,.0f} at {merchant} this month, which is "
                        f"{increase_pct}% higher than your typical ₹{hist_mean:,.0f}. "
                        f"Check for price increases, duplicate charges, or unplanned purchases."
                    ),
                    "meta_data": {
                        "merchant": merchant,
                        "transaction_amount": round(total, 2),
                        "historical_mean": round(hist_mean, 2),
                        "increase_pct": increase_pct,
                        "ratio": round(ratio, 2),
                        "is_new_merchant": False,
                        "category": first_txn.category if first_txn else None,
                    },
                })

    return anomalies


# ---------------------------------------------------------------------------
# 4. Subscription Detection — recurring payments with consistent amounts
# ---------------------------------------------------------------------------

_SUBSCRIPTION_EXCLUDED_CATEGORIES = {"Cash", "Transfers", "Income", "Investment"}


def detect_subscriptions(
    transactions: list[Transaction],
    today: Optional[date] = None,
) -> list[dict]:
    """Detect recurring charges using coefficient of variation across months."""
    today = today or date.today()
    all_debits = [
        t for t in transactions
        if t.transaction_type == "debit" and t.merchant
    ]

    merchant_txns: dict[str, list[Transaction]] = defaultdict(list)
    for t in all_debits:
        merchant = (t.merchant or "").strip()
        if merchant:
            merchant_txns[merchant].append(t)

    anomalies: list[dict] = []

    for merchant, txns in merchant_txns.items():
        if merchant.upper() in _EXCLUDED_MERCHANTS:
            continue

        # Exclude non-subscription categories
        cats = {(t.category or "").strip() for t in txns}
        if cats & _SUBSCRIPTION_EXCLUDED_CATEGORIES:
            continue

        # Check if transactions span multiple distinct months
        months = {(t.date.year, t.date.month) for t in txns}
        if len(months) < 2:
            continue

        amounts = [float(t.amount) for t in txns]
        avg_amount = statistics.mean(amounts)

        if avg_amount < 50:
            continue

        # Coefficient of variation (consistency check)
        std = statistics.stdev(amounts) if len(amounts) >= 2 else 0.0
        cv = std / avg_amount if avg_amount > 0 else 1.0

        if cv >= 0.3:
            continue

        occurrence_count = len(months)
        monthly_cost = round(avg_amount, 2)
        annual_cost = round(monthly_cost * 12, 2)

        score = min(40.0, 15.0 + occurrence_count * 5.0)
        category = txns[0].category if txns else None

        anomalies.append({
            "transaction_id": txns[-1].id,  # most recent occurrence
            "type": "subscription",
            "score": round(score, 1),
            "title": f"Recurring Subscription: {merchant}",
            "description": (
                f"Detected a recurring charge of ~₹{monthly_cost:,.0f}/month at {merchant} "
                f"across {occurrence_count} months (CV={cv:.2f}). "
                f"This costs approximately ₹{annual_cost:,.0f}/year."
            ),
            "meta_data": {
                "merchant": merchant,
                "monthly_cost": monthly_cost,
                "annual_cost": annual_cost,
                "avg_amount": round(avg_amount, 2),
                "occurrence_count": occurrence_count,
                "cv": round(cv, 3),
                "category": category,
                "months": sorted([f"{y}-{m:02d}" for y, m in months]),
            },
        })

    anomalies.sort(key=lambda x: -x["meta_data"]["annual_cost"])
    return anomalies


# ---------------------------------------------------------------------------
# 5. Budget Risk — integrate with existing compute_forecast
# ---------------------------------------------------------------------------

def detect_budget_risk_anomalies(
    transactions: list[Transaction],
    budgets: list[Budget],
) -> list[dict]:
    """Flag budgets that are on track to be exceeded or already exceeded."""
    anomalies: list[dict] = []

    for budget in budgets:
        forecast = compute_forecast(budget, transactions)
        risk = forecast["risk"]

        if risk not in ("high", "exceeded"):
            continue

        current = forecast["current_spend"]
        projected = forecast["projected_spend"]
        limit = forecast["budget"]
        overrun = forecast["expected_overrun"]
        pct_used = (current / limit * 100) if limit > 0 else 0.0

        if risk == "exceeded":
            score = min(100.0, 70.0 + overrun / limit * 30) if limit > 0 else 75.0
            title = f"{budget.category} Budget Exceeded by ₹{overrun:,.0f}"
            description = (
                f"You have already exceeded your ₹{limit:,.0f} {budget.category} budget "
                f"by ₹{overrun:,.0f} this month. Current spend is ₹{current:,.0f} "
                f"({pct_used:.0f}% of budget)."
            )
        else:
            score = min(100.0, 55.0 + overrun / limit * 20) if limit > 0 else 57.0
            title = f"{budget.category} Budget at Risk — Projected ₹{overrun:,.0f} Overrun"
            description = (
                f"At the current daily spending rate of ₹{forecast['daily_rate']:,.0f}/day, "
                f"your {budget.category} budget will likely exceed ₹{limit:,.0f} by "
                f"₹{overrun:,.0f} this month. Current spend: ₹{current:,.0f} "
                f"({pct_used:.0f}% of budget)."
            )

        anomalies.append({
            "transaction_id": None,
            "type": "budget",
            "score": round(score, 1),
            "title": title,
            "description": description,
            "meta_data": {
                "category": budget.category,
                "budget": limit,
                "current_spend": round(current, 2),
                "projected_spend": round(projected, 2),
                "expected_overrun": round(overrun, 2),
                "pct_used": round(pct_used, 1),
                "daily_rate": forecast["daily_rate"],
                "days_remaining": forecast["days_remaining"],
                "risk": risk,
            },
        })

    return anomalies


# ---------------------------------------------------------------------------
# Master runner
# ---------------------------------------------------------------------------

def run_anomaly_detection(user_id: int, db: Session) -> int:
    """
    Clear existing anomalies for this user and run all five detectors.
    Returns the count of anomalies persisted.
    """
    transactions: list[Transaction] = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .all()
    )
    budgets: list[Budget] = (
        db.query(Budget)
        .filter(Budget.user_id == user_id)
        .all()
    )

    # Idempotent: wipe previous results
    db.query(Anomaly).filter(Anomaly.user_id == user_id).delete(
        synchronize_session=False
    )
    db.flush()

    all_raw: list[dict] = []
    all_raw.extend(detect_transaction_anomalies(transactions))
    all_raw.extend(detect_category_anomalies(transactions))
    all_raw.extend(detect_merchant_anomalies(transactions))
    all_raw.extend(detect_subscriptions(transactions))
    all_raw.extend(detect_budget_risk_anomalies(transactions, budgets))

    for raw in all_raw:
        anomaly = Anomaly(
            user_id=user_id,
            transaction_id=raw.get("transaction_id"),
            type=raw["type"],
            severity=_severity_from_score(raw["score"]),
            title=raw["title"],
            description=raw["description"],
            score=raw["score"],
            meta_data=raw.get("meta_data"),
        )
        db.add(anomaly)

    db.commit()
    return len(all_raw)
