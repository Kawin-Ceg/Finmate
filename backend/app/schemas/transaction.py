from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional, List

VALID_CATEGORIES = {
    "Food", "Transport", "Shopping", "Utilities", "Health", "Insurance",
    "Investment", "Income", "Education", "Rent", "Entertainment",
    "Subscriptions", "Transfers", "Cash", "Other"
}


class CategoryFeedbackCreate(BaseModel):
    corrected_category: str = Field(..., description="The correct category for this transaction")

    def validate_category(self) -> None:
        if self.corrected_category not in VALID_CATEGORIES:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail=f"Invalid category. Must be one of: {sorted(VALID_CATEGORIES)}"
            )


class CategoryFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: int
    merchant_name: str
    original_category: str
    corrected_category: str
    created_at: datetime


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
    duplicates_skipped: int = 0


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
