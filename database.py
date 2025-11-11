"""
Database interface for message storage.
Supports both PostgreSQL and JSON file storage.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import json
import os
import traceback

from config import Config
from models import Message


class DatabaseInterface(ABC):
    """Abstract base class for database implementations."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the database/storage."""
        pass

    @abstractmethod
    def get_all_messages(self) -> List[Message]:
        """Retrieve all messages."""
        pass

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Add a new message."""
        pass

    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message by ID.

        Returns:
            True if message was deleted, False if not found
        """
        pass


class PostgresDatabase(DatabaseInterface):
    """PostgreSQL database implementation."""

    def __init__(self):
        import psycopg
        from psycopg.rows import dict_row

        self.psycopg = psycopg
        self.dict_row = dict_row

    def _get_connection(self):
        """Get a database connection."""
        return self.psycopg.connect(Config.DATABASE_URL, row_factory=self.dict_row)

    def initialize(self) -> None:
        """Create the messages table if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f'''
                        CREATE TABLE IF NOT EXISTS {Config.TABLE_NAME} (
                            {Config.COLUMN_ID} VARCHAR(50) PRIMARY KEY,
                            {Config.COLUMN_TEXT} TEXT NOT NULL,
                            {Config.COLUMN_TIMESTAMP} TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        )
                    ''')
                    conn.commit()
            print("✅ PostgreSQL database initialized")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            traceback.print_exc()

    def get_all_messages(self) -> List[Message]:
        """Retrieve all messages ordered by timestamp descending."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f'SELECT {Config.COLUMN_ID}, {Config.COLUMN_TEXT}, {Config.COLUMN_TIMESTAMP} '
                        f'FROM {Config.TABLE_NAME} ORDER BY {Config.COLUMN_TIMESTAMP} DESC'
                    )
                    rows = cur.fetchall()
                    return [
                        Message(
                            id=row[Config.COLUMN_ID],
                            text=row[Config.COLUMN_TEXT],
                            timestamp=row[Config.COLUMN_TIMESTAMP].isoformat().replace('+00:00', 'Z')
                        )
                        for row in rows
                    ]
        except Exception as e:
            print(f"Error loading messages: {e}")
            return []

    def add_message(self, message: Message) -> None:
        """Insert a new message into the database."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f'INSERT INTO {Config.TABLE_NAME} ({Config.COLUMN_ID}, {Config.COLUMN_TEXT}, {Config.COLUMN_TIMESTAMP}) '
                        f'VALUES (%s, %s, %s)',
                        (message.id, message.text, message.timestamp)
                    )
                    conn.commit()
        except Exception as e:
            print(f"Error saving message: {e}")
            raise

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f'DELETE FROM {Config.TABLE_NAME} WHERE {Config.COLUMN_ID} = %s',
                        (message_id,)
                    )
                    deleted = cur.rowcount
                    conn.commit()
                    return deleted > 0
        except Exception as e:
            print(f"Error deleting message: {e}")
            raise


class JSONDatabase(DatabaseInterface):
    """JSON file-based database implementation for local development."""

    def __init__(self):
        self.file_path = Config.JSON_DATA_FILE

    def initialize(self) -> None:
        """Ensure the JSON file exists."""
        if not os.path.exists(self.file_path):
            self._save_messages([])
        print("📝 Using JSON file storage (local mode)")

    def _load_messages(self) -> List[dict]:
        """Load raw message data from JSON file."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading messages: {e}")
            return []

    def _save_messages(self, messages: List[dict]) -> None:
        """Save raw message data to JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            print(f"Error saving messages: {e}")
            raise

    def get_all_messages(self) -> List[Message]:
        """Retrieve all messages from JSON file."""
        data = self._load_messages()
        return [Message.from_dict(msg) for msg in data]

    def add_message(self, message: Message) -> None:
        """Add a message to the JSON file."""
        messages = self._load_messages()
        messages.insert(0, message.to_dict())
        self._save_messages(messages)

    def delete_message(self, message_id: str) -> bool:
        """Delete a message from the JSON file."""
        messages = self._load_messages()
        filtered = [msg for msg in messages if msg['id'] != message_id]

        if len(filtered) == len(messages):
            return False

        self._save_messages(filtered)
        return True


def get_database() -> DatabaseInterface:
    """
    Factory function to get the appropriate database implementation.

    Returns:
        PostgresDatabase if DATABASE_URL is set, otherwise JSONDatabase
    """
    if Config.use_postgres():
        db = PostgresDatabase()
    else:
        db = JSONDatabase()

    db.initialize()
    return db
