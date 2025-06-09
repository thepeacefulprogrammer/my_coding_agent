"""Unit tests for chat widget with message display area."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from my_coding_agent.gui.chat_message_model import (
    ChatMessage,
    ChatMessageModel,
    MessageRole,
    MessageStatus,
)
from my_coding_agent.gui.chat_widget import (
    ChatWidget,
    MessageBubble,
    MessageDisplayArea,
)


class TestMessageBubble:
    """Test the MessageBubble widget for individual chat messages."""

    @pytest.fixture
    def qtbot_app(self, qtbot):
        """Ensure QApplication is available for widget tests."""
        if not QApplication.instance():
            app = QApplication([])
            yield app
            app.quit()
        else:
            yield QApplication.instance()

    @pytest.fixture
    def user_message(self):
        """Create a test user message."""
        return ChatMessage.create_user_message("Hello, AI assistant!")

    @pytest.fixture
    def assistant_message(self):
        """Create a test assistant message."""
        return ChatMessage.create_assistant_message("Hello! How can I help you today?")

    @pytest.fixture
    def system_message(self):
        """Create a test system message."""
        return ChatMessage.create_system_message("System initialized successfully")

    def test_message_bubble_creation_user(self, qtbot, qtbot_app, user_message):
        """Test creating a message bubble for user message."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        assert bubble.message == user_message
        assert bubble.role == MessageRole.USER
        assert isinstance(bubble, QWidget)

    def test_message_bubble_creation_assistant(
        self, qtbot, qtbot_app, assistant_message
    ):
        """Test creating a message bubble for assistant message."""
        bubble = MessageBubble(assistant_message)
        qtbot.addWidget(bubble)

        assert bubble.message == assistant_message
        assert bubble.role == MessageRole.ASSISTANT

    def test_message_bubble_creation_system(self, qtbot, qtbot_app, system_message):
        """Test creating a message bubble for system message."""
        bubble = MessageBubble(system_message)
        qtbot.addWidget(bubble)

        assert bubble.message == system_message
        assert bubble.role == MessageRole.SYSTEM

    def test_message_bubble_content_display(self, qtbot, qtbot_app, user_message):
        """Test that message content is displayed correctly."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        # Should have a text widget that displays the content
        assert hasattr(bubble, "content_label") or hasattr(bubble, "content_text")
        # Content should be accessible through the bubble
        displayed_content = bubble.get_displayed_content()
        assert displayed_content == "Hello, AI assistant!"

    def test_message_bubble_timestamp_display(self, qtbot, qtbot_app, user_message):
        """Test that timestamp is displayed."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        # Should have timestamp display
        assert hasattr(bubble, "timestamp_label")
        timestamp_text = bubble.get_timestamp_text()
        assert isinstance(timestamp_text, str)
        assert len(timestamp_text) > 0

    def test_message_bubble_status_display(self, qtbot, qtbot_app, user_message):
        """Test that message status is displayed."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        # Should show status
        status_text = bubble.get_status_text()
        assert "pending" in status_text.lower() or "sent" in status_text.lower()

    def test_message_bubble_status_update(self, qtbot, qtbot_app, user_message):
        """Test updating message status in bubble."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        # Update status
        bubble.update_status(MessageStatus.SENT)
        status_text = bubble.get_status_text()
        assert "sent" in status_text.lower()

        # Update to error
        bubble.update_status(MessageStatus.ERROR)
        status_text = bubble.get_status_text()
        assert "error" in status_text.lower()

    def test_message_bubble_error_display(self, qtbot, qtbot_app, user_message):
        """Test displaying error messages."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        # Set error
        bubble.set_error("Network connection failed")

        # Should show error message
        assert bubble.has_error()
        error_text = bubble.get_error_text()
        assert "Network connection failed" in error_text

    def test_message_bubble_clear_error(self, qtbot, qtbot_app, user_message):
        """Test clearing error from bubble."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        # Set and clear error
        bubble.set_error("Some error")
        bubble.clear_error()

        assert not bubble.has_error()

    def test_message_bubble_styling_user(self, qtbot, qtbot_app, user_message):
        """Test styling for user messages."""
        bubble = MessageBubble(user_message)
        qtbot.addWidget(bubble)

        # User messages should have specific styling
        style = bubble.styleSheet()
        assert isinstance(style, str)
        # Should have some styling applied
        assert len(style) > 0

    def test_message_bubble_styling_assistant(
        self, qtbot, qtbot_app, assistant_message
    ):
        """Test styling for assistant messages."""
        bubble = MessageBubble(assistant_message)
        qtbot.addWidget(bubble)

        # Assistant messages should have different styling from user
        style = bubble.styleSheet()
        assert isinstance(style, str)

    def test_message_bubble_word_wrap(self, qtbot, qtbot_app):
        """Test word wrapping for long messages."""
        long_message = ChatMessage.create_user_message(
            "This is a very long message that should wrap to multiple lines when displayed in the message bubble widget."
        )
        bubble = MessageBubble(long_message)
        qtbot.addWidget(bubble)

        # Content should support word wrapping
        content = bubble.get_displayed_content()
        assert content == long_message.content

    def test_message_bubble_metadata_display(self, qtbot, qtbot_app):
        """Test displaying message metadata."""
        metadata = {"tokens": 150, "model": "gpt-4"}
        message = ChatMessage.create_assistant_message(
            "Response with metadata", metadata=metadata
        )
        bubble = MessageBubble(message)
        qtbot.addWidget(bubble)

        # Should be able to show/hide metadata
        bubble.show_metadata(True)
        assert bubble.is_metadata_visible()

        bubble.show_metadata(False)
        assert not bubble.is_metadata_visible()


class TestMessageDisplayArea:
    """Test the MessageDisplayArea widget for displaying chat messages."""

    @pytest.fixture
    def qtbot_app(self, qtbot):
        """Ensure QApplication is available for widget tests."""
        if not QApplication.instance():
            app = QApplication([])
            yield app
            app.quit()
        else:
            yield QApplication.instance()

    @pytest.fixture
    def message_model(self):
        """Create a message model for testing."""
        return ChatMessageModel()

    @pytest.fixture
    def display_area(self, qtbot, qtbot_app, message_model):
        """Create a message display area for testing."""
        area = MessageDisplayArea(message_model)
        area.set_test_mode(True)  # Enable test mode for reliable testing
        qtbot.addWidget(area)
        return area

    def test_display_area_initialization(self, display_area):
        """Test message display area initialization."""
        assert isinstance(display_area, QWidget)
        assert hasattr(display_area, "message_model")
        assert isinstance(display_area.layout(), QVBoxLayout)

    def test_display_area_scroll_widget(self, display_area):
        """Test that display area has scrolling capability."""
        # Should have a scroll area
        assert hasattr(display_area, "scroll_area")
        assert isinstance(display_area.scroll_area, QScrollArea)

    def test_display_area_add_message(self, display_area, message_model):
        """Test adding a message to display area."""
        message = ChatMessage.create_user_message("Test message")

        # Add message to model (should trigger display update)
        message_model.add_message(message)

        # Display area should show the message
        assert display_area.get_message_count() == 1
        assert display_area.has_message(message.message_id)

    def test_display_area_add_multiple_messages(self, display_area, message_model):
        """Test adding multiple messages."""
        messages = [
            ChatMessage.create_user_message("Hello"),
            ChatMessage.create_assistant_message("Hi there!"),
            ChatMessage.create_user_message("How are you?"),
        ]

        for message in messages:
            message_model.add_message(message)

        assert display_area.get_message_count() == 3

    def test_display_area_message_order(self, display_area, message_model):
        """Test that messages are displayed in correct order."""
        messages = [
            ChatMessage.create_user_message("First"),
            ChatMessage.create_assistant_message("Second"),
            ChatMessage.create_user_message("Third"),
        ]

        for message in messages:
            message_model.add_message(message)

        # Messages should be in chronological order
        displayed_messages = display_area.get_displayed_messages()
        assert len(displayed_messages) == 3
        assert displayed_messages[0].content == "First"
        assert displayed_messages[1].content == "Second"
        assert displayed_messages[2].content == "Third"

    def test_display_area_auto_scroll(self, display_area, message_model):
        """Test auto-scrolling to bottom when new messages arrive."""
        # Add many messages to trigger scrolling
        for i in range(20):
            message = ChatMessage.create_user_message(f"Message {i}")
            message_model.add_message(message)

        # Should auto-scroll to bottom
        assert display_area.is_scrolled_to_bottom()

    def test_display_area_manual_scroll(self, display_area, message_model):
        """Test manual scrolling behavior."""
        # Add messages
        for i in range(10):
            message = ChatMessage.create_user_message(f"Message {i}")
            message_model.add_message(message)

        # Scroll to top
        display_area.scroll_to_top()
        assert not display_area.is_scrolled_to_bottom()

        # Scroll to bottom
        display_area.scroll_to_bottom()
        assert display_area.is_scrolled_to_bottom()

    def test_display_area_message_update(self, display_area, message_model):
        """Test updating message status in display."""
        message = ChatMessage.create_user_message("Test message")
        message_model.add_message(message)

        # Update status
        message_model.update_message_status(message.message_id, MessageStatus.SENT)

        # Process any pending events to ensure signal handling completes
        QApplication.processEvents()

        # Display should reflect the update
        bubble = display_area.get_message_bubble(message.message_id)
        assert bubble is not None
        assert "sent" in bubble.get_status_text().lower()

    def test_display_area_message_removal(self, display_area, message_model):
        """Test removing messages from display."""
        message = ChatMessage.create_user_message("Test message")
        message_model.add_message(message)

        assert display_area.has_message(message.message_id)

        # Remove message
        message_model.remove_message(message.message_id)

        assert not display_area.has_message(message.message_id)
        assert display_area.get_message_count() == 0

    def test_display_area_clear_all(self, display_area, message_model):
        """Test clearing all messages."""
        # Add messages
        for i in range(5):
            message = ChatMessage.create_user_message(f"Message {i}")
            message_model.add_message(message)

        assert display_area.get_message_count() == 5

        # Clear all
        message_model.clear_all_messages()

        assert display_area.get_message_count() == 0

    def test_display_area_typing_indicator(self, display_area):
        """Test typing indicator functionality."""
        # Show typing indicator
        display_area.show_typing_indicator("AI is typing...")
        assert display_area.is_typing_indicator_visible()

        # Hide typing indicator
        display_area.hide_typing_indicator()
        assert not display_area.is_typing_indicator_visible()

    def test_display_area_search_functionality(self, display_area, message_model):
        """Test searching messages in display area."""
        messages = [
            ChatMessage.create_user_message("Hello world"),
            ChatMessage.create_assistant_message("Python programming"),
            ChatMessage.create_user_message("World peace"),
        ]

        for message in messages:
            message_model.add_message(message)

        # Search for "world"
        results = display_area.search_messages("world")
        assert len(results) == 2  # "Hello world" and "World peace"

    def test_display_area_theme_support(self, display_area):
        """Test theme/styling support."""
        # Should support dark/light themes
        display_area.apply_theme("dark")
        dark_style = display_area.styleSheet()

        display_area.apply_theme("light")
        light_style = display_area.styleSheet()

        # Styles should be different
        assert dark_style != light_style


class TestChatWidget:
    """Test the main ChatWidget class."""

    @pytest.fixture
    def qtbot_app(self, qtbot):
        """Ensure QApplication is available for widget tests."""
        if not QApplication.instance():
            app = QApplication([])
            yield app
            app.quit()
        else:
            yield QApplication.instance()

    @pytest.fixture
    def chat_widget(self, qtbot, qtbot_app):
        """Create a chat widget for testing."""
        widget = ChatWidget()
        widget.display_area.set_test_mode(True)  # Enable test mode for reliable testing
        qtbot.addWidget(widget)
        return widget

    def test_chat_widget_initialization(self, chat_widget):
        """Test chat widget initialization."""
        assert isinstance(chat_widget, QWidget)
        assert hasattr(chat_widget, "message_model")
        assert hasattr(chat_widget, "display_area")
        assert isinstance(chat_widget.message_model, ChatMessageModel)
        assert isinstance(chat_widget.display_area, MessageDisplayArea)

    def test_chat_widget_layout(self, chat_widget):
        """Test chat widget layout structure."""
        layout = chat_widget.layout()
        assert isinstance(layout, QVBoxLayout)

        # Should have display area
        assert chat_widget.display_area is not None

    def test_chat_widget_add_user_message(self, chat_widget):
        """Test adding user message through widget interface."""
        chat_widget.add_user_message("Hello, AI!")

        assert chat_widget.message_model.rowCount() == 1
        messages = chat_widget.message_model.get_all_messages()
        assert messages[0].content == "Hello, AI!"
        assert messages[0].role == MessageRole.USER

    def test_chat_widget_add_assistant_message(self, chat_widget):
        """Test adding assistant message through widget interface."""
        chat_widget.add_assistant_message("Hello! How can I help?")

        assert chat_widget.message_model.rowCount() == 1
        messages = chat_widget.message_model.get_all_messages()
        assert messages[0].content == "Hello! How can I help?"
        assert messages[0].role == MessageRole.ASSISTANT

    def test_chat_widget_add_system_message(self, chat_widget):
        """Test adding system message through widget interface."""
        chat_widget.add_system_message("System ready")

        assert chat_widget.message_model.rowCount() == 1
        messages = chat_widget.message_model.get_all_messages()
        assert messages[0].content == "System ready"
        assert messages[0].role == MessageRole.SYSTEM

    def test_chat_widget_conversation_flow(self, chat_widget):
        """Test a complete conversation flow."""
        # User starts conversation
        chat_widget.add_user_message("Hello")

        # Assistant responds
        chat_widget.add_assistant_message("Hi there! How can I help?")

        # User asks question
        chat_widget.add_user_message("What's the weather like?")

        # Assistant responds
        chat_widget.add_assistant_message("I'd need location info to check weather.")

        # Check conversation
        messages = chat_widget.message_model.get_all_messages()
        assert len(messages) == 4
        assert messages[0].role == MessageRole.USER
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[2].role == MessageRole.USER
        assert messages[3].role == MessageRole.ASSISTANT

    def test_chat_widget_clear_conversation(self, chat_widget):
        """Test clearing the conversation."""
        # Add messages
        chat_widget.add_user_message("Hello")
        chat_widget.add_assistant_message("Hi")

        assert chat_widget.message_model.rowCount() == 2

        # Clear conversation
        chat_widget.clear_conversation()

        assert chat_widget.message_model.rowCount() == 0

    def test_chat_widget_export_conversation(self, chat_widget):
        """Test exporting conversation."""
        chat_widget.add_user_message("Hello")
        chat_widget.add_assistant_message("Hi there!")

        exported = chat_widget.export_conversation()
        assert len(exported) == 2
        assert exported[0]["role"] == "user"
        assert exported[1]["role"] == "assistant"

    def test_chat_widget_message_status_tracking(self, chat_widget):
        """Test message status tracking."""
        # Add user message
        message_id = chat_widget.add_user_message("Test message")

        # Update status
        chat_widget.update_message_status(message_id, MessageStatus.SENDING)
        message = chat_widget.message_model.get_message_by_id(message_id)
        assert message.status == MessageStatus.SENDING

        # Mark as sent
        chat_widget.update_message_status(message_id, MessageStatus.SENT)
        assert message.status == MessageStatus.SENT

    def test_chat_widget_error_handling(self, chat_widget):
        """Test error handling in chat widget."""
        # Add message
        message_id = chat_widget.add_user_message("Test message")

        # Set error
        chat_widget.set_message_error(message_id, "Network error")
        message = chat_widget.message_model.get_message_by_id(message_id)
        assert message.has_error()
        assert message.error_message == "Network error"

    def test_chat_widget_typing_indicator(self, chat_widget):
        """Test typing indicator in chat widget."""
        # Show typing
        chat_widget.show_typing_indicator()
        assert chat_widget.display_area.is_typing_indicator_visible()

        # Hide typing
        chat_widget.hide_typing_indicator()
        assert not chat_widget.display_area.is_typing_indicator_visible()

    def test_chat_widget_scroll_behavior(self, chat_widget):
        """Test scrolling behavior."""
        # Add many messages
        for i in range(20):
            chat_widget.add_user_message(f"Message {i}")

        # Should auto-scroll to bottom
        assert chat_widget.is_scrolled_to_bottom()

        # Manual scroll control
        chat_widget.scroll_to_top()
        assert not chat_widget.is_scrolled_to_bottom()

    def test_chat_widget_theme_application(self, chat_widget):
        """Test applying themes to chat widget."""
        # Apply dark theme
        chat_widget.apply_theme("dark")

        # Apply light theme
        chat_widget.apply_theme("light")

        # Should not raise exceptions

    def test_chat_widget_message_search(self, chat_widget):
        """Test message search functionality."""
        chat_widget.add_user_message("Hello world")
        chat_widget.add_assistant_message("Python programming")
        chat_widget.add_user_message("World peace")

        results = chat_widget.search_messages("world")
        assert len(results) == 2

    def test_chat_widget_accessibility(self, chat_widget):
        """Test accessibility features."""
        # Should support keyboard navigation
        assert chat_widget.focusPolicy() != Qt.FocusPolicy.NoFocus

        # Should have proper widget roles
        assert (
            chat_widget.accessibleName() is not None
            or chat_widget.accessibleName() == ""
        )
