from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class CategoryFeedback(Base):
    __tablename__ = "category_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)

    merchant_name = Column(String(255), nullable=False)
    original_category = Column(String(100), nullable=False)
    corrected_category = Column(String(100), nullable=False)

    model_confidence = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    transaction = relationship("Transaction")
