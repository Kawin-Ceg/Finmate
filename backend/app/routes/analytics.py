from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.analytics import (
    CashflowResponse,
    CategoryBreakdownResponse,
    HeatmapResponse,
    HealthScoreResponse,
    MonthlyTrendResponse,
    OverviewResponse,
    TopMerchantsResponse,
)
from app.services.analytics_service import (
    get_cashflow,
    get_category_breakdown,
    get_heatmap,
    get_monthly_trend,
    get_overview,
    get_top_merchants,
)
from app.services.health_score_service import compute_health_score

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _user_transactions(user: User, db: Session):
    return db.query(Transaction).filter(Transaction.user_id == user.id).all()


@router.get("/overview", response_model=OverviewResponse)
def analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_overview(_user_transactions(current_user, db))


@router.get("/monthly-trend", response_model=MonthlyTrendResponse)
def analytics_monthly_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"data": get_monthly_trend(_user_transactions(current_user, db))}


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
def analytics_category_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"data": get_category_breakdown(_user_transactions(current_user, db))}


@router.get("/top-merchants", response_model=TopMerchantsResponse)
def analytics_top_merchants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"data": get_top_merchants(_user_transactions(current_user, db))}


@router.get("/cashflow", response_model=CashflowResponse)
def analytics_cashflow(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"data": get_cashflow(_user_transactions(current_user, db))}


@router.get("/heatmap", response_model=HeatmapResponse)
def analytics_heatmap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"data": get_heatmap(_user_transactions(current_user, db))}


@router.get("/health-score", response_model=HealthScoreResponse)
def analytics_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return compute_health_score(_user_transactions(current_user, db))
