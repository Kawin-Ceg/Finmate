import hashlib
import os
import secrets
from datetime import datetime, timedelta
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.user_session import UserSession
from app.schemas.profile import (
    ChangePasswordRequest,
    SendOTPResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserCreate, UserLogin
from app.services.email_service import send_verification_otp
from app.utils.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


OTP_MAX_ATTEMPTS = 5
OTP_LOCKOUT_MINUTES = 15


def _gen_otp() -> str:
    # Cryptographically secure 6-digit code (100000-999999)
    return str(secrets.randbelow(900000) + 100000)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _create_default_settings(user_id: int, db: Session) -> None:
    if not db.query(UserSettings).filter(UserSettings.user_id == user_id).first():
        db.add(UserSettings(user_id=user_id))
        db.flush()


@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    db.flush()

    _create_default_settings(new_user.id, db)

    # Generate and send verification OTP immediately
    otp = _gen_otp()
    new_user.otp_code = otp
    new_user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    new_user.otp_sent_at = datetime.utcnow()

    db.commit()
    db.refresh(new_user)

    send_verification_otp(new_user.email, new_user.name, otp)

    return {"message": "Account created. Please verify your email."}


@router.post("/login")
def login(user: UserLogin, request: Request, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"user_id": db_user.id, "email": db_user.email})

    # Track session
    device_info = request.headers.get("User-Agent", "Unknown")[:500]
    ip_address = request.client.host if request.client else None

    session = UserSession(
        user_id=db_user.id,
        token_hash=_token_hash(access_token),
        device_info=device_info,
        ip_address=ip_address,
    )
    db.add(session)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "email_verified": db_user.email_verified,
            "avatar_url": db_user.avatar_url,
        },
    }


@router.post("/send-verification-otp", response_model=SendOTPResponse)
def send_otp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email is already verified.")

    # Rate limit: 60 seconds between sends
    if current_user.otp_sent_at:
        elapsed = (datetime.utcnow() - current_user.otp_sent_at).total_seconds()
        if elapsed < 60:
            wait = int(60 - elapsed)
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {wait} seconds before requesting a new code.",
            )

    otp = _gen_otp()
    current_user.otp_code = otp
    current_user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    current_user.otp_sent_at = datetime.utcnow()
    current_user.otp_failed_attempts = 0
    current_user.otp_locked_until = None
    db.commit()

    sent = send_verification_otp(current_user.email, current_user.name, otp)
    return SendOTPResponse(
        message="Verification code sent to your email." if sent else "Verification code printed to console (SMTP not configured).",
        email_sent=sent,
    )


@router.post("/verify-email")
def verify_email(
    body: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.email_verified:
        return {"message": "Email already verified."}

    if current_user.otp_locked_until and datetime.utcnow() < current_user.otp_locked_until:
        wait_minutes = ceil((current_user.otp_locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=429,
            detail=f"Too many incorrect attempts. Try again in {wait_minutes} minute(s).",
        )

    if not current_user.otp_code or not current_user.otp_expiry:
        raise HTTPException(status_code=400, detail="No verification code found. Request a new one.")

    if datetime.utcnow() > current_user.otp_expiry:
        raise HTTPException(status_code=400, detail="Code has expired. Request a new one.")

    if current_user.otp_code != body.otp.strip():
        current_user.otp_failed_attempts += 1
        if current_user.otp_failed_attempts >= OTP_MAX_ATTEMPTS:
            current_user.otp_locked_until = datetime.utcnow() + timedelta(minutes=OTP_LOCKOUT_MINUTES)
            current_user.otp_failed_attempts = 0
            db.commit()
            raise HTTPException(
                status_code=429,
                detail=f"Too many incorrect attempts. Try again in {OTP_LOCKOUT_MINUTES} minutes.",
            )
        db.commit()
        remaining = OTP_MAX_ATTEMPTS - current_user.otp_failed_attempts
        raise HTTPException(
            status_code=400,
            detail=f"Incorrect verification code. {remaining} attempt(s) remaining.",
        )

    current_user.email_verified = True
    current_user.verification_timestamp = datetime.utcnow()
    current_user.otp_code = None
    current_user.otp_expiry = None
    current_user.otp_failed_attempts = 0
    current_user.otp_locked_until = None
    db.commit()

    return {"message": "Email verified successfully."}


@router.post("/resend-otp", response_model=SendOTPResponse)
def resend_otp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return send_otp(current_user=current_user, db=db)


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    current_user.password_hash = hash_password(body.new_password)
    db.commit()

    return {"message": "Password updated successfully."}
