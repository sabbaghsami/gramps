"""
Grandad Reminders - A simple reminder display system.
Flask application with PostgreSQL/JSON storage support.
"""
from flask import Flask, jsonify, request, send_from_directory
import random
import string
import traceback
from datetime import datetime, timedelta, timezone
from openai import OpenAI

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
        self.app.add_url_rule('/api/translate', 'translate', self.translate, methods=['POST'])

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
            expiry_duration_minutes = data.get('expiry_duration_minutes')

            if not text:
                return jsonify({'error': 'Message text is required'}), 400

            # Calculate expiry time if duration is provided
            expiry_time = None
            if expiry_duration_minutes is not None and expiry_duration_minutes > 0:
                now = datetime.now(timezone.utc)
                expiry_dt = now + timedelta(minutes=expiry_duration_minutes)
                expiry_time = expiry_dt.isoformat().replace('+00:00', 'Z')

            message = Message.create(
                message_id=self.generate_id(),
                text=text,
                expiry_time=expiry_time
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

    def translate(self):
        """POST /api/translate - Translate text using OpenAI API."""
        try:
            data = request.get_json()
            text = data.get('text', '').strip()
            target_language = data.get('target_language', '').strip()

            if not text:
                return jsonify({'error': 'Text is required'}), 400

            if not target_language:
                return jsonify({'error': 'Target language is required'}), 400

            if not Config.OPENAI_API_KEY:
                return jsonify({'error': 'OpenAI API key not configured'}), 500

            # Initialize OpenAI client
            client = OpenAI(api_key=Config.OPENAI_API_KEY)

            # Create translation prompt
            prompt = f"Translate the following text to {target_language}. Only provide the translation, no explanations:\n\n{text}"

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional translator. Provide only the translation without any additional text or explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            translated_text = response.choices[0].message.content.strip()

            return jsonify({
                'translated_text': translated_text,
                'original_text': text,
                'target_language': target_language
            }), 200

        except Exception as e:
            print(f"Error in translate: {e}")
            traceback.print_exc()

            # Provide more specific error messages
            error_message = str(e)
            if 'APIConnectionError' in str(type(e)):
                error_message = 'Cannot connect to OpenAI API. Please check your internet connection and API key.'
            elif 'AuthenticationError' in str(type(e)):
                error_message = 'Invalid OpenAI API key. Please check your API key configuration.'
            elif 'RateLimitError' in str(type(e)):
                error_message = 'OpenAI API rate limit exceeded. Please try again later.'
            elif 'APIError' in str(type(e)):
                error_message = f'OpenAI API error: {str(e)}'
            else:
                error_message = f'Translation failed: {str(e)}'

            return jsonify({'error': error_message}), 500

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
