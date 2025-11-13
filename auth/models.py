"""
User model and authentication utilities.
"""
import re
import secrets
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional
import bcrypt


@dataclass
class User:
    """User model for authentication."""

    id: Optional[int]
    email: str
    password_hash: str
    email_verified: bool = False
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    created_at: Optional[datetime] = None
    remember_token: Optional[str] = None

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Returns: (is_valid, error_message)
        """
        if len(password) < 10:
            return False, "Password must be at least 10 characters long"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

        return True, ""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    def is_reset_token_valid(self) -> bool:
        """Check if reset token is still valid."""
        if not self.reset_token or not self.reset_token_expires:
            return False
        return datetime.now(timezone.utc) < self.reset_token_expires

    def to_dict(self) -> dict:
        """Convert user to dictionary (without sensitive data)."""
        return {
            'id': self.id,
            'email': self.email,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
