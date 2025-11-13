"""
Authentication module for Grandad Reminders.
Handles user signup, login, email verification, and password reset.
"""

from auth.models import User
from auth.database import get_auth_database
from auth.middleware import login_required, get_current_user

__all__ = ['User', 'get_auth_database', 'login_required', 'get_current_user']
