"""
Initialize the authentication database.
Creates SQLite database with users and sessions tables.
"""
from auth.database import AuthDatabase


def main():
    """Initialize the authentication database."""
    print("Initializing authentication database...")

    db = AuthDatabase()
    print("✅ Authentication database initialized successfully!")
    print(f"📁 Database location: {db.db_path}")
    print("\nTables created:")
    print("  - users (id, username, email, password_hash, email_verified, etc.)")
    print("  - sessions (id, user_id, session_token, expires_at, remember_me)")
    print("\n✨ You can now start the application and create user accounts!")


if __name__ == '__main__':
    main()
