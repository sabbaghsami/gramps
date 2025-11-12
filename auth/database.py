"""
Database layer for authentication.
Supports both SQLite (local) and PostgreSQL (production).
"""
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import contextmanager
import traceback

from auth.models import User
from config import Config


class AuthDatabaseInterface(ABC):
    """Abstract base class for authentication database implementations."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the database."""
        pass

    @abstractmethod
    def create_user(self, username: str, email: str, password_hash: str,
                   verification_token: Optional[str] = None) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_user_by_verification_token(self, token: str) -> Optional[User]:
        """Get user by verification token."""
        pass

    @abstractmethod
    def get_user_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by password reset token."""
        pass

    @abstractmethod
    def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified."""
        pass

    @abstractmethod
    def set_reset_token(self, user_id: int, reset_token: str, expires_at: datetime) -> bool:
        """Set password reset token for user."""
        pass

    @abstractmethod
    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Update user's password and clear reset token."""
        pass

    @abstractmethod
    def create_session(self, user_id: int, session_token: str,
                      expires_at: datetime, remember_me: bool = False) -> int:
        """Create a new session."""
        pass

    @abstractmethod
    def get_session(self, session_token: str) -> Optional[dict]:
        """Get session by token."""
        pass

    @abstractmethod
    def delete_session(self, session_token: str) -> bool:
        """Delete a session."""
        pass

    @abstractmethod
    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        pass


class SQLiteAuthDatabase(AuthDatabaseInterface):
    """SQLite database for user authentication (local development)."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.AUTH_DB_PATH
        self.initialize()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Users table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email_verified INTEGER DEFAULT 0,
                    verification_token TEXT,
                    reset_token TEXT,
                    reset_token_expires TEXT,
                    created_at TEXT NOT NULL,
                    remember_token TEXT
                )
            ''')

            # Sessions table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TEXT NOT NULL,
                    remember_me INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')

            # Create indexes for better performance
            cur.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')

            conn.commit()
        print("📝 Using SQLite for authentication (local mode)")

    def create_user(self, username: str, email: str, password_hash: str,
                   verification_token: Optional[str] = None) -> User:
        """Create a new user."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()

            cur.execute('''
                INSERT INTO users (username, email, password_hash, verification_token, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, verification_token, now))

            user_id = cur.lastrowid

            return User(
                id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                verification_token=verification_token,
                created_at=datetime.fromisoformat(now)
            )

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cur.fetchone()

            if not row:
                return None

            return self._row_to_user(row)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cur.fetchone()

            if not row:
                return None

            return self._row_to_user(row)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cur.fetchone()

            if not row:
                return None

            return self._row_to_user(row)

    def get_user_by_verification_token(self, token: str) -> Optional[User]:
        """Get user by verification token."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE verification_token = ?', (token,))
            row = cur.fetchone()

            if not row:
                return None

            return self._row_to_user(row)

    def get_user_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by password reset token."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE reset_token = ?', (token,))
            row = cur.fetchone()

            if not row:
                return None

            return self._row_to_user(row)

    def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                UPDATE users
                SET email_verified = 1, verification_token = NULL
                WHERE id = ?
            ''', (user_id,))

            return cur.rowcount > 0

    def set_reset_token(self, user_id: int, reset_token: str, expires_at: datetime) -> bool:
        """Set password reset token for user."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                UPDATE users
                SET reset_token = ?, reset_token_expires = ?
                WHERE id = ?
            ''', (reset_token, expires_at.isoformat(), user_id))

            return cur.rowcount > 0

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Update user's password and clear reset token."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                UPDATE users
                SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL
                WHERE id = ?
            ''', (new_password_hash, user_id))

            return cur.rowcount > 0

    def create_session(self, user_id: int, session_token: str,
                      expires_at: datetime, remember_me: bool = False) -> int:
        """Create a new session."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()

            cur.execute('''
                INSERT INTO sessions (user_id, session_token, expires_at, remember_me, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at.isoformat(), int(remember_me), now))

            return cur.lastrowid

    def get_session(self, session_token: str) -> Optional[dict]:
        """Get session by token."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT s.*, u.*
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            ''', (session_token,))
            row = cur.fetchone()

            if not row:
                return None

            # Check if session is expired
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.now(timezone.utc) > expires_at:
                # Delete expired session
                self.delete_session(session_token)
                return None

            return {
                'session_id': row['id'],
                'user': self._row_to_user(row),
                'expires_at': expires_at,
                'remember_me': bool(row['remember_me'])
            }

    def delete_session(self, session_token: str) -> bool:
        """Delete a session."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
            return cur.rowcount > 0

    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
            return cur.rowcount

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object."""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            email_verified=bool(row['email_verified']),
            verification_token=row['verification_token'],
            reset_token=row['reset_token'],
            reset_token_expires=datetime.fromisoformat(row['reset_token_expires']) if row['reset_token_expires'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            remember_token=row['remember_token']
        )


class PostgresAuthDatabase(AuthDatabaseInterface):
    """PostgreSQL database for user authentication (production)."""

    def __init__(self):
        import psycopg
        from psycopg.rows import dict_row

        self.psycopg = psycopg
        self.dict_row = dict_row

    def _get_connection(self):
        """Get a database connection."""
        return self.psycopg.connect(Config.DATABASE_URL, row_factory=self.dict_row)

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Users table
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            email_verified BOOLEAN DEFAULT FALSE,
                            verification_token TEXT,
                            reset_token TEXT,
                            reset_token_expires TIMESTAMP WITH TIME ZONE,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            remember_token TEXT
                        )
                    ''')

                    # Sessions table
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS sessions (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            session_token TEXT UNIQUE NOT NULL,
                            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            remember_me BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                        )
                    ''')

                    # Create indexes for better performance
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')

                    conn.commit()
            print("✅ PostgreSQL authentication database initialized")
        except Exception as e:
            print(f"❌ Error initializing auth database: {e}")
            traceback.print_exc()

    def create_user(self, username: str, email: str, password_hash: str,
                   verification_token: Optional[str] = None) -> User:
        """Create a new user."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO users (username, email, password_hash, verification_token, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id, created_at
                ''', (username, email, password_hash, verification_token))

                result = cur.fetchone()
                user_id = result['id']
                created_at = result['created_at']

                conn.commit()

                return User(
                    id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    verification_token=verification_token,
                    created_at=created_at
                )

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE email = %s', (email,))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_user(row)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE username = %s', (username,))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_user(row)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_user(row)

    def get_user_by_verification_token(self, token: str) -> Optional[User]:
        """Get user by verification token."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE verification_token = %s', (token,))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_user(row)

    def get_user_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by password reset token."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE reset_token = %s', (token,))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_user(row)

    def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE users
                    SET email_verified = TRUE, verification_token = NULL
                    WHERE id = %s
                ''', (user_id,))

                rowcount = cur.rowcount
                conn.commit()
                return rowcount > 0

    def set_reset_token(self, user_id: int, reset_token: str, expires_at: datetime) -> bool:
        """Set password reset token for user."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE users
                    SET reset_token = %s, reset_token_expires = %s
                    WHERE id = %s
                ''', (reset_token, expires_at, user_id))

                rowcount = cur.rowcount
                conn.commit()
                return rowcount > 0

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Update user's password and clear reset token."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE users
                    SET password_hash = %s, reset_token = NULL, reset_token_expires = NULL
                    WHERE id = %s
                ''', (new_password_hash, user_id))

                rowcount = cur.rowcount
                conn.commit()
                return rowcount > 0

    def create_session(self, user_id: int, session_token: str,
                      expires_at: datetime, remember_me: bool = False) -> int:
        """Create a new session."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO sessions (user_id, session_token, expires_at, remember_me, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id
                ''', (user_id, session_token, expires_at, remember_me))

                session_id = cur.fetchone()['id']
                conn.commit()
                return session_id

    def get_session(self, session_token: str) -> Optional[dict]:
        """Get session by token."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT s.id, s.user_id, s.expires_at, s.remember_me, s.created_at,
                           u.id as u_id, u.username, u.email, u.password_hash, u.email_verified,
                           u.verification_token, u.reset_token, u.reset_token_expires,
                           u.created_at as u_created_at, u.remember_token
                    FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = %s
                ''', (session_token,))
                row = cur.fetchone()

                if not row:
                    return None

                # Check if session is expired
                expires_at = row['expires_at']
                if datetime.now(timezone.utc) > expires_at:
                    # Delete expired session
                    self.delete_session(session_token)
                    return None

                # Build user object from the joined row
                user = User(
                    id=row['u_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    email_verified=row['email_verified'],
                    verification_token=row['verification_token'],
                    reset_token=row['reset_token'],
                    reset_token_expires=row['reset_token_expires'],
                    created_at=row['u_created_at'],
                    remember_token=row['remember_token']
                )

                return {
                    'session_id': row['id'],
                    'user': user,
                    'expires_at': expires_at,
                    'remember_me': row['remember_me']
                }

    def delete_session(self, session_token: str) -> bool:
        """Delete a session."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sessions WHERE session_token = %s', (session_token,))
                rowcount = cur.rowcount
                conn.commit()
                return rowcount > 0

    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sessions WHERE user_id = %s', (user_id,))
                rowcount = cur.rowcount
                conn.commit()
                return rowcount

    def _row_to_user(self, row: dict) -> User:
        """Convert database row to User object."""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            email_verified=row['email_verified'],
            verification_token=row['verification_token'],
            reset_token=row['reset_token'],
            reset_token_expires=row['reset_token_expires'],
            created_at=row['created_at'],
            remember_token=row['remember_token']
        )


def get_auth_database() -> AuthDatabaseInterface:
    """
    Factory function to get the appropriate auth database implementation.

    Returns:
        PostgresAuthDatabase if DATABASE_URL is set, otherwise SQLiteAuthDatabase
    """
    if Config.use_postgres():
        db = PostgresAuthDatabase()
    else:
        db = SQLiteAuthDatabase()

    db.initialize()
    return db


# Legacy class name for backwards compatibility
AuthDatabase = get_auth_database
