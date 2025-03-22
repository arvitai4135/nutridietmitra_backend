
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger as logging
import os
from fastapi import HTTPException, status

# Constants
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token expires in 1 hour
EMAIL = os.getenv('EMAIL')
APP_PASSWORD = os.getenv('APP_PASSWORD')
S3_BUCKET_NAME = "ai-interview-bot"

def send_password_reset_email(email: str):
    """
    Send a password reset email with a reset link containing the token.
    """
    if not EMAIL or not APP_PASSWORD:
        logging.error("EMAIL or APP_PASSWORD is not set in the environment variables.")
        raise ValueError("Email credentials are missing.")

    
    subject = "Apooitment confirmed"
    body = f"your appoitment is confirmed."

    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Start TLS encryption
            server.login(EMAIL, APP_PASSWORD)
            server.sendmail(EMAIL, email, msg.as_string())
        logging.info(f"Password reset email sent successfully to {email}.")
    except Exception as e:
        logging.error(f"Failed to send password reset email to {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email. Please try again later.",
        )