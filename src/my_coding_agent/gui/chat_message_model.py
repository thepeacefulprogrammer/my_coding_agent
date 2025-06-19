"""Chat message model for PyQt6 chat interface."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel


class MessageRole(Enum):
    """Enum for message roles in the chat."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

    def __str__(self) -> str:
        """Return the string representation of the role."""
        return self.value


class MessageStatus(Enum):
    """Enum for message status in the chat."""

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    ERROR = "error"
    TYPING = "typing"

    def __str__(self) -> str:
        """Return the string representation of the status."""
        return self.value


@dataclass
class ChatMessage:
    """Data class representing a chat message."""

    content: str
    role: MessageRole
    status: MessageStatus
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_user_message(
        cls, content: str, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Create a user message."""
        return cls(
            content=content,
            role=MessageRole.USER,
            status=MessageStatus.PENDING,
            metadata=metadata or {},
        )

    @classmethod
    def create_assistant_message(
        cls, content: str, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Create an assistant message."""
        return cls(
            content=content,
            role=MessageRole.ASSISTANT,
            status=MessageStatus.DELIVERED,
            metadata=metadata or {},
        )

    @classmethod
    def create_system_message(
        cls, content: str, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Create a system message."""
        return cls(
            content=content,
            role=MessageRole.SYSTEM,
            status=MessageStatus.DELIVERED,
            metadata=metadata or {},
        )

    def set_status(self, status: MessageStatus) -> None:
        """Set the message status."""
        self.status = status

    def set_error(self, error_message: str) -> None:
        """Set error status and message."""
        self.status = MessageStatus.ERROR
        self.error_message = error_message

    def clear_error(self) -> None:
        """Clear error status and message."""
        self.error_message = None
        self.status = MessageStatus.PENDING

    def is_user_message(self) -> bool:
        """Check if the message is from user."""
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """Check if the message is from assistant."""
        return self.role == MessageRole.ASSISTANT

    def is_system_message(self) -> bool:
        """Check if the message is from system."""
        return self.role == MessageRole.SYSTEM

    def has_error(self) -> bool:
        """Check if the message has an error."""
        return self.error_message is not None

    def format_timestamp(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format the timestamp as a string."""
        return self.timestamp.strftime(format_str)

    def __eq__(self, other) -> bool:
        """Check equality based on message_id."""
        if not isinstance(other, ChatMessage):
            return False
        return self.message_id == other.message_id

    def __repr__(self) -> str:
        """Return string representation of the message."""
        return f"ChatMessage(id={self.message_id[:8]}..., role={self.role.value}, content='{self.content[:50]}...')"


class ChatMessageModel(QStandardItemModel):
    """Model for managing chat messages in PyQt6."""

    # Signals
    message_added = pyqtSignal(ChatMessage)
    message_updated = pyqtSignal(ChatMessage)
    message_removed = pyqtSignal(str)  # message_id

    def __init__(self, parent: QObject | None = None):
        """Initialize the chat message model."""
        super().__init__(parent)
        self._messages: list[ChatMessage] = []

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the model."""
        self.beginInsertRows(
            self.index(-1, -1), len(self._messages), len(self._messages)
        )
        self._messages.append(message)

        # Create a QStandardItem for the message
        item = QStandardItem()
        item.setData(message, 0)
        self.appendRow(item)

        self.endInsertRows()
        self.message_added.emit(message)

    def get_message(self, index: int) -> ChatMessage | None:
        """Get a message by index."""
        if 0 <= index < len(self._messages):
            return self._messages[index]
        return None

    def get_message_by_id(self, message_id: str) -> ChatMessage | None:
        """Get a message by its ID."""
        for message in self._messages:
            if message.message_id == message_id:
                return message
        return None

    def update_message_status(self, message_id: str, status: MessageStatus) -> bool:
        """Update the status of a message."""
        message = self.get_message_by_id(message_id)
        if message:
            # Direct status assignment to ensure it works
            message.status = status

            # Emit signal with the updated message
            self.message_updated.emit(message)
            return True
        return False

    def set_message_error(self, message_id: str, error_message: str) -> bool:
        """Set error status for a message."""
        message = self.get_message_by_id(message_id)
        if message:
            message.set_error(error_message)
            self.message_updated.emit(message)
            return True
        return False

    def clear_message_error(self, message_id: str) -> bool:
        """Clear error status for a message."""
        message = self.get_message_by_id(message_id)
        if message:
            message.clear_error()
            self.message_updated.emit(message)
            return True
        return False

    def remove_message(self, message_id: str) -> bool:
        """Remove a message by its ID."""
        for i, message in enumerate(self._messages):
            if message.message_id == message_id:
                self.beginRemoveRows(self.index(-1, -1), i, i)
                self._messages.pop(i)
                self.removeRow(i)
                self.endRemoveRows()
                self.message_removed.emit(message_id)
                return True
        return False

    def clear_all_messages(self) -> None:
        """Clear all messages from the model."""
        self.beginResetModel()
        self._messages.clear()
        self.clear()
        self.endResetModel()

    def get_all_messages(self) -> list[ChatMessage]:
        """Get all messages."""
        return self._messages.copy()

    @property
    def messages(self) -> list[ChatMessage]:
        """Property to access messages for testing compatibility."""
        return self._messages

    def get_messages_by_role(self, role: MessageRole) -> list[ChatMessage]:
        """Get messages filtered by role."""
        return [msg for msg in self._messages if msg.role == role]

    def get_recent_messages(self, limit: int) -> list[ChatMessage]:
        """Get the most recent messages."""
        if limit >= len(self._messages):
            return self._messages.copy()
        return self._messages[-limit:]

    def export_conversation_history(
        self, role_filter: MessageRole | None = None
    ) -> list[dict[str, Any]]:
        """Export conversation history as a list of dictionaries."""
        messages = self._messages
        if role_filter:
            messages = [msg for msg in messages if msg.role == role_filter]

        return [
            {
                "message_id": msg.message_id,
                "content": msg.content,
                "role": msg.role.value,
                "status": msg.status.value,
                "timestamp": msg.format_timestamp(),
                "error_message": msg.error_message,
                "metadata": msg.metadata,
            }
            for msg in messages
        ]
