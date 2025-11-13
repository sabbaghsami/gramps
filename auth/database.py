"""
Authentication database layer (PostgreSQL-only).

Simple, production-parity design: both local and deployed use DATABASE_URL.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
import logging

from auth.models import User
from config import Config

logger = logging.getLogger(__name__)


class AuthDatabaseInterface(ABC):
    """Minimal interface used by middleware and routes."""

    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def create_user(self, email: str, password_hash: str,
                    verification_token: Optional[str] = None) -> User: ...

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    def get_user_by_verification_token(self, token: str) -> Optional[User]: ...

    @abstractmethod
    def get_user_by_reset_token(self, token: str) -> Optional[User]: ...

    @abstractmethod
    def verify_email(self, user_id: int) -> bool: ...

    @abstractmethod
    def set_reset_token(self, user_id: int, reset_token: str, expires_at: datetime) -> bool: ...

    @abstractmethod
    def update_password(self, user_id: int, new_password_hash: str) -> bool: ...

    @abstractmethod
    def create_session(self, user_id: int, session_token: str, expires_at: datetime,
                       remember_me: bool = False) -> int: ...

    @abstractmethod
    def get_session(self, session_token: str) -> Optional[dict]: ...

    @abstractmethod
    def delete_session(self, session_token: str) -> bool: ...

    @abstractmethod
    def delete_user_sessions(self, user_id: int) -> int: ...


class PostgresAuthDatabase(AuthDatabaseInterface):
    """Concrete PostgreSQL implementation."""

    def __init__(self):
        import psycopg
        from psycopg.rows import dict_row

        if not Config.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set for PostgresAuthDatabase")

        self._psycopg = psycopg
        self._dict_row = dict_row

    # --- connection helpers
    def _conn(self):
        return self._psycopg.connect(Config.DATABASE_URL, row_factory=self._dict_row)

    def _execute(self, sql: str, params: tuple) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                affected = cur.rowcount
                conn.commit()
                return affected

    def _one(self, sql: str, params: tuple):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()

    # --- model helpers
    @staticmethod
    def _to_py_dt(value) -> Optional[datetime]:
        return value if value is not None else None

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            email_verified=bool(row["email_verified"]),
            verification_token=row.get("verification_token"),
            reset_token=row.get("reset_token"),
            reset_token_expires=row.get("reset_token_expires"),
            created_at=row.get("created_at"),
            remember_token=row.get("remember_token"),
        )

    # --- schema
    def initialize(self) -> None:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            email_verified BOOLEAN DEFAULT FALSE,
                            verification_token TEXT,
                            reset_token TEXT,
                            reset_token_expires TIMESTAMPTZ,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            remember_token TEXT
                        )
                        '''
                    )
                    cur.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS sessions (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            session_token TEXT UNIQUE NOT NULL,
                            expires_at TIMESTAMPTZ NOT NULL,
                            remember_me BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        '''
                    )
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')
                    # Drop legacy username index if it exists
                    try:
                        cur.execute('DROP INDEX IF EXISTS idx_users_username')
                    except Exception:
                        pass
                conn.commit()
            logger.info("PostgreSQL authentication database initialized")
        except Exception as e:
            logger.error(f"Error initializing auth database: {e}")
            logger.exception("Traceback:")

    # --- users
    def create_user(self, email: str, password_hash: str,
                    verification_token: Optional[str] = None) -> User:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO users (email, password_hash, verification_token, created_at)
                    VALUES (%s, %s, %s, NOW())
                    RETURNING id, created_at
                    ''', (email, password_hash, verification_token)
                )
                row = cur.fetchone()
                conn.commit()
                return User(
                    id=row["id"],
                    email=email,
                    password_hash=password_hash,
                    verification_token=verification_token,
                    created_at=row["created_at"],
                )

    def _get_user_by(self, col: str, val) -> Optional[User]:
        row = self._one(f"SELECT * FROM users WHERE {col} = %s", (val,))
        return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self._get_user_by("email", email)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self._get_user_by("id", user_id)

    def get_user_by_verification_token(self, token: str) -> Optional[User]:
        return self._get_user_by("verification_token", token)

    def get_user_by_reset_token(self, token: str) -> Optional[User]:
        return self._get_user_by("reset_token", token)

    def verify_email(self, user_id: int) -> bool:
        return self._execute(
            "UPDATE users SET email_verified = TRUE, verification_token = NULL WHERE id = %s",
            (user_id,),
        ) > 0

    def set_reset_token(self, user_id: int, reset_token: str, expires_at: datetime) -> bool:
        return self._execute(
            "UPDATE users SET reset_token = %s, reset_token_expires = %s WHERE id = %s",
            (reset_token, expires_at, user_id),
        ) > 0

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        return self._execute(
            "UPDATE users SET password_hash = %s, reset_token = NULL, reset_token_expires = NULL WHERE id = %s",
            (new_password_hash, user_id),
        ) > 0

    # --- sessions
    def create_session(self, user_id: int, session_token: str, expires_at: datetime,
                       remember_me: bool = False) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO sessions (user_id, session_token, expires_at, remember_me, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id
                    ''', (user_id, session_token, expires_at, remember_me)
                )
                row = cur.fetchone()
                conn.commit()
                return row["id"]

    def get_session(self, session_token: str) -> Optional[dict]:
        row = self._one(
            '''
            SELECT
              s.id AS session_id,
              s.user_id AS s_user_id,
              s.expires_at AS s_expires_at,
              s.remember_me AS s_remember_me,
              s.created_at AS s_created_at,
              u.id AS u_id, u.email, u.password_hash, u.email_verified,
              u.verification_token, u.reset_token, u.reset_token_expires,
              u.created_at AS u_created_at, u.remember_token
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = %s
            ''', (session_token,)
        )
        if not row:
            return None

        expires_at = self._to_py_dt(row["s_expires_at"])
        if expires_at and datetime.now(timezone.utc) > expires_at:
            self.delete_session(session_token)
            return None

        user = User(
            id=row["u_id"],
            email=row["email"],
            password_hash=row["password_hash"],
            email_verified=bool(row["email_verified"]),
            verification_token=row["verification_token"],
            reset_token=row["reset_token"],
            reset_token_expires=row["reset_token_expires"],
            created_at=row["u_created_at"],
            remember_token=row["remember_token"],
        )

        return {
            "session_id": row["session_id"],
            "user": user,
            "expires_at": expires_at,
            "remember_me": bool(row["s_remember_me"]),
        }

    def delete_session(self, session_token: str) -> bool:
        return self._execute("DELETE FROM sessions WHERE session_token = %s", (session_token,)) > 0

    def delete_user_sessions(self, user_id: int) -> int:
        return self._execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))


def get_auth_database() -> AuthDatabaseInterface:
    """Return the Postgres-backed auth database. Requires DATABASE_URL."""
    if not Config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. The auth module requires PostgreSQL.")
    db: AuthDatabaseInterface = PostgresAuthDatabase()
    db.initialize()
    return db
