"""
Database interface for message storage (PostgreSQL-only, user-scoped).

Phase 1: messages belong to a single owner (owner_user_id).
"""
from abc import ABC, abstractmethod
from typing import List
import traceback

from config import Config
from models import Message


class DatabaseInterface(ABC):
    """Abstract base class for database implementations."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the database (migrations, indexes)."""
        pass

    @abstractmethod
    def get_messages_for_user(self, user_id: int) -> List[Message]:
        """Retrieve all non-expired messages for a user."""
        pass

    @abstractmethod
    def add_message_for_user(self, message: Message, owner_user_id: int) -> None:
        """Add a new message for a specific user."""
        pass

    @abstractmethod
    def delete_message_for_user(self, message_id: str, owner_user_id: int) -> bool:
        """Delete a message by ID only if it belongs to the user."""
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
        """Create/alter tables and run migrations (owner_user_id)."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Create table if it doesn't exist
                    cur.execute(f'''
                        CREATE TABLE IF NOT EXISTS {Config.TABLE_NAME} (
                            {Config.COLUMN_ID} VARCHAR(50) PRIMARY KEY,
                            {Config.COLUMN_TEXT} TEXT NOT NULL,
                            {Config.COLUMN_TIMESTAMP} TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            {Config.COLUMN_EXPIRY_TIME} TIMESTAMP WITH TIME ZONE,
                            owner_user_id INTEGER
                        )
                    ''')

                    # Migration: Add expiry_time column if it doesn't exist (idempotent)
                    cur.execute(f'''
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = '{Config.TABLE_NAME}'
                                AND column_name = '{Config.COLUMN_EXPIRY_TIME}'
                            ) THEN
                                ALTER TABLE {Config.TABLE_NAME}
                                ADD COLUMN {Config.COLUMN_EXPIRY_TIME} TIMESTAMP WITH TIME ZONE;
                            END IF;
                        END $$;
                    ''')

                    # Migration: Add owner_user_id column if not exists
                    cur.execute(f'''
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = '{Config.TABLE_NAME}'
                                  AND column_name = 'owner_user_id'
                            ) THEN
                                ALTER TABLE {Config.TABLE_NAME}
                                ADD COLUMN owner_user_id INTEGER;
                            END IF;
                        END $$;
                    ''')

                    # Index for owner_user_id
                    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{Config.TABLE_NAME}_owner ON {Config.TABLE_NAME}(owner_user_id)")

                    # FK to auth.users (if not exists)
                    cur.execute(f'''
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_constraint
                                WHERE conname = 'fk_{Config.TABLE_NAME}_owner_user_id_users'
                            ) THEN
                                ALTER TABLE {Config.TABLE_NAME}
                                ADD CONSTRAINT fk_{Config.TABLE_NAME}_owner_user_id_users
                                FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE;
                            END IF;
                        END $$;
                    ''')

                    conn.commit()
            print("✅ PostgreSQL database initialized")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            traceback.print_exc()

    def get_messages_for_user(self, user_id: int) -> List[Message]:
        """Retrieve all non-expired messages for a specific user."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f'''SELECT {Config.COLUMN_ID}, {Config.COLUMN_TEXT}, {Config.COLUMN_TIMESTAMP}, {Config.COLUMN_EXPIRY_TIME}
                            FROM {Config.TABLE_NAME}
                           WHERE owner_user_id = %s
                             AND ({Config.COLUMN_EXPIRY_TIME} IS NULL OR {Config.COLUMN_EXPIRY_TIME} > NOW())
                        ORDER BY {Config.COLUMN_TIMESTAMP} DESC''',
                        (user_id,)
                    )
                    rows = cur.fetchall()
                    return [
                        Message(
                            id=row[Config.COLUMN_ID],
                            text=row[Config.COLUMN_TEXT],
                            timestamp=row[Config.COLUMN_TIMESTAMP].isoformat().replace('+00:00', 'Z'),
                            expiry_time=row[Config.COLUMN_EXPIRY_TIME].isoformat().replace('+00:00', 'Z') if row[Config.COLUMN_EXPIRY_TIME] else None
                        )
                        for row in rows
                    ]
        except Exception as e:
            print(f"Error loading messages: {e}")
            return []

    def add_message_for_user(self, message: Message, owner_user_id: int) -> None:
        """Insert a new message into the database for a user."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f'INSERT INTO {Config.TABLE_NAME} ({Config.COLUMN_ID}, {Config.COLUMN_TEXT}, {Config.COLUMN_TIMESTAMP}, {Config.COLUMN_EXPIRY_TIME}, owner_user_id) '
                        f'VALUES (%s, %s, %s, %s, %s)',
                        (message.id, message.text, message.timestamp, message.expiry_time, owner_user_id)
                    )
                    conn.commit()
        except Exception as e:
            print(f"Error saving message: {e}")
            raise

    def delete_message_for_user(self, message_id: str, owner_user_id: int) -> bool:
        """Delete a message by ID if owned by the user."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f'DELETE FROM {Config.TABLE_NAME} WHERE {Config.COLUMN_ID} = %s AND owner_user_id = %s',
                        (message_id, owner_user_id)
                    )
                    deleted = cur.rowcount
                    conn.commit()
                    return deleted > 0
        except Exception as e:
            print(f"Error deleting message: {e}")
            raise


def get_database() -> DatabaseInterface:
    """Return the Postgres database implementation (requires DATABASE_URL)."""
    if not Config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Messages DB requires PostgreSQL.")
    db = PostgresDatabase()
    db.initialize()
    return db
