from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    date = Column(
        Date,
        nullable=False
    )

    merchant = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    amount = Column(
        Float,
        nullable=False
    )

    transaction_type = Column(
        String(10),
        nullable=False,
        default="debit"
    )

    category = Column(
        String(100),
        nullable=False,
        default="Other"
    )

    source_file = Column(
        String(255),
        nullable=True
    )

    predicted_category = Column(
        String(100),
        nullable=True
    )

    prediction_confidence = Column(
        Float,
        nullable=True
    )

    categorization_method = Column(
        String(20),
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        back_populates="transactions"
    )
