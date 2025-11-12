"""
Authentication routes for signup, login, verification, and password reset.
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, render_template, redirect, url_for, flash, make_response, session

from auth.database import get_auth_database
from auth.models import User
from auth.email_service import EmailService
from auth.middleware import logout_user, get_current_user

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize services
auth_db = get_auth_database()
email_service = EmailService()


@auth_bp.route('/signup', methods=['GET'])
def signup_page():
    """Render signup page."""
    # Redirect if already logged in
    if get_current_user():
        return redirect(url_for('admin'))

    return render_template('auth/signup.html')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Handle user signup."""
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('auth.signup_page'))

        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return redirect(url_for('auth.signup_page'))

        if not User.validate_email(email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('auth.signup_page'))

        is_valid, error_msg = User.validate_password(password)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('auth.signup_page'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.signup_page'))

        # Check if user already exists
        if auth_db.get_user_by_email(email):
            flash('Email already registered', 'error')
            return redirect(url_for('auth.signup_page'))

        if auth_db.get_user_by_username(username):
            flash('Username already taken', 'error')
            return redirect(url_for('auth.signup_page'))

        # Create user
        password_hash = User.hash_password(password)
        verification_token = User.generate_token()

        user = auth_db.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            verification_token=verification_token
        )

        # Send verification email
        email_sent = email_service.send_verification_email(email, username, verification_token)

        if email_sent:
            flash('Account created! Please check your email to verify your account.', 'success')
        else:
            flash('Account created but verification email could not be sent. Please contact support.', 'warning')

        return redirect(url_for('auth.login_page'))

    except Exception as e:
        print(f"Signup error: {e}")
        flash('An error occurred during signup. Please try again.', 'error')
        return redirect(url_for('auth.signup_page'))


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify user's email address."""
    user = auth_db.get_user_by_verification_token(token)

    if not user:
        flash('Invalid or expired verification link', 'error')
        return redirect(url_for('auth.login_page'))

    if user.email_verified:
        flash('Email already verified. You can log in.', 'info')
        return redirect(url_for('auth.login_page'))

    # Verify email
    auth_db.verify_email(user.id)
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Render login page."""
    # Redirect if already logged in
    if get_current_user():
        return redirect(url_for('admin'))

    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    try:
        email_or_username = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'

        if not email_or_username or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('auth.login_page'))

        # Try to find user by email or username
        user = auth_db.get_user_by_email(email_or_username)
        if not user:
            user = auth_db.get_user_by_username(email_or_username)

        if not user or not User.verify_password(password, user.password_hash):
            flash('Invalid email/username or password', 'error')
            return redirect(url_for('auth.login_page'))

        if not user.email_verified:
            flash('Please verify your email before logging in', 'error')
            return redirect(url_for('auth.login_page'))

        # Create session
        session_token = User.generate_token()
        expires_in_days = 30 if remember_me else 1
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        auth_db.create_session(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at,
            remember_me=remember_me
        )

        # Set cookie
        response = make_response(redirect(url_for('admin')))
        response.set_cookie(
            'session_token',
            session_token,
            expires=expires_at,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax'
        )

        flash(f'Welcome back, {user.username}!', 'success')
        return response

    except Exception as e:
        print(f"Login error: {e}")
        flash('An error occurred during login. Please try again.', 'error')
        return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Handle user logout."""
    logout_user()

    response = make_response(redirect(url_for('auth.login_page')))
    response.set_cookie('session_token', '', expires=0)

    flash('You have been logged out', 'info')
    return response


@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    """Render forgot password page."""
    return render_template('auth/forgot_password.html')


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Handle forgot password request."""
    try:
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Email is required', 'error')
            return redirect(url_for('auth.forgot_password_page'))

        user = auth_db.get_user_by_email(email)

        # Always show success message (don't reveal if email exists)
        if user:
            reset_token = User.generate_token()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            auth_db.set_reset_token(user.id, reset_token, expires_at)
            email_service.send_password_reset_email(email, user.username, reset_token)

        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login_page'))

    except Exception as e:
        print(f"Forgot password error: {e}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password_page'))


@auth_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    """Render reset password page."""
    user = auth_db.get_user_by_reset_token(token)

    if not user or not user.is_reset_token_valid():
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('auth.login_page'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Handle password reset."""
    try:
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        user = auth_db.get_user_by_reset_token(token)

        if not user or not user.is_reset_token_valid():
            flash('Invalid or expired reset link', 'error')
            return redirect(url_for('auth.login_page'))

        is_valid, error_msg = User.validate_password(password)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('auth.reset_password_page', token=token))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.reset_password_page', token=token))

        # Update password
        new_password_hash = User.hash_password(password)
        auth_db.update_password(user.id, new_password_hash)

        # Delete all user sessions for security
        auth_db.delete_user_sessions(user.id)

        flash('Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login_page'))

    except Exception as e:
        print(f"Reset password error: {e}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.reset_password_page', token=token))


@auth_bp.route('/verification-required')
def verification_required():
    """Page shown when email verification is required."""
    return render_template('auth/email_verification_sent.html')
