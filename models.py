"""
Data models for the application.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass
class Message:
    """Represents a reminder message."""

    id: str
    text: str
    timestamp: str

    @classmethod
    def create(cls, message_id: str, text: str, timestamp: str = None) -> 'Message':
        """
        Create a new Message instance.

        Args:
            message_id: Unique identifier for the message
            text: The message content
            timestamp: ISO format timestamp (defaults to current UTC time)

        Returns:
            Message instance
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        return cls(id=message_id, text=text, timestamp=timestamp)

    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary format."""
        return {
            'id': self.id,
            'text': self.text,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Message':
        """Create a Message from a dictionary."""
        return cls(
            id=data['id'],
            text=data['text'],
            timestamp=data['timestamp']
        )
