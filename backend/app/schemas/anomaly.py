from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: Optional[int] = None
    type: str
    severity: str
    title: str
    description: str
    score: float
    meta_data: Optional[Any] = None
    created_at: datetime


class AnomalySummaryResponse(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int
    last_analyzed: Optional[datetime] = None


class AnomalyTypeCount(BaseModel):
    type: str
    count: int


class AnomalyStatsResponse(BaseModel):
    by_type: list[AnomalyTypeCount]
    by_severity: dict[str, int]
    highest_score: float
    total: int


class SubscriptionItem(BaseModel):
    merchant: str
    monthly_cost: float
    annual_cost: float
    occurrence_count: int
    avg_amount: float
    category: Optional[str] = None
    anomaly_id: int


class SubscriptionsResponse(BaseModel):
    subscriptions: list[SubscriptionItem]
    total_monthly_cost: float
    total_annual_cost: float
    count: int


class RunAnomalyResponse(BaseModel):
    message: str
    anomalies_detected: int
