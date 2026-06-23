from __future__ import annotations

from typing import List

from pydantic import BaseModel

from app.schemas.analytics import (
    CategoryBreakdownItem,
    HealthScoreResponse,
    MonthlyTrendItem,
    OverviewResponse,
    TopMerchantItem,
)
from app.schemas.anomaly import AnomalyResponse
from app.schemas.budget import BudgetForecastResponse


class CategoryBreakdownData(BaseModel):
    data: List[CategoryBreakdownItem]


class MonthlyTrendData(BaseModel):
    data: List[MonthlyTrendItem]


class TopMerchantsData(BaseModel):
    data: List[TopMerchantItem]


class DashboardOverviewResponse(BaseModel):
    """
    Single consolidated payload for the dashboard landing page.
    Mirrors the exact shape of the 7 separate calls it replaces:
    /analytics/health-score, /analytics/overview, /budgets/forecast,
    /anomalies, /analytics/category-breakdown, /analytics/monthly-trend,
    /analytics/top-merchants.
    """

    health_score: HealthScoreResponse
    overview: OverviewResponse
    forecast: BudgetForecastResponse
    anomalies: List[AnomalyResponse]
    categories: CategoryBreakdownData
    monthly_trend: MonthlyTrendData
    top_merchants: TopMerchantsData
