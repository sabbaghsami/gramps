"""
Authentication middleware for protecting routes.
"""
from functools import wraps
from flask import request, redirect, url_for, g, abort
from typing import Optional

from auth.database import get_auth_database, AuthDatabaseInterface
from auth.models import User


def get_auth_db() -> AuthDatabaseInterface:
    """Get or create auth database instance."""
    if not hasattr(g, 'auth_db'):
        g.auth_db = get_auth_database()
    return g.auth_db


def get_current_user() -> Optional[User]:
    """Get the currently logged-in user from session."""
    if hasattr(g, 'current_user'):
        return g.current_user

    session_token = request.cookies.get('session_token')
    if not session_token:
        g.current_user = None
        return None

    auth_db = get_auth_db()
    session = auth_db.get_session(session_token)

    if not session:
        g.current_user = None
        return None

    user = session['user']
    g.current_user = user
    return user


def login_required(f):
    """
    Decorator to protect routes that require authentication.

    Usage:
        @app.route('/admin')
        @login_required
        def admin():
            return 'Admin page'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        if user is None:
            # Check if it's an API request or HTML request
            if request.path.startswith('/api/'):
                # For API requests, return 403 Forbidden
                abort(403)
            else:
                # For HTML pages, redirect to login
                return redirect(url_for('auth.login_page', next=request.url))

        if not user.email_verified:
            # Redirect to verification page if email not verified
            return redirect(url_for('auth.verification_required'))

        return f(*args, **kwargs)

    return decorated_function


def logout_user():
    """Log out the current user by clearing their session."""
    session_token = request.cookies.get('session_token')
    if session_token:
        auth_db = get_auth_db()
        auth_db.delete_session(session_token)

    # Clear from g object
    if hasattr(g, 'current_user'):
        g.current_user = None
