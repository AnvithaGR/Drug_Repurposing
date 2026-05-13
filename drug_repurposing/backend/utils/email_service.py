import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from jose import jwt

# Email configuration - update these with your SMTP settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your-email@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your-app-password")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

# For development, we'll mock emails if credentials are not set
ENABLE_EMAIL = SENDER_EMAIL != "your-email@gmail.com"


def generate_verification_token(email: str, expires_delta: int = 24) -> str:
    """Generate a JWT token for email verification (expires in hours)."""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=expires_delta),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token: str) -> str | None:
    """Verify a token and return the email if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        return email
    except:
        return None


def send_verification_email(recipient_email: str, username: str, verification_token: str) -> bool:
    """Send email verification link."""
    if not ENABLE_EMAIL:
        # In development mode without real email config
        print(f"\n[DEV MODE] Email verification token for {username} ({recipient_email}):")
        print(f"Token: {verification_token}")
        print(f"Verification link: http://127.0.0.1:8000/api/verify-email?token={verification_token}\n")
        return True
    
    try:
        verification_link = f"http://127.0.0.1:8000/api/verify-email?token={verification_token}"
        
        subject = "Verify your email for Drug Repurposing System"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Welcome to Drug Repurposing System!</h2>
                <p>Hi {username},</p>
                <p>Thank you for registering! Please verify your email address by clicking the link below:</p>
                <p>
                    <a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </p>
                <p>Or copy this link: {verification_link}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create this account, please ignore this email.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">Drug Repurposing System</p>
            </body>
        </html>
        """
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = recipient_email
        
        part = MIMEText(body, "html")
        message.attach(part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_password_reset_email(recipient_email: str, reset_token: str) -> bool:
    """Send password reset email."""
    if not ENABLE_EMAIL:
        print(f"\n[DEV MODE] Password reset token for {recipient_email}:")
        print(f"Token: {reset_token}")
        print(f"Reset link: http://127.0.0.1:8000/api/reset-password?token={reset_token}\n")
        return True
    
    try:
        reset_link = f"http://127.0.0.1:8000/api/reset-password?token={reset_token}"
        
        subject = "Reset your password - Drug Repurposing System"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password. Click the link below:</p>
                <p>
                    <a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = recipient_email
        
        part = MIMEText(body, "html")
        message.attach(part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
