from sqlalchemy import Boolean, Column, DateTime, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    token_hash = Column(String(128), nullable=False, index=True)  # SHA-256 of JWT
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    last_used = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sessions")
