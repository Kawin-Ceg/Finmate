"""
Dashboard — Consolidated Overview
Dashboard.jsx previously fired 7 separate requests on every page load:
health-score, overview, budget forecast, anomalies, category breakdown,
monthly trend, and top merchants. This endpoint returns all seven payloads
in one round trip, in the exact shape the frontend already expects.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.anomaly import Anomaly
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewResponse
from app.services.analytics_service import (
    get_category_breakdown_sql,
    get_monthly_trend_sql,
    get_overview_sql,
    get_top_merchants_sql,
)
from app.services.budget_service import compute_forecast, generate_alerts
from app.services.health_score_service import compute_health_score

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    )
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    anomalies = (
        db.query(Anomaly)
        .filter(Anomaly.user_id == current_user.id)
        .order_by(Anomaly.score.desc())
        .all()
    )

    health = compute_health_score(transactions)
    overview = get_overview_sql(current_user.id, db)

    today = date.today()
    forecasts = [compute_forecast(b, transactions) for b in budgets]
    alerts = generate_alerts(forecasts)

    return DashboardOverviewResponse(
        health_score=health,
        overview=overview,
        forecast={
            "forecasts": forecasts,
            "alerts": alerts,
            "month": today.month,
            "year": today.year,
        },
        anomalies=anomalies,
        categories={"data": get_category_breakdown_sql(current_user.id, db)},
        monthly_trend={"data": get_monthly_trend_sql(current_user.id, db)},
        top_merchants={"data": get_top_merchants_sql(current_user.id, db)},
    )
