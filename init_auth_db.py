"""
Initialize the authentication database (PostgreSQL-only).
"""
from auth.database import AuthDatabase
from config import Config


def main():
    """Initialize the authentication database."""
    print("Initializing authentication database...")

    db = AuthDatabase()
    print("✅ Authentication database initialized successfully!")
    if Config.DATABASE_URL:
        print(f"🔌 DATABASE_URL: {Config.DATABASE_URL}")
    else:
        print("⚠️ DATABASE_URL not set. The auth module requires PostgreSQL.")
    print("\nTables created:")
    print("  - users (id, username, email, password_hash, email_verified, etc.)")
    print("  - sessions (id, user_id, session_token, expires_at, remember_me)")
    print("\n✨ You can now start the application and create user accounts!")


if __name__ == '__main__':
    main()
