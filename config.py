"""
Configuration settings and constants for the application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # Server settings
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 3000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    JSON_DATA_FILE = 'messages.json'

    # OpenAI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

    # Database table and column names
    TABLE_NAME = 'messages'
    COLUMN_ID = 'id'
    COLUMN_TEXT = 'text'
    COLUMN_TIMESTAMP = 'timestamp'

    @classmethod
    def use_postgres(cls) -> bool:
        """Check if PostgreSQL should be used."""
        return cls.DATABASE_URL is not None

    @classmethod
    def get_db_mode(cls) -> str:
        """Get the current database mode as a string."""
        return "PostgreSQL" if cls.use_postgres() else "JSON file"
