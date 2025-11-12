"""
Error handlers for HTTP errors (404, 403, etc.)
"""
from flask import render_template


def register_error_handlers(app):
    """Register custom error handlers with the Flask app."""

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 - Page Not Found errors."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 - Forbidden errors."""
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 - Internal Server errors."""
        return render_template('errors/500.html'), 500
