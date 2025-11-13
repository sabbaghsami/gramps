"""
Email service for sending verification and password reset emails.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os

from config import Config


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.sender_email = Config.SENDER_EMAIL
        # Point to templates/email at project root
        project_root = os.path.dirname(os.path.dirname(__file__))
        self.templates_dir = os.path.join(project_root, 'templates', 'email')

    def _load_template(self, template_name: str) -> str:
        """Load a template file from the templates directory."""
        template_path = os.path.join(self.templates_dir, template_name)
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _render_email(self, content: str, **variables) -> str:
        """Render an email by combining base template, CSS, and content with variables."""
        # Load base template and CSS
        base_template = self._load_template('base_email.html')
        styles = self._load_template('email_styles.css')

        # Replace variables in content
        for key, value in variables.items():
            content = content.replace(f'{{{{ {key} }}}}', str(value))

        # Combine everything
        html = base_template.replace('{{ styles }}', styles)
        html = html.replace('{{ content }}', content)

        return html

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

    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification email."""
        verification_url = f"{Config.BASE_URL}/auth/verify/{verification_token}"

        subject = "Verify Your Email - Grandad Reminders"
        content = self._load_template('verification_email.html')
        html_body = self._render_email(
            content,
            verification_url=verification_url
        )

        return self.send_email(to_email, subject, html_body)

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email."""
        reset_url = f"{Config.BASE_URL}/auth/reset-password/{reset_token}"

        subject = "Reset Your Password - Grandad Reminders"
        content = self._load_template('password_reset_email.html')
        html_body = self._render_email(
            content,
            reset_url=reset_url
        )

        return self.send_email(to_email, subject, html_body)

    def send_workspace_invite_email(self, to_email: str, inviter_name: str, workspace_name: str, join_url: str) -> bool:
        """Send a workspace invite email with a join link."""
        subject = f"You're invited to a shared board: {workspace_name}"
        content = self._load_template('workspace_invite_email.html')
        html_body = self._render_email(
            content,
            inviter_name=inviter_name,
            workspace_name=workspace_name,
            join_url=join_url
        )
        return self.send_email(to_email, subject, html_body)
