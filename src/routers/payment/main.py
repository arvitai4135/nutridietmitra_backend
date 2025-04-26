import requests
import enum
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from loguru import logger as logging
from src.database import Database
from src.routers.payment.schemas import CreatePaymentLinkSchema, PaymentWebhookSchema
from src.routers.payment.models import Payment
from src.utils.jwt import get_email_from_token
from ..users.models import User
import requests
import random
import os
from dotenv import load_dotenv
# OAuth2 token authentication (for securing payment routes)
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Body, Depends, HTTPException, status, Request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
load_dotenv()

# X_API_VERSION = os.getenv('X_API_VERSION') 
# X_CLIENT_ID = os.getenv('X_CLIENT_ID')
# X_CLIENT_SECRET = os.getenv('X_CLIENT_SECRET')
X_API_VERSION = "2025-01-01"#os.getenv('X_API_VERSION', 'v1')  # Default version 'v1'
X_CLIENT_ID = "TEST10336412a92793060b4d3d8cd83521463301"#os.getenv('X_CLIENT_ID', 'default-client-id')
X_CLIENT_SECRET ="cfsk_ma_test_aff7e27bb247244e4bde9c8c7e77d9c7_489509d5" #os.getenv('X_CLIENT_SECRET', 'default-secret-key')


# Dependency to get database session
db_util = Database()

def get_db():
    db = db_util.get_session()
    try:
        yield db
    finally:
        db.close()

# Define router
router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
    responses={404: {"description": "Not found"}},
)

# Payment Status Enum
class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    successful = "successful"
    failed = "failed"

# from fastapi import Request  # Import Request

@router.post("/create-payment-link", response_model=dict)
def create_payment_link(
    request: Request,
    request_data: CreatePaymentLinkSchema = Body(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    API to generate a Cashfree payment link and store details in the database.
    """
    logging.debug("Create payment link function called")

    auth_header = request.headers.get("Authorization")
    if not auth_header or "Bearer " not in auth_header:
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")

    token = auth_header.split(" ")[1]
    email = get_email_from_token(token)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found, cannot create appointment",
        )

    # Plan durations in months
    plan_months = {
        "one_month": 1,
        "two_months": 2,
        "three_months": 3,
        "six_months": 6,
        "single_meal": 0,
        "weekly_meal_plan": 0,
        "monthly_meal_plan": 1,
        "custom": 0,
    }

    if request_data.plan_type not in plan_months:
        raise HTTPException(status_code=400, detail="Invalid plan_type")

    # Set subscription end only for plans with duration
    duration = plan_months[request_data.plan_type]
    subscription_end = (
        datetime.now(timezone.utc) + timedelta(days=30 * duration)
        if duration > 0 else None
    )

    expiry_time = datetime.now(timezone.utc) + timedelta(hours=24)
    formatted_expiry_time = expiry_time.isoformat(timespec="seconds")

    random_number = random.randint(100, 999)
    link_id = f"{user.id}{random_number}"

    payload = {
        "customer_details": {
            "customer_email": request_data.customer_email,
            "customer_name": request_data.customer_name,
            "customer_phone": request_data.customer_phone,
        },
        "link_amount": request_data.amount,
        "link_currency": request_data.currency,
        "link_expiry_time": formatted_expiry_time,
        "link_purpose": request_data.link_purpose,
        "link_id": link_id,
        "link_meta": {
            "notify_url": "https://ee08e626ecd88c61c85f5c69c0418cb5.m.pipedream.net",
            "return_url": "https://www.cashfree.com/devstudio/thankyou",
        },
        "link_notify": {"send_email": True},
    }

    headers = {
        "x-api-version": X_API_VERSION,
        "x-client-id": X_CLIENT_ID,
        "x-client-secret": X_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://sandbox.cashfree.com/pg/links", json=payload, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to create payment link: {e}")
        raise HTTPException(status_code=400, detail="Failed to create payment link")

    response_data = response.json()
    logging.info(f"Payment link created successfully: {response_data}")

    new_payment = Payment(
        user_id=user.id,
        cf_link_id=response_data["cf_link_id"],
        link_id=response_data["link_id"],
        link_url=response_data["link_url"],
        amount=request_data.amount,
        currency=request_data.currency,
        link_status=PaymentStatusEnum.pending,
        plan_type=request_data.plan_type,
        subscription_end=subscription_end,
    )

    db.add(new_payment)
    db.commit()

    return {
        "success": True,
        "status": 201,
        "message": "Payment link created successfully",
        "data": {"link_url": response_data["link_url"]}
    }

# ------------------- 2️⃣ Webhook - Update Payment -------------------
@router.post("/cashfree-webhook")
async def cashfree_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook API to update payment status based on Cashfree's response.
    """
    logging.debug("Webhook function called")

    try:
        data = await request.json()
        logging.info(f"Received Webhook Data: {data}")

        payment_data = data.get("data", {})
        order_data = payment_data.get("order", {})

        cf_link_id = str(payment_data.get("cf_link_id", ""))
        link_id = payment_data.get("link_id", "")
        transaction_id = str(order_data.get("transaction_id", ""))
        amount_paid = float(payment_data.get("link_amount_paid", 0))
        payment_status = order_data.get("transaction_status", "").lower()

        # Map payment status
        status_map = {"success": PaymentStatusEnum.successful, "failed": PaymentStatusEnum.failed, "pending": PaymentStatusEnum.pending}
        payment_status = status_map.get(payment_status, PaymentStatusEnum.pending)

        # Find the existing payment record
        payment = db.query(Payment).filter(Payment.cf_link_id == cf_link_id).first()
        if not payment:
            logging.warning(f"Webhook: No matching payment found for cf_link_id {cf_link_id}")
            raise HTTPException(status_code=404, detail="Payment record not found")

        # Update payment record
        payment.transaction_id = transaction_id
        payment.amount_paid = amount_paid
        payment.link_status = payment_status
        payment.updated_at = func.current_timestamp()

        db.commit()

        logging.info(f"Payment {cf_link_id} updated successfully to {payment_status}")

        return {
            "success": True,
            "status": 200,
            "message": "Payment record updated",
            "data": {"status": payment_status}
        }

    except Exception as e:
        logging.error(f"Error in webhook processing: {e}")
        return {
            "success": False,
            "status": 500,
            "message": "An unexpected error occurred",
            "data": None
        }
