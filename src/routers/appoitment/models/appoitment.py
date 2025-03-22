from sqlalchemy import Column, Integer, String, Text, Enum, TIMESTAMP
from sqlalchemy.orm import validates
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum
import re

Base = declarative_base()

class AppointmentStatus(enum.Enum):
    active = "active"
    inactive = "inactive"

class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    mobile_number = Column(String(15), nullable=False)
    medical_issue = Column(Text, nullable=False)
    message = Column(Text)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.active)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email address")
        return email

    @validates('mobile_number')
    def validate_mobile_number(self, key, mobile_number):
        if not re.match(r"^\+?[1-9]\d{1,14}$", mobile_number):
            raise ValueError("Invalid mobile number")
        return mobile_number

    def __repr__(self):
        return f"<Appointment(id={self.id}, name={self.name}, email={self.email}, mobile_number={self.mobile_number}, status={self.status})>"
