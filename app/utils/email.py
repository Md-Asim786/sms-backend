import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_reset_password_email(email_to: str, otp: str):
    if not settings.SMTP_HOST:
        print(f"DEBUG: SMTP_HOST not configured. OTP for {email_to} is {otp}")
        return False

    subject = f"{settings.SCHOOL_NAME_ABBR} - Password Reset OTP"
    
    # HTML content for the email
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; rounded: 10px;">
                <h2 style="color: #1e3a8a; text-align: center;">{settings.SCHOOL_NAME_ABBR} LMS</h2>
                <p>Hello,</p>
                <p>You have requested a password reset for your LMS account. Use the following OTP to verify your request:</p>
                <div style="background-color: #f3f4f6; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #1e3a8a; margin: 20px 0;">
                    {otp}
                </div>
                <p>This OTP is valid for 10 minutes. If you did not request this, please ignore this email.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
                <p style="font-size: 12px; color: #777; text-align: center;">
                    This is an automated message from {settings.SCHOOL_NAME_ABBR} Learning Management System.
                </p>
            </div>
        </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAILS_FROM_NAME or settings.SCHOOL_NAME_ABBR} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = email_to

    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, email_to, message.as_string())
        return True
    except Exception as e:
        print(f"ERROR: Failed to send email to {email_to}: {e}")
        return False
