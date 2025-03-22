from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import enum

# Enum for appointment status
class AppointmentStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"

# Response schema for appointments
class AppointmentResponseData(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    medical_issue: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Request schema for creating an appointment
class CreateAppointmentSchema(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    mobile_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")  # Phone number validation (optional international format)
    medical_issue: str
    message: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.active

# Request schema for updating an appointment (e.g., updating status or medical issue)
class UpdateAppointmentSchema(BaseModel):
    status: Optional[AppointmentStatus] = AppointmentStatus.active
    medical_issue: Optional[str] = None
    message: Optional[str] = None

# Response schema for a single appointment
class AppointmentResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile_number: str
    medical_issue: str
    message: Optional[str] = None
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Schema for listing appointments (if needed for list view)
class AppointmentListResponse(BaseModel):
    success: bool
    status: int
    message: str
    data: list[AppointmentResponse]

# Response schema for appointment status update
class AppointmentStatusUpdateResponse(BaseModel):
    success: bool
    status: int
    message: str
    data: AppointmentResponse

# Schema for appointment profile path update (if applicable)
class AppointmentProfilePathResponse(BaseModel):
    success: bool
    status: int
    message: str
    data: dict

