from pydantic import BaseModel


class OverviewResponse(BaseModel):
    income: float
    expense: float
    savings: float
    savings_rate: float


class MonthlyTrendItem(BaseModel):
    month: str
    spending: float


class MonthlyTrendResponse(BaseModel):
    data: list[MonthlyTrendItem]


class CategoryBreakdownItem(BaseModel):
    category: str
    amount: float
    percentage: float
    count: int


class CategoryBreakdownResponse(BaseModel):
    data: list[CategoryBreakdownItem]


class TopMerchantItem(BaseModel):
    merchant: str
    total_amount: float
    transaction_count: int


class TopMerchantsResponse(BaseModel):
    data: list[TopMerchantItem]


class CashflowItem(BaseModel):
    month: str
    income: float
    expense: float


class CashflowResponse(BaseModel):
    data: list[CashflowItem]


class HeatmapItem(BaseModel):
    day: str
    average_spending: float
    total_spending: float
    transaction_count: int


class HeatmapResponse(BaseModel):
    data: list[HeatmapItem]


class HealthScoreBreakdown(BaseModel):
    savings_rate: float
    savings_rate_max: int
    expense_stability: float
    expense_stability_max: int
    income_consistency: float
    income_consistency_max: int
    diversification: float
    diversification_max: int


class HealthScoreResponse(BaseModel):
    score: int
    grade: str
    status: str
    breakdown: HealthScoreBreakdown
    insights: list[str]
