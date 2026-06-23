import csv
import io
from math import ceil
from datetime import datetime, date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import extract, or_
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.transaction import Transaction
from app.models.user import User
from app.models.category_feedback import CategoryFeedback
from app.schemas.transaction import (
    CategoryFeedbackCreate,
    CategoryFeedbackResponse,
    TransactionListResponse,
    TransactionSummaryResponse,
    TransactionUploadResponse,
)
from app.services.categorizer import categorize_with_confidence
from app.services.anomaly_service import run_anomaly_detection

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

DATE_FORMATS = [
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%m/%d/%Y",
    "%d/%m/%y",
    "%Y/%m/%d",
]


def _parse_date(value: str) -> date_type:
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: '{value}'")


def _parse_amount(value: str) -> float:
    cleaned = (
        value.strip()
        .replace(",", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    return float(cleaned)


def _find_column(fieldnames: list, patterns: list) -> Optional[str]:
    for field in fieldnames:
        norm = field.strip().lower().replace(" ", "_").replace("-", "_")
        for pattern in patterns:
            if pattern in norm:
                return field
    return None


@router.post("/upload", response_model=TransactionUploadResponse)
async def upload_transactions(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are accepted."
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    text = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to decode file. Save the CSV as UTF-8 and try again."
        )

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file has no headers.")

    original_fields = list(reader.fieldnames)

    date_col = _find_column(
        original_fields,
        ["date", "txn_date", "transaction_date", "value_date", "posting_date"]
    )
    merchant_col = _find_column(
        original_fields,
        ["merchant", "payee", "name", "narration", "particulars", "description", "details"]
    )
    desc_col = _find_column(
        original_fields,
        ["description", "desc", "remarks", "note", "reference"]
    )
    amount_col = _find_column(
        original_fields,
        ["amount", "transaction_amount", "net_amount", "txn_amount"]
    )
    debit_col = _find_column(
        original_fields,
        ["debit", "dr", "withdrawal", "withdrawn", "debit_amount"]
    )
    credit_col = _find_column(
        original_fields,
        ["credit", "cr", "deposit", "deposited", "credit_amount"]
    )

    if not date_col:
        raise HTTPException(
            status_code=400,
            detail="CSV missing a date column. Expected: date, txn_date, or transaction_date."
        )

    if not merchant_col:
        raise HTTPException(
            status_code=400,
            detail="CSV missing a merchant column. Expected: merchant, payee, narration, or particulars."
        )

    if not amount_col and not (debit_col or credit_col):
        raise HTTPException(
            status_code=400,
            detail="CSV must have an 'amount' column, or separate 'debit' and 'credit' columns."
        )

    existing_signatures = {
        (d, (m or "").strip().lower(), round(a, 2))
        for d, m, a in db.query(
            Transaction.date, Transaction.merchant, Transaction.amount
        ).filter(Transaction.user_id == current_user.id)
    }

    imported = 0
    duplicates_skipped = 0
    parse_errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            raw_date = row.get(date_col, "").strip()
            if not raw_date:
                continue

            txn_date = _parse_date(raw_date)

            merchant = row.get(merchant_col, "").strip() or "Unknown"
            description = row.get(desc_col, "").strip() if desc_col and desc_col != merchant_col else None

            if amount_col:
                raw_amount = row.get(amount_col, "").strip()
                if not raw_amount:
                    continue
                signed_amount = _parse_amount(raw_amount)
                txn_type = "credit" if signed_amount >= 0 else "debit"
                abs_amount = abs(signed_amount)
            else:
                debit_raw = row.get(debit_col, "").strip() if debit_col else ""
                credit_raw = row.get(credit_col, "").strip() if credit_col else ""
                debit_amt = _parse_amount(debit_raw) if debit_raw else 0.0
                credit_amt = _parse_amount(credit_raw) if credit_raw else 0.0

                if credit_amt > 0:
                    txn_type = "credit"
                    abs_amount = credit_amt
                else:
                    txn_type = "debit"
                    abs_amount = debit_amt

            if abs_amount == 0:
                continue

            signature = (txn_date, merchant.strip().lower(), round(abs_amount, 2))
            if signature in existing_signatures:
                duplicates_skipped += 1
                continue
            existing_signatures.add(signature)

            cat_result = categorize_with_confidence(merchant, description or "")

            transaction = Transaction(
                user_id=current_user.id,
                date=txn_date,
                merchant=merchant,
                description=description,
                amount=abs_amount,
                transaction_type=txn_type,
                category=cat_result["category"],
                source_file=file.filename,
                predicted_category=cat_result["category"],
                prediction_confidence=cat_result.get("confidence"),
                categorization_method=cat_result["method"],
            )
            db.add(transaction)
            imported += 1

        except Exception as exc:
            parse_errors.append(f"Row {row_num}: {exc}")
            continue

    if imported == 0 and duplicates_skipped == 0:
        db.rollback()
        detail = "No valid transactions found in the file."
        if parse_errors:
            detail += f" Errors: {'; '.join(parse_errors[:3])}"
        raise HTTPException(status_code=400, detail=detail)

    db.commit()

    if imported > 0:
        try:
            run_anomaly_detection(current_user.id, db)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Anomaly detection failed after upload: %s", exc)

    if imported == 0:
        message = f"All {duplicates_skipped} row(s) already exist — nothing new imported."
    elif duplicates_skipped > 0:
        message = f"Upload successful — {imported} imported, {duplicates_skipped} duplicate(s) skipped."
    else:
        message = "Upload successful"

    return TransactionUploadResponse(
        message=message,
        transactions_imported=imported,
        duplicates_skipped=duplicates_skipped,
    )


@router.get("/summary", response_model=TransactionSummaryResponse)
def get_summary(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    if month:
        query = query.filter(extract("month", Transaction.date) == month)
    if year:
        query = query.filter(extract("year", Transaction.date) == year)

    transactions = query.all()

    total_spending = sum(
        t.amount for t in transactions if t.transaction_type == "debit"
    )
    total_income = sum(
        t.amount for t in transactions if t.transaction_type == "credit"
    )

    category_totals: dict = {}
    for t in transactions:
        if t.transaction_type == "debit":
            category_totals[t.category] = (
                category_totals.get(t.category, 0) + t.amount
            )

    top_category = (
        max(category_totals, key=lambda k: category_totals[k])
        if category_totals
        else None
    )

    largest_expense = max(
        (t.amount for t in transactions if t.transaction_type == "debit"),
        default=0.0
    )

    return TransactionSummaryResponse(
        total_transactions=len(transactions),
        total_spending=round(total_spending, 2),
        total_income=round(total_income, 2),
        top_category=top_category,
        largest_expense=round(largest_expense, 2)
    )


@router.get("/categories")
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Transaction.category)
        .filter(Transaction.user_id == current_user.id)
        .distinct()
        .order_by(Transaction.category)
        .all()
    )
    return [r[0] for r in rows]


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.merchant.ilike(term),
                Transaction.description.ilike(term),
                Transaction.category.ilike(term)
            )
        )

    if category:
        query = query.filter(Transaction.category == category)

    if month:
        query = query.filter(extract("month", Transaction.date) == month)

    if year:
        query = query.filter(extract("year", Transaction.date) == year)

    total = query.count()
    transactions = (
        query
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        limit=limit,
        total_pages=ceil(total / limit) if total > 0 else 1
    )


@router.post("/{transaction_id}/feedback", response_model=CategoryFeedbackResponse)
def submit_category_feedback(
    transaction_id: int,
    payload: CategoryFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a user correction on a transaction's ML-assigned category."""
    payload.validate_category()

    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    if txn.category == payload.corrected_category:
        raise HTTPException(
            status_code=400,
            detail="Corrected category is the same as the current category — no change needed."
        )

    original_category = txn.category

    # Update the transaction's category immediately
    txn.category = payload.corrected_category
    txn.categorization_method = "user_corrected"

    # Record the correction for future model retraining
    feedback = CategoryFeedback(
        user_id=current_user.id,
        transaction_id=transaction_id,
        merchant_name=txn.merchant,
        original_category=original_category,
        corrected_category=payload.corrected_category,
        model_confidence=txn.prediction_confidence,
        model_version="v2",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
