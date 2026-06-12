from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id"),
        nullable=True,
    )

    type = Column(String(50), nullable=False)          # transaction | category | merchant | subscription | budget
    severity = Column(String(20), nullable=False)      # low | medium | high | critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    score = Column(Float, nullable=False, default=0.0)  # 0–100
    meta_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="anomalies")
