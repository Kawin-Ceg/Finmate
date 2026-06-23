from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional


class BudgetCreate(BaseModel):
    category: str
    monthly_limit: float = Field(gt=0, description="Must be greater than 0")


class BudgetUpdate(BaseModel):
    monthly_limit: float = Field(gt=0, description="Must be greater than 0")


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    monthly_limit: float
    created_at: datetime
    updated_at: Optional[datetime] = None


class BudgetWithProgress(BaseModel):
    """Budget with real-time spend computed from transactions."""

    id: int
    category: str
    monthly_limit: float
    current_spend: float
    remaining: float
    pct_used: float        # 0-100
    risk: str              # safe | watch | high | exceeded
    created_at: datetime


class BudgetOverviewResponse(BaseModel):
    total_budget: float
    total_spent: float
    remaining: float
    at_risk_count: int


class BudgetForecastItem(BaseModel):
    category: str
    budget: float
    current_spend: float
    projected_spend: float
    lower_bound: float
    upper_bound: float
    exceed_probability: float
    expected_overrun: float
    risk: str
    daily_rate: float
    days_remaining: int
    forecast_method: str
    explanation: str


class BudgetForecastResponse(BaseModel):
    forecasts: List[BudgetForecastItem]
    alerts: List[str]
    month: int
    year: int
