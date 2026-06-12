from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    merchant: str
    description: Optional[str] = None
    amount: float
    transaction_type: str
    category: str
    source_file: Optional[str] = None
    predicted_category: Optional[str] = None
    prediction_confidence: Optional[float] = None
    categorization_method: Optional[str] = None
    created_at: datetime


class TransactionUploadResponse(BaseModel):
    message: str
    transactions_imported: int


class TransactionSummaryResponse(BaseModel):
    total_transactions: int
    total_spending: float
    total_income: float
    top_category: Optional[str] = None
    largest_expense: float


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    limit: int
    total_pages: int
