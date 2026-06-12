from sqlalchemy import Boolean, Column, DateTime, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # General
    currency = Column(String(10), default="INR", nullable=False)
    timezone = Column(String(100), default="Asia/Kolkata", nullable=False)
    date_format = Column(String(20), default="DD/MM/YYYY", nullable=False)

    # Appearance
    theme = Column(String(20), default="system", nullable=False)  # light | dark | system

    # Notifications
    notif_budget_alerts = Column(Boolean, default=True, nullable=False)
    notif_anomaly_alerts = Column(Boolean, default=True, nullable=False)
    notif_monthly_reports = Column(Boolean, default=False, nullable=False)
    notif_financial_insights = Column(Boolean, default=False, nullable=False)
    notif_product_updates = Column(Boolean, default=False, nullable=False)

    # Privacy
    privacy_show_balances = Column(Boolean, default=True, nullable=False)
    privacy_show_amounts = Column(Boolean, default=True, nullable=False)
    privacy_mask_values = Column(Boolean, default=False, nullable=False)
    privacy_mode = Column(Boolean, default=False, nullable=False)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="settings", uselist=False)
