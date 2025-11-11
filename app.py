"""
Grandad Reminders - A simple reminder display system.
Flask application with PostgreSQL/JSON storage support.
"""
from flask import Flask, jsonify, request, send_from_directory
import random
import string
import traceback
from datetime import datetime

from config import Config
from database import get_database
from models import Message


class ReminderApp:
    """Main application class for the reminder system."""

    def __init__(self):
        self.app = Flask(__name__, static_folder='.')
        self.db = get_database()
        self._register_routes()

    def _register_routes(self) -> None:
        """Register all Flask routes."""
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/admin', 'admin', self.admin)
        self.app.add_url_rule('/api/messages', 'get_messages', self.get_messages, methods=['GET'])
        self.app.add_url_rule('/api/messages', 'add_message', self.add_message, methods=['POST'])
        self.app.add_url_rule('/api/messages/<message_id>', 'delete_message', self.delete_message, methods=['DELETE'])

    @staticmethod
    def generate_id() -> str:
        """Generate a unique message ID."""
        timestamp = int(datetime.now().timestamp() * 1000)
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f"{timestamp:x}{random_str}"

    def index(self):
        """Serve the display page."""
        return send_from_directory('.', 'display.html')

    def admin(self):
        """Serve the admin page."""
        return send_from_directory('.', 'admin.html')

    def get_messages(self):
        """GET /api/messages - Retrieve all messages."""
        try:
            messages = self.db.get_all_messages()
            return jsonify([msg.to_dict() for msg in messages]), 200
        except Exception as e:
            print(f"Error in get_messages: {e}")
            return jsonify({'error': 'Failed to load messages'}), 500

    def add_message(self):
        """POST /api/messages - Add a new message."""
        try:
            data = request.get_json()
            text = data.get('text', '').strip()

            if not text:
                return jsonify({'error': 'Message text is required'}), 400

            message = Message.create(
                message_id=self.generate_id(),
                text=text
            )

            self.db.add_message(message)
            return jsonify(message.to_dict()), 201

        except Exception as e:
            print(f"ERROR in add_message: {e}")
            traceback.print_exc()
            return jsonify({'error': f'Failed to save message: {str(e)}'}), 500

    def delete_message(self, message_id: str):
        """DELETE /api/messages/<id> - Delete a message by ID."""
        try:
            deleted = self.db.delete_message(message_id)

            if not deleted:
                return jsonify({'error': 'Message not found'}), 404

            return jsonify({'success': True}), 200

        except Exception as e:
            print(f"Error in delete_message: {e}")
            return jsonify({'error': 'Failed to delete message'}), 500

    def run(self) -> None:
        """Start the Flask development server."""
        print(f"🚀 Server running at http://localhost:{Config.PORT}")
        print(f"📱 Display page: http://localhost:{Config.PORT}/")
        print(f"⚙️  Admin page: http://localhost:{Config.PORT}/admin")
        print(f"💾 Database mode: {Config.get_db_mode()}")

        self.app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )


def create_app() -> Flask:
    """
    Application factory for creating Flask app instance.
    Used by production WSGI servers like Gunicorn.
    """
    reminder_app = ReminderApp()
    return reminder_app.app


if __name__ == '__main__':
    app_instance = ReminderApp()
    app_instance.run()
