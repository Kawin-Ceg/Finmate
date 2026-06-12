import csv
import io
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.anomaly import Anomaly
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_session import UserSession
from app.models.user_settings import UserSettings
from app.schemas.settings_schema import DeleteAccountRequest, ExportRequest
from app.utils.auth import verify_password

router = APIRouter(prefix="/account", tags=["Account"])

AVATAR_DIR = Path(__file__).resolve().parents[2] / "static" / "avatars"


@router.post("/export")
def export_data(
    body: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.date.desc())
        .all()
    )
    budgets = (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id)
        .all()
    )

    if body.format == "json":
        payload = {
            "user": {"name": current_user.name, "email": current_user.email},
            "transactions": [
                {
                    "date": str(t.date),
                    "merchant": t.merchant,
                    "amount": float(t.amount),
                    "type": t.transaction_type,
                    "category": t.category,
                    "description": t.description,
                }
                for t in transactions
            ],
            "budgets": [
                {
                    "category": b.category,
                    "monthly_limit": float(b.monthly_limit),
                }
                for b in budgets
            ],
        }
        content = json.dumps(payload, indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=finmate_export.json"},
        )

    # Default: CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Merchant", "Amount", "Type", "Category", "Description"])
    for t in transactions:
        writer.writerow([
            str(t.date),
            t.merchant or "",
            float(t.amount),
            t.transaction_type,
            t.category or "",
            t.description or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=finmate_transactions.csv"},
    )


@router.delete("")
def delete_account(
    body: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password.")

    # Remove avatar file
    if current_user.avatar_url:
        for f in AVATAR_DIR.glob(f"{current_user.id}.*"):
            f.unlink(missing_ok=True)

    # SQLAlchemy cascade deletes transactions, budgets, anomalies, settings, sessions
    db.delete(current_user)
    db.commit()

    return {"message": "Account permanently deleted."}
