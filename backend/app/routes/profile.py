import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.profile import AvatarResponse, ProfileResponse, ProfileUpdate, SecurityScoreResponse

router = APIRouter(prefix="/profile", tags=["Profile"])

AVATAR_DIR = Path(__file__).resolve().parents[2] / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put("", response_model=ProfileResponse)
def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name is not None:
        name = body.name.strip()
        if len(name) < 1:
            raise HTTPException(status_code=400, detail="Name cannot be empty.")
        current_user.name = name

    if body.country is not None:
        current_user.country = body.country.strip() or None

    if body.bio is not None:
        current_user.bio = body.bio.strip()[:500] or None

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/avatar", response_model=AvatarResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, or GIF images are accepted.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{current_user.id}.{ext}"
    dest = AVATAR_DIR / filename

    # Remove old avatar if extension changed
    for old in AVATAR_DIR.glob(f"{current_user.id}.*"):
        if old != dest:
            old.unlink(missing_ok=True)

    with open(dest, "wb") as f:
        f.write(contents)

    avatar_url = f"/static/avatars/{filename}"
    current_user.avatar_url = avatar_url
    db.commit()

    return AvatarResponse(avatar_url=avatar_url)


@router.delete("/avatar")
def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.avatar_url:
        for old in AVATAR_DIR.glob(f"{current_user.id}.*"):
            old.unlink(missing_ok=True)
        current_user.avatar_url = None
        db.commit()
    return {"message": "Avatar removed."}


@router.get("/security-score", response_model=SecurityScoreResponse)
def security_score(
    current_user: User = Depends(get_current_user),
):
    score = 0
    factors = []

    if current_user.email_verified:
        score += 40
    else:
        factors.append({
            "text": "Verify your email address",
            "action": "verify_email",
            "impact": "+40 pts",
        })

    if current_user.avatar_url:
        score += 15
    else:
        factors.append({
            "text": "Add a profile photo",
            "action": "upload_avatar",
            "impact": "+15 pts",
        })

    if current_user.name and current_user.country:
        score += 20
    else:
        factors.append({
            "text": "Complete your profile (name & country)",
            "action": "edit_profile",
            "impact": "+20 pts",
        })

    # Password is always set — give base pts
    score += 25

    # Clamp
    score = min(100, score)

    if score >= 80:
        grade = "Excellent"
    elif score >= 60:
        grade = "Good"
    elif score >= 40:
        grade = "Fair"
    else:
        grade = "Needs attention"

    return SecurityScoreResponse(score=score, grade=grade, factors=factors)
