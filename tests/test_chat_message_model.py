"""Unit tests for chat message model for PyQt6."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from PyQt6.QtGui import QStandardItemModel

from my_coding_agent.gui.chat_message_model import (
    ChatMessage,
    ChatMessageModel,
    MessageRole,
    MessageStatus,
)


class TestMessageRole:
    """Test the MessageRole enum."""

    def test_message_role_values(self):
        """Test that MessageRole has correct values."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_message_role_str_representation(self):
        """Test string representation of MessageRole."""
        assert str(MessageRole.USER) == "user"
        assert str(MessageRole.ASSISTANT) == "assistant"
        assert str(MessageRole.SYSTEM) == "system"


class TestMessageStatus:
    """Test the MessageStatus enum."""

    def test_message_status_values(self):
        """Test that MessageStatus has correct values."""
        assert MessageStatus.PENDING.value == "pending"
        assert MessageStatus.SENDING.value == "sending"
        assert MessageStatus.SENT.value == "sent"
        assert MessageStatus.DELIVERED.value == "delivered"
        assert MessageStatus.ERROR.value == "error"
        assert MessageStatus.TYPING.value == "typing"

    def test_message_status_str_representation(self):
        """Test string representation of MessageStatus."""
        assert str(MessageStatus.PENDING) == "pending"
        assert str(MessageStatus.SENDING) == "sending"
        assert str(MessageStatus.SENT) == "sent"
        assert str(MessageStatus.DELIVERED) == "delivered"
        assert str(MessageStatus.ERROR) == "error"
        assert str(MessageStatus.TYPING) == "typing"


class TestChatMessage:
    """Test the ChatMessage data class."""

    def test_create_user_message(self):
        """Test creating a user message."""
        message = ChatMessage.create_user_message("Hello, AI!")

        assert message.content == "Hello, AI!"
        assert message.role == MessageRole.USER
        assert message.status == MessageStatus.PENDING
        assert message.message_id is not None
        assert isinstance(message.timestamp, datetime)
        assert message.error_message is None
        assert message.metadata == {}

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        message = ChatMessage.create_assistant_message("Hello, human!")

        assert message.content == "Hello, human!"
        assert message.role == MessageRole.ASSISTANT
        assert message.status == MessageStatus.DELIVERED
        assert message.message_id is not None
        assert isinstance(message.timestamp, datetime)
        assert message.error_message is None
        assert message.metadata == {}

    def test_create_system_message(self):
        """Test creating a system message."""
        message = ChatMessage.create_system_message("System initialized")

        assert message.content == "System initialized"
        assert message.role == MessageRole.SYSTEM
        assert message.status == MessageStatus.DELIVERED
        assert message.message_id is not None
        assert isinstance(message.timestamp, datetime)
        assert message.error_message is None
        assert message.metadata == {}

    def test_create_message_with_metadata(self):
        """Test creating a message with metadata."""
        metadata = {"tokens": 150, "model": "gpt-4"}
        message = ChatMessage.create_assistant_message(
            "Response with metadata", metadata=metadata
        )

        assert message.metadata == metadata
        assert message.metadata["tokens"] == 150
        assert message.metadata["model"] == "gpt-4"

    def test_message_id_uniqueness(self):
        """Test that each message gets a unique ID."""
        message1 = ChatMessage.create_user_message("Message 1")
        message2 = ChatMessage.create_user_message("Message 2")

        assert message1.message_id != message2.message_id

    def test_set_status(self):
        """Test setting message status."""
        message = ChatMessage.create_user_message("Test message")

        message.set_status(MessageStatus.SENDING)
        assert message.status == MessageStatus.SENDING

        message.set_status(MessageStatus.SENT)
        assert message.status == MessageStatus.SENT

    def test_set_error(self):
        """Test setting error status and message."""
        message = ChatMessage.create_user_message("Test message")

        message.set_error("Network error occurred")
        assert message.status == MessageStatus.ERROR
        assert message.error_message == "Network error occurred"

    def test_clear_error(self):
        """Test clearing error status."""
        message = ChatMessage.create_user_message("Test message")
        message.set_error("Some error")

        message.clear_error()
        assert message.error_message is None
        assert message.status == MessageStatus.PENDING

    def test_is_user_message(self):
        """Test checking if message is from user."""
        user_msg = ChatMessage.create_user_message("User message")
        assistant_msg = ChatMessage.create_assistant_message("Assistant message")

        assert user_msg.is_user_message() is True
        assert assistant_msg.is_user_message() is False

    def test_is_assistant_message(self):
        """Test checking if message is from assistant."""
        user_msg = ChatMessage.create_user_message("User message")
        assistant_msg = ChatMessage.create_assistant_message("Assistant message")

        assert user_msg.is_assistant_message() is False
        assert assistant_msg.is_assistant_message() is True

    def test_is_system_message(self):
        """Test checking if message is system message."""
        user_msg = ChatMessage.create_user_message("User message")
        system_msg = ChatMessage.create_system_message("System message")

        assert user_msg.is_system_message() is False
        assert system_msg.is_system_message() is True

    def test_has_error(self):
        """Test checking if message has error."""
        message = ChatMessage.create_user_message("Test message")

        assert message.has_error() is False

        message.set_error("Error occurred")
        assert message.has_error() is True

        message.clear_error()
        assert message.has_error() is False

    def test_message_equality(self):
        """Test message equality based on message_id."""
        message1 = ChatMessage.create_user_message("Test message")
        message2 = ChatMessage.create_user_message("Test message")

        # Different messages should not be equal
        assert message1 != message2

        # Same message instance should be equal to itself
        assert message1 == message1

    def test_message_repr(self):
        """Test string representation of message."""
        message = ChatMessage.create_user_message("Hello")
        repr_str = repr(message)

        assert "ChatMessage" in repr_str
        assert "user" in repr_str
        assert "Hello" in repr_str

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        message = ChatMessage.create_user_message("Test message")
        formatted = message.format_timestamp()

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_timestamp_custom_format(self):
        """Test timestamp formatting with custom format."""
        message = ChatMessage.create_user_message("Test message")
        formatted = message.format_timestamp("%H:%M")

        assert isinstance(formatted, str)
        assert ":" in formatted  # Should contain time separator


class TestChatMessageModel:
    """Test the ChatMessageModel class."""

    @pytest.fixture
    def message_model(self):
        """Create a ChatMessageModel instance for testing."""
        return ChatMessageModel()

    def test_model_initialization(self, message_model):
        """Test model initialization."""
        assert isinstance(message_model, QStandardItemModel)
        assert message_model.rowCount() == 0
        assert len(message_model._messages) == 0

    def test_add_message(self, message_model):
        """Test adding a message to the model."""
        message = ChatMessage.create_user_message("Hello")

        message_model.add_message(message)

        assert message_model.rowCount() == 1
        assert len(message_model._messages) == 1
        assert message_model._messages[0] == message

    def test_add_multiple_messages(self, message_model):
        """Test adding multiple messages."""
        messages = [
            ChatMessage.create_user_message("Hello"),
            ChatMessage.create_assistant_message("Hi there!"),
            ChatMessage.create_user_message("How are you?"),
        ]

        for message in messages:
            message_model.add_message(message)

        assert message_model.rowCount() == 3
        assert len(message_model._messages) == 3

    def test_get_message(self, message_model):
        """Test getting a message by index."""
        message = ChatMessage.create_user_message("Test message")
        message_model.add_message(message)

        retrieved = message_model.get_message(0)
        assert retrieved == message

    def test_get_message_invalid_index(self, message_model):
        """Test getting message with invalid index."""
        assert message_model.get_message(-1) is None
        assert message_model.get_message(0) is None
        assert message_model.get_message(100) is None

    def test_get_message_by_id(self, message_model):
        """Test getting a message by ID."""
        message = ChatMessage.create_user_message("Test message")
        message_model.add_message(message)

        retrieved = message_model.get_message_by_id(message.message_id)
        assert retrieved == message

    def test_get_message_by_invalid_id(self, message_model):
        """Test getting message with invalid ID."""
        assert message_model.get_message_by_id("nonexistent") is None

    def test_update_message_status(self, message_model):
        """Test updating message status."""
        message = ChatMessage.create_user_message("Test message")
        message_model.add_message(message)

        success = message_model.update_message_status(
            message.message_id, MessageStatus.SENT
        )

        assert success is True
        assert message.status == MessageStatus.SENT

    def test_update_message_status_invalid_id(self, message_model):
        """Test updating status with invalid message ID."""
        success = message_model.update_message_status("invalid", MessageStatus.SENT)
        assert success is False

    def test_set_message_error(self, message_model):
        """Test setting message error."""
        message = ChatMessage.create_user_message("Test message")
        message_model.add_message(message)

        success = message_model.set_message_error(message.message_id, "Network error")

        assert success is True
        assert message.has_error() is True
        assert message.error_message == "Network error"

    def test_set_message_error_invalid_id(self, message_model):
        """Test setting error with invalid message ID."""
        success = message_model.set_message_error("invalid", "Error")
        assert success is False

    def test_clear_message_error(self, message_model):
        """Test clearing message error."""
        message = ChatMessage.create_user_message("Test message")
        message.set_error("Some error")
        message_model.add_message(message)

        success = message_model.clear_message_error(message.message_id)

        assert success is True
        assert message.has_error() is False

    def test_clear_message_error_invalid_id(self, message_model):
        """Test clearing error with invalid message ID."""
        success = message_model.clear_message_error("invalid")
        assert success is False

    def test_remove_message(self, message_model):
        """Test removing a message."""
        message = ChatMessage.create_user_message("Test message")
        message_model.add_message(message)

        success = message_model.remove_message(message.message_id)

        assert success is True
        assert message_model.rowCount() == 0
        assert len(message_model._messages) == 0

    def test_remove_message_invalid_id(self, message_model):
        """Test removing message with invalid ID."""
        success = message_model.remove_message("invalid")
        assert success is False

    def test_clear_all_messages(self, message_model):
        """Test clearing all messages."""
        messages = [
            ChatMessage.create_user_message("Message 1"),
            ChatMessage.create_assistant_message("Message 2"),
            ChatMessage.create_user_message("Message 3"),
        ]

        for message in messages:
            message_model.add_message(message)

        message_model.clear_all_messages()

        assert message_model.rowCount() == 0
        assert len(message_model._messages) == 0

    def test_get_all_messages(self, message_model):
        """Test getting all messages."""
        messages = [
            ChatMessage.create_user_message("Message 1"),
            ChatMessage.create_assistant_message("Message 2"),
        ]

        for message in messages:
            message_model.add_message(message)

        all_messages = message_model.get_all_messages()

        assert len(all_messages) == 2
        assert all_messages[0] == messages[0]
        assert all_messages[1] == messages[1]

    def test_get_messages_by_role(self, message_model):
        """Test getting messages filtered by role."""
        user_msg1 = ChatMessage.create_user_message("User message 1")
        assistant_msg = ChatMessage.create_assistant_message("Assistant message")
        user_msg2 = ChatMessage.create_user_message("User message 2")

        message_model.add_message(user_msg1)
        message_model.add_message(assistant_msg)
        message_model.add_message(user_msg2)

        user_messages = message_model.get_messages_by_role(MessageRole.USER)
        assistant_messages = message_model.get_messages_by_role(MessageRole.ASSISTANT)

        assert len(user_messages) == 2
        assert len(assistant_messages) == 1
        assert user_messages[0] == user_msg1
        assert user_messages[1] == user_msg2
        assert assistant_messages[0] == assistant_msg

    def test_get_recent_messages(self, message_model):
        """Test getting recent messages."""
        messages = [ChatMessage.create_user_message(f"Message {i}") for i in range(10)]

        for message in messages:
            message_model.add_message(message)

        # Get last 5 messages
        recent = message_model.get_recent_messages(5)

        assert len(recent) == 5
        assert recent[0] == messages[5]  # Index 5-9 are the last 5
        assert recent[4] == messages[9]

    def test_get_recent_messages_limit_exceeds_total(self, message_model):
        """Test getting recent messages when limit exceeds total."""
        messages = [ChatMessage.create_user_message(f"Message {i}") for i in range(3)]

        for message in messages:
            message_model.add_message(message)

        recent = message_model.get_recent_messages(10)

        assert len(recent) == 3
        assert recent == messages

    def test_message_signals_emitted(self, message_model):
        """Test that appropriate signals are emitted."""
        # Mock the signals
        message_model.message_added = Mock()
        message_model.message_updated = Mock()
        message_model.message_removed = Mock()

        # Add message
        message = ChatMessage.create_user_message("Test")
        message_model.add_message(message)
        message_model.message_added.emit.assert_called_once()

        # Update message status
        message_model.update_message_status(message.message_id, MessageStatus.SENT)
        message_model.message_updated.emit.assert_called()

        # Remove message
        message_model.remove_message(message.message_id)
        message_model.message_removed.emit.assert_called_once()

    def test_conversation_history_export(self, message_model):
        """Test exporting conversation history."""
        messages = [
            ChatMessage.create_user_message("Hello"),
            ChatMessage.create_assistant_message("Hi there!"),
            ChatMessage.create_user_message("How are you?"),
            ChatMessage.create_assistant_message("I'm doing well!"),
        ]

        for message in messages:
            message_model.add_message(message)

        history = message_model.export_conversation_history()

        assert len(history) == 4
        for i, exported in enumerate(history):
            assert exported["content"] == messages[i].content
            assert exported["role"] == messages[i].role.value
            assert "timestamp" in exported
            assert "message_id" in exported

    def test_conversation_history_export_with_filters(self, message_model):
        """Test exporting conversation history with role filter."""
        messages = [
            ChatMessage.create_user_message("Hello"),
            ChatMessage.create_assistant_message("Hi there!"),
            ChatMessage.create_user_message("How are you?"),
        ]

        for message in messages:
            message_model.add_message(message)

        # Export only user messages
        user_history = message_model.export_conversation_history(
            role_filter=MessageRole.USER
        )

        assert len(user_history) == 2
        assert all(msg["role"] == "user" for msg in user_history)
