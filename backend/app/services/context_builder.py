"""
Context Builder
Assembles a structured financial context dict from all FinMate engines.
This is what gets injected into the LLM prompt.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.user_settings import UserSettings
from app.services.analytics_service import (
    get_category_breakdown,
    get_monthly_trend,
    get_overview,
    get_top_merchants,
)
from app.services.budget_service import compute_budget_progress, compute_forecast
from app.services.health_score_service import compute_health_score

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "AUD": "A$",
    "CAD": "C$",
    "SGD": "S$",
}
DEFAULT_CURRENCY_SYMBOL = "₹"
DEFAULT_TIMEZONE = "Asia/Kolkata"


def _fmt(amount: float, symbol: str = DEFAULT_CURRENCY_SYMBOL) -> str:
    return f"{symbol}{amount:,.2f}"


def build_context(user_id: int, db: Session, intent: str = "") -> dict:
    """Return a rich financial context dict for the given user."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    currency_symbol = CURRENCY_SYMBOLS.get(
        (settings.currency if settings else "INR"), DEFAULT_CURRENCY_SYMBOL
    )
    try:
        tz = ZoneInfo(settings.timezone if settings and settings.timezone else DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo(DEFAULT_TIMEZONE)

    all_txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    recent_anomalies = (
        db.query(Anomaly)
        .filter(Anomaly.user_id == user_id)
        .order_by(Anomaly.created_at.desc())
        .limit(10)
        .all()
    )

    today = datetime.now(tz).date()
    cutoff_30 = today - timedelta(days=30)
    cutoff_90 = today - timedelta(days=90)

    txns_30d = [t for t in all_txns if t.date >= cutoff_30]
    txns_90d = [t for t in all_txns if t.date >= cutoff_90]

    # Overview (30-day window)
    overview = get_overview(txns_30d) if txns_30d else {"income": 0, "expense": 0, "savings": 0, "savings_rate": 0}

    # Health score (all-time for stability)
    health = compute_health_score(all_txns) if all_txns else {"score": 0, "grade": "N/A", "status": "No data", "insights": []}

    # Category breakdown (30d)
    categories = get_category_breakdown(txns_30d) if txns_30d else []

    # Top merchants (30d)
    top_merchants = get_top_merchants(txns_30d, limit=8) if txns_30d else []

    # Monthly trend (90d)
    monthly_trend = get_monthly_trend(txns_90d) if txns_90d else []

    # Budget progress + forecasts
    budget_data = []
    for b in budgets:
        progress = compute_budget_progress(b, all_txns)
        forecast = compute_forecast(b, all_txns)
        budget_data.append({**progress, "forecast": forecast})

    # Recent transactions (last 20 debits)
    recent_txns = sorted(
        [t for t in all_txns if t.transaction_type == "debit"],
        key=lambda t: t.date,
        reverse=True,
    )[:20]

    # Subscriptions detected via anomaly engine
    subscriptions = [
        {
            "merchant": a.title.replace("Subscription: ", ""),
            "amount": a.meta_data.get("avg_amount", 0) if a.meta_data else 0,
        }
        for a in recent_anomalies
        if a.type == "subscription"
    ]

    # Anomaly summary
    anomaly_summary = [
        {
            "type": a.type,
            "severity": a.severity,
            "title": a.title,
            "description": a.description,
            "score": a.score,
        }
        for a in recent_anomalies
    ]

    # Build narrative context strings for LLM
    ctx = {
        "has_data": bool(all_txns),
        "data_window": "last 30 days",
        "today": today.strftime("%B %d, %Y"),
        "currency_symbol": currency_symbol,
        "overview": {
            "income": overview["income"],
            "expense": overview["expense"],
            "savings": overview["savings"],
            "savings_rate": overview["savings_rate"],
            "income_fmt": _fmt(overview["income"], currency_symbol),
            "expense_fmt": _fmt(overview["expense"], currency_symbol),
            "savings_fmt": _fmt(overview["savings"], currency_symbol),
        },
        "health": {
            "score": health["score"],
            "grade": health["grade"],
            "status": health["status"],
            "insights": health.get("insights", []),
            "breakdown": health.get("breakdown", {}),
        },
        "categories": categories[:10],
        "top_merchants": top_merchants,
        "monthly_trend": monthly_trend,
        "budgets": budget_data,
        "recent_transactions": [
            {
                "date": t.date.strftime("%d %b %Y"),
                "merchant": t.merchant,
                "amount": t.amount,
                "amount_fmt": _fmt(t.amount, currency_symbol),
                "category": t.category,
            }
            for t in recent_txns
        ],
        "anomalies": anomaly_summary,
        "subscriptions": subscriptions,
        "total_transactions": len(all_txns),
        "total_budgets": len(budgets),
        "total_anomalies": len(recent_anomalies),
    }

    return ctx


def context_to_prompt_text(ctx: dict) -> str:
    """Convert context dict to a readable text block for the LLM system prompt."""
    if not ctx["has_data"]:
        return "The user has no transaction data yet. Encourage them to upload their bank statement CSV."

    sym = ctx.get("currency_symbol", DEFAULT_CURRENCY_SYMBOL)

    lines = [
        f"=== FINANCIAL CONTEXT (as of {ctx['today']}) ===",
        "",
        f"OVERVIEW (Last 30 days):",
        f"  Income:   {ctx['overview']['income_fmt']}",
        f"  Expenses: {ctx['overview']['expense_fmt']}",
        f"  Savings:  {ctx['overview']['savings_fmt']} ({ctx['overview']['savings_rate']}% savings rate)",
        "",
        f"FINANCIAL HEALTH SCORE: {ctx['health']['score']}/100 ({ctx['health']['grade']} — {ctx['health']['status']})",
    ]

    if ctx["health"]["insights"]:
        lines.append("  Key Insights:")
        for ins in ctx["health"]["insights"]:
            lines.append(f"    • {ins}")

    if ctx["health"]["breakdown"]:
        bd = ctx["health"]["breakdown"]
        lines.append(f"  Score Breakdown: Savings Rate {bd.get('savings_rate',0)}/{bd.get('savings_rate_max',35)} pts | "
                     f"Expense Stability {bd.get('expense_stability',0)}/{bd.get('expense_stability_max',25)} pts | "
                     f"Income Consistency {bd.get('income_consistency',0)}/{bd.get('income_consistency_max',25)} pts | "
                     f"Diversification {bd.get('diversification',0)}/{bd.get('diversification_max',15)} pts")

    lines.append("")
    if ctx["categories"]:
        lines.append("TOP SPENDING CATEGORIES (last 30 days):")
        for c in ctx["categories"][:6]:
            lines.append(f"  {c['category']:20s} {sym}{c['amount']:>10,.2f}  ({c['percentage']}%)")

    lines.append("")
    if ctx["top_merchants"]:
        lines.append("TOP MERCHANTS:")
        for m in ctx["top_merchants"][:5]:
            lines.append(f"  {m['merchant']:25s} {sym}{m.get('total_amount', 0):>10,.2f}")

    if ctx["budgets"]:
        lines.append("")
        lines.append("BUDGET STATUS:")
        for b in ctx["budgets"]:
            risk_emoji = {"safe": "✓", "watch": "⚠", "high": "!", "exceeded": "✗"}.get(b["risk"], "?")
            lines.append(
                f"  [{risk_emoji}] {b['category']:20s} {sym}{b['current_spend']:>8,.2f} / {sym}{b['monthly_limit']:>8,.2f}"
                f"  ({b['pct_used']:.0f}%)  — Projected: {sym}{b['forecast']['projected_spend']:,.2f}"
            )

    if ctx["anomalies"]:
        lines.append("")
        lines.append("RECENT ANOMALIES / FLAGS:")
        for a in ctx["anomalies"][:5]:
            lines.append(f"  [{a['severity'].upper()}] {a['title']}: {a['description'][:100]}")

    if ctx["subscriptions"]:
        lines.append("")
        lines.append("DETECTED SUBSCRIPTIONS:")
        for s in ctx["subscriptions"]:
            lines.append(f"  {s['merchant']:25s} ~{sym}{s['amount']:,.0f}/mo")

    if ctx["monthly_trend"]:
        lines.append("")
        lines.append("MONTHLY SPENDING TREND:")
        for m in ctx["monthly_trend"][-4:]:
            lines.append(f"  {m['month']:10s} {sym}{m['spending']:>10,.2f}")

    return "\n".join(lines)
