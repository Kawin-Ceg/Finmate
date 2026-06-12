from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetForecastResponse,
    BudgetOverviewResponse,
    BudgetResponse,
    BudgetUpdate,
    BudgetWithProgress,
)
from app.services.budget_service import (
    compute_budget_progress,
    compute_forecast,
    generate_alerts,
)
from datetime import date

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def _user_txns(user: User, db: Session) -> list:
    return db.query(Transaction).filter(Transaction.user_id == user.id).all()


def _get_budget_or_404(budget_id: int, user: User, db: Session) -> Budget:
    b = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user.id,
    ).first()
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found.")
    return b


# ── GET /budgets/overview  (must be before /{budget_id} routes) ─────────────

@router.get("/overview", response_model=BudgetOverviewResponse)
def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    if not budgets:
        return BudgetOverviewResponse(
            total_budget=0.0,
            total_spent=0.0,
            remaining=0.0,
            at_risk_count=0,
        )
    txns = _user_txns(current_user, db)
    progresses = [compute_budget_progress(b, txns) for b in budgets]
    total_budget = sum(p["monthly_limit"] for p in progresses)
    total_spent = sum(p["current_spend"] for p in progresses)
    at_risk = sum(1 for p in progresses if p["risk"] in ("high", "exceeded"))
    return BudgetOverviewResponse(
        total_budget=round(total_budget, 2),
        total_spent=round(total_spent, 2),
        remaining=round(total_budget - total_spent, 2),
        at_risk_count=at_risk,
    )


# ── GET /budgets/forecast ────────────────────────────────────────────────────

@router.get("/forecast", response_model=BudgetForecastResponse)
def get_forecast(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    today = date.today()
    if not budgets:
        return BudgetForecastResponse(
            forecasts=[],
            alerts=[],
            month=today.month,
            year=today.year,
        )
    txns = _user_txns(current_user, db)
    forecasts = [compute_forecast(b, txns) for b in budgets]
    alerts = generate_alerts(forecasts)
    return BudgetForecastResponse(
        forecasts=forecasts,
        alerts=alerts,
        month=today.month,
        year=today.year,
    )


# ── GET /budgets  (list) ─────────────────────────────────────────────────────

@router.get("", response_model=List[BudgetWithProgress])
def list_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    txns = _user_txns(current_user, db)
    return [compute_budget_progress(b, txns) for b in budgets]


# ── POST /budgets  (create) ──────────────────────────────────────────────────

@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.monthly_limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="Monthly limit must be greater than 0.",
        )
    existing = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.category == data.category,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A budget for '{data.category}' already exists.",
        )
    budget = Budget(
        user_id=current_user.id,
        category=data.category,
        monthly_limit=data.monthly_limit,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


# ── PUT /budgets/{budget_id}  (update) ───────────────────────────────────────

@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.monthly_limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="Monthly limit must be greater than 0.",
        )
    budget = _get_budget_or_404(budget_id, current_user, db)
    budget.monthly_limit = data.monthly_limit
    db.commit()
    db.refresh(budget)
    return budget


# ── DELETE /budgets/{budget_id} ──────────────────────────────────────────────

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = _get_budget_or_404(budget_id, current_user, db)
    db.delete(budget)
    db.commit()
