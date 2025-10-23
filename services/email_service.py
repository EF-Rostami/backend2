# email_service.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_APP_PASSWORD")
        self.from_name = os.getenv("SMTP_FROM_NAME", "Support")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_user)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False

    async def send_reset_password_email(self, to_email: str, reset_link: str):
        subject = "Password Reset Request"
        html_content = f"""
        <p>Hello,</p>
        <p>You requested a password reset. Click the link below to reset your password:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
        <p>If you didn't request this, ignore this email.</p>
        <p>Thanks,<br/>Support Team</p>
        """
        text_content = f"Reset your password: {reset_link}"
        return await self.send_email(to_email, subject, html_content, text_content)


# -------------------------
# Top-level wrapper functions
# -------------------------
email_service = EmailService()  # singleton instance

async def send_admission_pending_email(to_email, parent_name, child_name, admission_number):
    subject = "Admission Submitted"
    html_content = f"""
    <p>Dear {parent_name},</p>
    <p>Your child {child_name} has been successfully registered.</p>
    <p>Admission Number: {admission_number}</p>
    <p>We will notify you once approved.</p>
    """
    return await email_service.send_email(to_email, subject, html_content)

async def send_admission_approval_email(to_email, parent_name, child_name, admission_number, parent_username, parent_password, student_username, student_password, portal_url):
    subject = "Admission Approved"
    html_content = f"""
    <p>Dear {parent_name},</p>
    <p>Your child {child_name} has been approved!</p>
    <p>Admission Number: {admission_number}</p>
    <p>Login details:</p>
    <ul>
      <li>Parent: {parent_username} / {parent_password}</li>
      <li>Student: {student_username} / {student_password}</li>
    </ul>
    <p>Portal URL: <a href="{portal_url}">{portal_url}</a></p>
    """
    return await email_service.send_email(to_email, subject, html_content)

async def send_admission_rejection_email(to_email, parent_name, child_name, admission_number, reason):
    subject = "Admission Rejected"
    html_content = f"""
    <p>Dear {parent_name},</p>
    <p>We regret to inform you that your child {child_name} has not been approved.</p>
    <p>Admission Number: {admission_number}</p>
    <p>Reason: {reason}</p>
    """
    return await email_service.send_email(to_email, subject, html_content)
