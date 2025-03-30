from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# from .models import Base  # Ensure this imports from the correct place
from sqlalchemy.ext.declarative import declarative_base
from src.routers.users.models.users import User


Base = declarative_base()

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    cf_link_id = Column(String(50), unique=True)  # Cashfree generated ID
    transaction_id = Column(String(100), unique=True, nullable=True)  # Optional transaction ID
    link_id = Column(String(50))  # Newly added column
    link_url = Column(Text)  # Payment link URL
    amount = Column(Numeric(10,2), nullable=False)  # Payment Amount
    currency = Column(String(10), default="INR")  # Currency (Default INR)
    status = Column(String(20), default="pending")  # Payment Status
    link_status = Column(String(20))  # Link Status (ACTIVE, EXPIRED, etc.)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())



    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
