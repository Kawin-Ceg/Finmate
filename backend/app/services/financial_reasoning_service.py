"""
Financial Reasoning Service
Pre-computes structured financial insights per intent before LLM call.
The LLM explains; this engine thinks.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.anomaly import Anomaly
from app.services.context_builder import DEFAULT_CURRENCY_SYMBOL, _fmt


def analyze_savings_opportunity(ctx: dict, target_amount: float | None = None) -> dict:
    """Identify actionable savings opportunities from context."""
    symbol = ctx.get("currency_symbol", DEFAULT_CURRENCY_SYMBOL)
    overview = ctx["overview"]
    categories = ctx["categories"]
    subscriptions = ctx["subscriptions"]
    budgets = ctx["budgets"]

    # Find above-average categories
    if not categories:
        return {"possible": False, "reason": "No spending data available."}

    total_expense = overview["expense"]
    avg_cat_spend = total_expense / max(len(categories), 1)

    high_cats = [c for c in categories if c["amount"] > avg_cat_spend * 1.2 and c["category"] != "Income"]
    high_cats_sorted = sorted(high_cats, key=lambda x: -x["amount"])[:3]

    # Subscription total
    sub_total = sum(s["amount"] for s in subscriptions)

    # Budget at risk
    at_risk = [b for b in budgets if b["risk"] in ("high", "exceeded")]

    # Rough potential savings: 20% reduction on top 2 categories
    potential = sum(c["amount"] * 0.20 for c in high_cats_sorted[:2]) + (sub_total * 0.5 if subscriptions else 0)
    potential = round(potential, 2)

    result = {
        "possible": True,
        "target": target_amount,
        "potential_savings": potential,
        "target_achievable": potential >= (target_amount or 0),
        "high_spend_categories": [
            {
                "category": c["category"],
                "amount": c["amount"],
                "amount_fmt": _fmt(c["amount"], symbol),
                "reduction_20pct": round(c["amount"] * 0.20, 2),
            }
            for c in high_cats_sorted
        ],
        "subscriptions_total": sub_total,
        "subscriptions_total_fmt": _fmt(sub_total, symbol),
        "subscription_count": len(subscriptions),
        "at_risk_budgets": [b["category"] for b in at_risk],
        "recommendations": _generate_savings_recs(high_cats_sorted, subscriptions, at_risk, target_amount, symbol),
    }
    return result


def _generate_savings_recs(high_cats, subscriptions, at_risk_budgets, target, symbol: str = DEFAULT_CURRENCY_SYMBOL) -> List[str]:
    recs = []
    for c in high_cats[:2]:
        saving = c["amount"] * 0.20
        recs.append(f"Reduce {c['category']} spending by 20% → save {_fmt(saving, symbol)}/month")
    if subscriptions:
        recs.append(f"Review {len(subscriptions)} subscriptions (total ~{_fmt(sum(s['amount'] for s in subscriptions), symbol)}/mo) — cancel unused ones")
    for b in at_risk_budgets[:2]:
        recs.append(f"Pause non-essential {b} purchases until month end")
    if not recs:
        recs.append("Your spending looks healthy. Consider increasing monthly savings target.")
    return recs


def analyze_budget_risk(ctx: dict) -> dict:
    """Rank budgets by risk and provide forecast explanations."""
    budgets = ctx["budgets"]
    if not budgets:
        return {"has_budgets": False}

    risk_rank = {"exceeded": 4, "high": 3, "watch": 2, "safe": 1}
    ranked = sorted(budgets, key=lambda b: risk_rank.get(b["risk"], 0), reverse=True)

    return {
        "has_budgets": True,
        "most_at_risk": ranked[0] if ranked else None,
        "all_ranked": [
            {
                "category": b["category"],
                "risk": b["risk"],
                "pct_used": b["pct_used"],
                "monthly_limit": b["monthly_limit"],
                "current_spend": b["current_spend"],
                "projected_spend": b["forecast"]["projected_spend"],
                "expected_overrun": b["forecast"]["expected_overrun"],
                "days_remaining": b["forecast"]["days_remaining"],
            }
            for b in ranked
        ],
        "exceeded_count": sum(1 for b in budgets if b["risk"] == "exceeded"),
        "high_risk_count": sum(1 for b in budgets if b["risk"] == "high"),
        "safe_count": sum(1 for b in budgets if b["risk"] == "safe"),
    }


def explain_health_score(ctx: dict) -> dict:
    """Break down why the health score is what it is."""
    health = ctx["health"]
    bd = health.get("breakdown", {})

    factors = []
    max_scores = {
        "savings_rate": 35,
        "expense_stability": 25,
        "income_consistency": 25,
        "diversification": 15,
    }
    labels = {
        "savings_rate": "Savings Rate",
        "expense_stability": "Expense Stability",
        "income_consistency": "Income Consistency",
        "diversification": "Category Diversification",
    }

    for key, max_val in max_scores.items():
        actual = bd.get(key, 0)
        pct = round(actual / max_val * 100) if max_val else 0
        factors.append({
            "factor": labels[key],
            "score": actual,
            "max": max_val,
            "pct": pct,
            "status": "good" if pct >= 70 else "needs_work" if pct >= 40 else "poor",
        })

    weakest = min(factors, key=lambda f: f["pct"])
    improvement_tips = _health_improvement_tips(factors, ctx)

    return {
        "score": health["score"],
        "grade": health["grade"],
        "status": health["status"],
        "factors": factors,
        "weakest_factor": weakest,
        "insights": health.get("insights", []),
        "improvement_tips": improvement_tips,
    }


def _health_improvement_tips(factors: list, ctx: dict) -> List[str]:
    tips = []
    for f in factors:
        if f["pct"] < 50:
            if f["factor"] == "Savings Rate":
                rate = ctx["overview"]["savings_rate"]
                tips.append(f"Savings rate is {rate}%. Target 20%+ by reducing top spending categories.")
            elif f["factor"] == "Expense Stability":
                tips.append("Monthly expenses vary significantly. Setting budgets helps stabilize spending.")
            elif f["factor"] == "Income Consistency":
                tips.append("Income varies month to month. An emergency fund (3-6 months expenses) can reduce financial stress.")
            elif f["factor"] == "Category Diversification":
                cats = ctx["categories"]
                if cats:
                    top = cats[0]
                    tips.append(f"{top['category']} dominates at {top['percentage']}% of expenses. Diversifying reduces risk.")
    return tips[:3]


def analyze_spending(ctx: dict) -> dict:
    """Identify spending patterns and outliers."""
    symbol = ctx.get("currency_symbol", DEFAULT_CURRENCY_SYMBOL)
    categories = ctx["categories"]
    top_merchants = ctx["top_merchants"]
    overview = ctx["overview"]

    if not categories:
        return {"has_data": False}

    total = overview["expense"]
    top_category = categories[0] if categories else None
    discretionary_cats = ["Food", "Entertainment", "Shopping", "Subscriptions"]
    discretionary_total = sum(
        c["amount"] for c in categories if c["category"] in discretionary_cats
    )
    discretionary_pct = round(discretionary_total / total * 100, 1) if total > 0 else 0

    return {
        "has_data": True,
        "total_expense": total,
        "total_expense_fmt": _fmt(total, symbol),
        "top_category": top_category,
        "categories": categories[:8],
        "top_merchants": top_merchants[:6],
        "discretionary_total": discretionary_total,
        "discretionary_total_fmt": _fmt(discretionary_total, symbol),
        "discretionary_pct": discretionary_pct,
        "high_discretionary": discretionary_pct > 50,
    }


def search_transactions_by_merchant(
    user_id: int, db: Session, merchant_query: str, currency_symbol: str = DEFAULT_CURRENCY_SYMBOL
) -> dict:
    """Find transactions matching a merchant name."""
    q = merchant_query.lower().strip()
    matches = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.merchant.ilike(f"%{q}%"),
        )
        .all()
    )

    total = sum(t.amount for t in matches)
    count = len(matches)

    return {
        "merchant_query": merchant_query,
        "found": count,
        "total": total,
        "total_fmt": _fmt(total, currency_symbol),
        "transactions": [
            {
                "date": t.date.strftime("%d %b %Y"),
                "merchant": t.merchant,
                "amount_fmt": _fmt(t.amount, currency_symbol),
                "category": t.category,
            }
            for t in sorted(matches, key=lambda x: x.date, reverse=True)[:10]
        ],
    }


def get_used_services(intent: str) -> List[str]:
    """Return which services were used for a given intent."""
    SERVICE_MAP = {
        "financial_summary": ["analytics", "health_score", "budgets", "anomalies"],
        "health_score": ["health_score", "analytics"],
        "budget_analysis": ["budgets", "forecasting"],
        "forecast_analysis": ["budgets", "forecasting"],
        "spending_analysis": ["analytics", "transactions"],
        "transaction_search": ["transactions"],
        "anomaly_analysis": ["anomaly_detection"],
        "subscription_analysis": ["anomaly_detection", "transactions"],
        "savings_recommendation": ["analytics", "budgets", "transactions"],
        "general_finance_question": ["analytics"],
    }
    return SERVICE_MAP.get(intent, ["analytics"])
