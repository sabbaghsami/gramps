"""
Data models for the application.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class Message:
    """Represents a reminder message."""

    id: str
    text: str
    timestamp: str
    expiry_time: Optional[str] = None

    @classmethod
    def create(cls, message_id: str, text: str, timestamp: str = None, expiry_time: str = None) -> 'Message':
        """
        Create a new Message instance.

        Args:
            message_id: Unique identifier for the message
            text: The message content
            timestamp: ISO format timestamp (defaults to current UTC time)
            expiry_time: Optional ISO format timestamp for when message expires

        Returns:
            Message instance
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        return cls(id=message_id, text=text, timestamp=timestamp, expiry_time=expiry_time)

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert message to dictionary format."""
        return {
            'id': self.id,
            'text': self.text,
            'timestamp': self.timestamp,
            'expiry_time': self.expiry_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Message':
        """Create a Message from a dictionary."""
        return cls(
            id=data['id'],
            text=data['text'],
            timestamp=data['timestamp'],
            expiry_time=data.get('expiry_time')
        )

    def is_expired(self) -> bool:
        """Check if the message has expired."""
        if self.expiry_time is None:
            return False

        try:
            expiry_dt = datetime.fromisoformat(self.expiry_time.replace('Z', '+00:00'))
            now_dt = datetime.now(timezone.utc)
            return now_dt > expiry_dt
        except (ValueError, AttributeError):
            return False
