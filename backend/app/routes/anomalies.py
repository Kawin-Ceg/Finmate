from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.dependencies import get_current_user
from app.models.anomaly import Anomaly
from app.models.user import User
from app.schemas.anomaly import (
    AnomalyResponse,
    AnomalySummaryResponse,
    AnomalyStatsResponse,
    AnomalyTypeCount,
    SubscriptionItem,
    SubscriptionsResponse,
    RunAnomalyResponse,
)
from app.services.anomaly_service import run_anomaly_detection

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[AnomalyResponse])
def list_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """All anomalies for the authenticated user, sorted by score descending."""
    return (
        db.query(Anomaly)
        .filter(Anomaly.user_id == current_user.id)
        .order_by(Anomaly.score.desc())
        .all()
    )


@router.get("/summary", response_model=AnomalySummaryResponse)
def anomaly_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Count of anomalies by severity + timestamp of last detection run."""
    rows = (
        db.query(Anomaly)
        .filter(Anomaly.user_id == current_user.id)
        .all()
    )
    counts: dict[str, int] = Counter(r.severity for r in rows)
    last = max((r.created_at for r in rows), default=None)

    return AnomalySummaryResponse(
        total=len(rows),
        critical=counts.get("critical", 0),
        high=counts.get("high", 0),
        medium=counts.get("medium", 0),
        low=counts.get("low", 0),
        last_analyzed=last,
    )


@router.get("/stats", response_model=AnomalyStatsResponse)
def anomaly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Breakdown by type and severity, plus highest risk score."""
    rows = (
        db.query(Anomaly)
        .filter(Anomaly.user_id == current_user.id)
        .all()
    )
    type_counts = Counter(r.type for r in rows)
    sev_counts = Counter(r.severity for r in rows)
    highest = max((r.score for r in rows), default=0.0)

    return AnomalyStatsResponse(
        by_type=[
            AnomalyTypeCount(type=t, count=c)
            for t, c in type_counts.most_common()
        ],
        by_severity=dict(sev_counts),
        highest_score=round(highest, 1),
        total=len(rows),
    )


@router.get("/subscriptions", response_model=SubscriptionsResponse)
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all detected subscription anomalies with cost breakdown."""
    rows = (
        db.query(Anomaly)
        .filter(
            Anomaly.user_id == current_user.id,
            Anomaly.type == "subscription",
        )
        .order_by(Anomaly.score.desc())
        .all()
    )

    items: list[SubscriptionItem] = []
    total_monthly = 0.0
    total_annual = 0.0

    for row in rows:
        meta = row.meta_data or {}
        monthly = float(meta.get("monthly_cost", 0))
        annual = float(meta.get("annual_cost", 0))
        total_monthly += monthly
        total_annual += annual
        items.append(
            SubscriptionItem(
                merchant=meta.get("merchant", row.title),
                monthly_cost=monthly,
                annual_cost=annual,
                occurrence_count=int(meta.get("occurrence_count", 0)),
                avg_amount=float(meta.get("avg_amount", monthly)),
                category=meta.get("category"),
                anomaly_id=row.id,
            )
        )

    return SubscriptionsResponse(
        subscriptions=items,
        total_monthly_cost=round(total_monthly, 2),
        total_annual_cost=round(total_annual, 2),
        count=len(items),
    )


@router.post("/run", response_model=RunAnomalyResponse)
def trigger_anomaly_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger anomaly re-detection for the current user."""
    count = run_anomaly_detection(current_user.id, db)
    return RunAnomalyResponse(
        message=f"Detection complete. {count} anomalies found.",
        anomalies_detected=count,
    )
