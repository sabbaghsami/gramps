"""
Email service for sending verification and password reset emails.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from config import Config


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.sender_email = Config.SENDER_EMAIL

    def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send an email via SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email

            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_verification_email(self, to_email: str, username: str, verification_token: str) -> bool:
        """Send email verification email."""
        verification_url = f"{Config.BASE_URL}/auth/verify/{verification_token}"

        subject = "Verify Your Email - Grandad Reminders"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #667eea;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">Welcome to Grandad Reminders!</h1>
                <p>Hi {username},</p>
                <p>Thank you for signing up! Please verify your email address to activate your account.</p>
                <p style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
                <div class="footer">
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                    <p>&copy; 2025 Grandad Reminders</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_body)

    def send_password_reset_email(self, to_email: str, username: str, reset_token: str) -> bool:
        """Send password reset email."""
        reset_url = f"{Config.BASE_URL}/auth/reset-password/{reset_token}"

        subject = "Reset Your Password - Grandad Reminders"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #667eea;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">Password Reset Request</h1>
                <p>Hi {username},</p>
                <p>We received a request to reset your password for your Grandad Reminders account.</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong> This link will expire in 1 hour for your security.
                </div>
                <div class="footer">
                    <p>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
                    <p>&copy; 2025 Grandad Reminders</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_body)
