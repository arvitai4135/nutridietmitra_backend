from fastapi import APIRouter, Body, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from src.database import Database
from . import models
from . import schema
from src.utils.jwt import get_email_from_token
from loguru import logger as logging
from .controller import send_password_reset_email
from ..users.models import User
from . import controller
# Dependency to get database session
db_util = Database()

def get_db():
    db = db_util.get_session()
    try:
        yield db
    finally:
        db.close()

# Defining the appointment router
router = APIRouter(
    prefix="/api/appointments",
    tags=["Appointments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create", status_code=201)
def create_appointment(request: Request, appointment: schema.CreateAppointmentSchema, db: Session = Depends(get_db)):
    """
    Endpoint to create a new appointment.
    """
    try:
        # Log the appointment creation attempt
        logging.info(f"Appointment creation attempt for email: {appointment.email}, mobile: {appointment.mobile_number}")

        # Get the email from the token
        email = appointment.email
        # Check if the user already has an active appointment
        # existing_appointment = db.query(models.Appointment).filter(
        #     models.Appointment.email == email, models.Appointment.status == "active"
        # ).first()

        # if existing_appointment:
        #     return {
        #         "success": False,
        #         "status": 400,
        #         "message": "You already have an active appointment scheduled.You can update existing appointment.",
        #     }

        # Create the appointment instance
        new_appointment = models.Appointment(
            name=appointment.name,
            email=appointment.email,
            mobile_number=appointment.mobile_number,
            medical_issue=appointment.medical_issue,
            message=appointment.message,
            status=appointment.status,
        )

        # Add the new appointment to the database
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)
        controller.send_password_reset_email(email=email)
        
        # Return success response
        return {
            "success": True,
            "status": 201,
            "message": "Appointment created successfully.",
            "data": {
                "id": new_appointment.id,
                "name": new_appointment.name,
                "email": new_appointment.email,
                "mobile_number": new_appointment.mobile_number,
                "status": new_appointment.status,
            }
        }

    except Exception as e:
        logging.error(f"An error occurred during appointment creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )

@router.get("/active", status_code=200)
def get_active_appointment(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint to get the active appointment for the authenticated user.
    """
    try:
        # Get the email from the token
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization token missing",
            )
        token = token.split(" ")[1]  # Assuming token is passed as "Bearer <token>"
        email = get_email_from_token(token)

        # Check if the user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Query the active appointment for the authenticated user
        active_appointment = db.query(models.Appointment).filter(
            models.Appointment.email == email, models.Appointment.status == "active"
        ).first()

        # If no active appointment exists, return a message
        if not active_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active appointment found",
            )

        # Return the active appointment details
        return {
            "success": True,
            "status": 200,
            "message": "Active appointment found",
            "data": {
                "id": active_appointment.id,
                "name": active_appointment.name,
                "email": active_appointment.email,
                "mobile_number": active_appointment.mobile_number,
                "medical_issue": active_appointment.medical_issue,
                "message": active_appointment.message,
                "status": active_appointment.status,
            }
        }

    except Exception as e:
        logging.error(f"An error occurred while fetching active appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )

from src.routers.users.schemas import UserRoleEnum  # Make sure you import UserRole if it's an enum
@router.get("/appointments", status_code=200)
def get_all_appointments(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint for admin to get the list of all appointments.
    """
    try:
        # Get the email from the token
        token = request.headers.get("Authorization")
        if not token:
            return {
                "success": False,
                "status": 401,
                "message": "Authorization token missing",
                "data": None
            }
        
        token = token.split(" ")[1]  # Assuming token is passed as "Bearer <token>"
        email = get_email_from_token(token)

        # Check if the user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {
                "success": False,
                "status": 404,
                "message": "User not found",
                "data": None
            }

        # Log the user's role to diagnose the issue
        logging.info(f"User role: {user.role}")

        # Check if user is admin
        if user.role != "admin":
            return {
            "success": False,
                "status": 403,
                "message": "You are not authorized to access this resource",
                "data": None
                }

        # Query all appointments
        appointments = db.query(models.Appointment).all()

        if not appointments:
            return {
                "success": False,
                "status": 404,
                "message": "No appointments found",
                "data": []
            }

        # Prepare the appointment list
        appointments_list = []
        for appointment in appointments:
            appointments_list.append({
                "id": appointment.id,
                "name": appointment.name,
                "email": appointment.email,
                "mobile_number": appointment.mobile_number,
                "medical_issue": appointment.medical_issue,
                "message": appointment.message,
                "dates_time": appointment.created_at.strftime('%b %d, %Y, %I:%M %p'),
                "status": appointment.status,
            })

        return {
            "success": True,
            "status": 200,
            "message": "Appointments fetched successfully",
            "data": appointments_list
        }

    except Exception as e:
        logging.error(f"An error occurred while fetching appointments: {e}")
        return {
            "success": False,
            "status": 500,
            "message": "An unexpected error occurred. Please try again later.",
            "data": None
        }


@router.delete("/delete/{appointment_id}", status_code=200)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to delete an appointment.
    """
    try:
        # Fetch the appointment from the database
        appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found.",
            )

        # Delete the appointment from the database
        db.delete(appointment)
        db.commit()

        return {
            "success": True,
            "status": 200,
            "message": "Appointment deleted successfully.",
            "data": None,
        }

    except Exception as e:
        logging.error(f"An error occurred during appointment deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )


@router.put("/update/{appointment_id}", status_code=200)
def update_appointment(
    request: Request,
    appointment_id: int, 
    update_data: schema.UpdateAppointmentSchema, 
    db: Session = Depends(get_db)
):
    """
    Endpoint to update an appointment (only admins can update status).
    """
    try:
        # Fetch the appointment from the database
        appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found.",
            )

        # Get the email from the token
        token = request.headers.get("Authorization")
        token = token.split(" ")[1]  # Assuming token is passed as "Bearer <token>"
        email = get_email_from_token(token)

        # Fetch the user associated with the email
        user = db.query(User).filter(User.email == email).first()
        logging.info(f"User: {user.role}")
        # If user is an admin, they can update the status
        if user and user.role == "admin":
            if update_data.status:
                appointment.status = update_data.status

        # Otherwise, non-admin users can update the medical_issue and message only
        if update_data.medical_issue:
            appointment.medical_issue = update_data.medical_issue

        if update_data.message:
            appointment.message = update_data.message

        # Commit the changes to the database
        db.commit()
        db.refresh(appointment)

        return {
            "success": True,
            "status": 200,
            "message": "Appointment updated successfully.",
            "data": {
                "id": appointment.id,
                "name": appointment.name,
                "email": appointment.email,
                "mobile_number": appointment.mobile_number,
                "status": appointment.status,
                "medical_issue": appointment.medical_issue,
                "message": appointment.message,
            },
        }

    except Exception as e:
        logging.error(f"An error occurred during appointment update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )
