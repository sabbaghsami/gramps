from flask import Flask, jsonify, request, send_from_directory
import os
from datetime import datetime, timezone
import random
import string
import traceback

app = Flask(__name__, static_folder='.')

# Database setup - use PostgreSQL if DATABASE_URL exists, otherwise use JSON file
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # PostgreSQL mode
    import psycopg
    from psycopg.rows import dict_row

    def get_db_connection():
        """Get PostgreSQL database connection"""
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    def init_db():
        """Initialize database schema"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS messages (
                            id VARCHAR(50) PRIMARY KEY,
                            text TEXT NOT NULL,
                            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        )
                    ''')
                    conn.commit()
            print("✅ PostgreSQL database initialized")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            traceback.print_exc()

    def load_messages():
        """Load messages from PostgreSQL"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT id, text, timestamp FROM messages ORDER BY timestamp DESC')
                    rows = cur.fetchall()
                    # Convert timestamp to ISO format string
                    return [{
                        'id': row['id'],
                        'text': row['text'],
                        'timestamp': row['timestamp'].isoformat().replace('+00:00', 'Z')
                    } for row in rows]
        except Exception as e:
            print(f"Error loading messages: {e}")
            return []

    def save_message(message):
        """Save a single message to PostgreSQL"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO messages (id, text, timestamp) VALUES (%s, %s, %s)',
                        (message['id'], message['text'], message['timestamp'])
                    )
                    conn.commit()
        except Exception as e:
            print(f"Error saving message: {e}")
            raise

    def delete_message_from_db(message_id):
        """Delete a message from PostgreSQL"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM messages WHERE id = %s', (message_id,))
                    deleted = cur.rowcount
                    conn.commit()
                    return deleted > 0
        except Exception as e:
            print(f"Error deleting message: {e}")
            raise

    # Initialize database on startup
    init_db()

else:
    # JSON file mode (for local development)
    import json
    DATA_FILE = 'messages.json'

    def load_messages():
        """Load messages from JSON file"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading messages: {e}")
            return []

    def save_message(message):
        """Save a single message to JSON file"""
        try:
            messages = load_messages()
            messages.insert(0, message)
            with open(DATA_FILE, 'w') as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            print(f"Error saving message: {e}")
            raise

    def delete_message_from_db(message_id):
        """Delete a message from JSON file"""
        try:
            messages = load_messages()
            filtered_messages = [msg for msg in messages if msg['id'] != message_id]

            if len(filtered_messages) == len(messages):
                return False

            with open(DATA_FILE, 'w') as f:
                json.dump(filtered_messages, f, indent=2)
            return True
        except Exception as e:
            print(f"Error deleting message: {e}")
            raise

    print("📝 Using JSON file storage (local mode)")

def generate_id():
    """Generate unique ID"""
    timestamp = int(datetime.now().timestamp() * 1000)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{timestamp:x}{random_str}"

# Routes
@app.route('/')
def index():
    """Serve display page"""
    return send_from_directory('.', 'display.html')

@app.route('/admin')
def admin():
    """Serve admin page"""
    return send_from_directory('.', 'admin.html')

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get all messages"""
    try:
        messages = load_messages()
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({'error': 'Failed to load messages'}), 500

@app.route('/api/messages', methods=['POST'])
def add_message():
    """Add a new message"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'error': 'Message text is required'}), 400

        new_message = {
            'id': generate_id(),
            'text': text,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        save_message(new_message)
        return jsonify(new_message), 201
    except Exception as e:
        print(f"ERROR in add_message: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to save message: {str(e)}'}), 500

@app.route('/api/messages/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message by ID"""
    try:
        deleted = delete_message_from_db(message_id)

        if not deleted:
            return jsonify({'error': 'Message not found'}), 404

        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to delete message'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    db_mode = "PostgreSQL" if DATABASE_URL else "JSON file"
    print(f"🚀 Server running at http://localhost:{port}")
    print(f"📱 Display page: http://localhost:{port}/")
    print(f"⚙️  Admin page: http://localhost:{port}/admin")
    print(f"💾 Database mode: {db_mode}")
    app.run(host='0.0.0.0', port=port, debug=True)