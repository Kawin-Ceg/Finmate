from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    email_verified: bool
    created_at: datetime


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None


class AvatarResponse(BaseModel):
    avatar_url: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class SendOTPResponse(BaseModel):
    message: str
    email_sent: bool


class VerifyEmailRequest(BaseModel):
    otp: str


class SecurityScoreResponse(BaseModel):
    score: int
    grade: str
    factors: list[dict]
