import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.user_session import UserSession

router = APIRouter(prefix="/security", tags=["Security"])


def _current_token_hash(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    return hashlib.sha256(token.encode()).hexdigest()


@router.get("/sessions")
def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
        )
        .order_by(UserSession.created_at.desc())
        .all()
    )
    current_hash = _current_token_hash(request)

    return [
        {
            "id": s.id,
            "device_info": s.device_info or "Unknown device",
            "ip_address": s.ip_address or "—",
            "is_current": s.token_hash == current_hash,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "last_used": s.last_used.isoformat() if s.last_used else None,
        }
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(UserSession)
        .filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    current_hash = _current_token_hash(request)
    if session.token_hash == current_hash:
        raise HTTPException(status_code=400, detail="Cannot revoke the current session.")

    session.is_active = False
    db.commit()
    return {"message": "Session revoked."}


@router.delete("/sessions")
def revoke_all_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_hash = _current_token_hash(request)
    (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
            UserSession.token_hash != current_hash,
        )
        .update({"is_active": False}, synchronize_session=False)
    )
    db.commit()
    return {"message": "All other sessions revoked."}
