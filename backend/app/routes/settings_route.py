from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.settings_schema import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


def _get_or_create_settings(user_id: int, db: Session) -> UserSettings:
    s = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not s:
        s = UserSettings(user_id=user_id)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("", response_model=SettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_or_create_settings(current_user.id, db)


@router.put("", response_model=SettingsResponse)
def update_settings(
    body: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = _get_or_create_settings(current_user.id, db)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(s, field, value)

    db.commit()
    db.refresh(s)
    return s
