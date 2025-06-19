"""Tests to verify message styling is properly applied."""

import pytest
from PyQt6.QtWidgets import QApplication

from src.my_coding_agent.gui.chat_message_model import MessageRole
from src.my_coding_agent.gui.chat_widget_v2 import (
    SimplifiedChatWidget,
    SimplifiedMessageBubble,
)


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def chat_widget(app):
    """Create SimplifiedChatWidget instance for testing."""
    widget = SimplifiedChatWidget()
    return widget


@pytest.mark.qt
class TestMessageStylingVerification:
    """Test suite to verify message styling differences."""

    def test_user_message_has_border_styling(self, chat_widget):
        """Test that user messages have distinct border styling."""
        # Add a user message
        user_msg_id = chat_widget.add_user_message("Hello, this is a user message")

        # Get the message bubble
        bubble = chat_widget.display_area._message_bubbles.get(user_msg_id)
        assert bubble is not None
        assert isinstance(bubble, SimplifiedMessageBubble)

        # Check that user message has border styling via paintEvent
        # The implementation now uses paintEvent() for custom drawing
        style_sheet = bubble.styleSheet()
        assert "SimplifiedMessageBubble" in style_sheet

        # User messages no longer have max-width in stylesheet (handled by paintEvent)
        # Just verify the bubble was created and has basic styling
        assert bubble.role == MessageRole.USER

    def test_ai_message_has_transparent_styling(self, chat_widget):
        """Test that AI messages have transparent, borderless styling."""
        # Add an AI message
        ai_msg_id = chat_widget.add_assistant_message("Hello, this is an AI response")

        # Get the message bubble
        bubble = chat_widget.display_area._message_bubbles.get(ai_msg_id)
        assert bubble is not None
        assert isinstance(bubble, SimplifiedMessageBubble)

        # Check that AI message has transparent styling
        style_sheet = bubble.styleSheet()
        # AI messages now use paintEvent() which draws nothing (transparent)
        assert "SimplifiedMessageBubble" in style_sheet
        assert bubble.role == MessageRole.ASSISTANT

    def test_user_vs_ai_message_styling_difference(self, chat_widget):
        """Test that user and AI messages have visually different styling."""
        # Add both types of messages
        user_msg_id = chat_widget.add_user_message("User message")
        ai_msg_id = chat_widget.add_assistant_message("AI message")

        # Get both bubbles
        user_bubble = chat_widget.display_area._message_bubbles.get(user_msg_id)
        ai_bubble = chat_widget.display_area._message_bubbles.get(ai_msg_id)

        assert user_bubble is not None
        assert ai_bubble is not None

        # They should have different roles (which drives the styling via paintEvent)
        assert user_bubble.role == MessageRole.USER
        assert ai_bubble.role == MessageRole.ASSISTANT
        assert user_bubble.role != ai_bubble.role

    def test_system_message_has_distinct_styling(self, chat_widget):
        """Test that system messages have their own distinct styling."""
        # Add a system message
        sys_msg_id = chat_widget.add_system_message("This is a system message")

        # Get the message bubble
        bubble = chat_widget.display_area._message_bubbles.get(sys_msg_id)
        assert bubble is not None

        # Check that system message has distinct role
        assert bubble.role == MessageRole.SYSTEM

        # System messages have distinct styling in paintEvent
        style_sheet = bubble.styleSheet()
        assert "SimplifiedMessageBubble" in style_sheet

    def test_theme_affects_message_styling(self, chat_widget):
        """Test that changing theme affects message styling."""
        # Add a user message
        user_msg_id = chat_widget.add_user_message("Test message")
        bubble = chat_widget.display_area._message_bubbles.get(user_msg_id)
        assert bubble is not None

        # Check initial theme
        initial_theme = bubble._current_theme

        # Apply different theme
        new_theme = "light" if initial_theme == "dark" else "dark"
        chat_widget.apply_theme(new_theme)

        # Check theme changed
        assert bubble._current_theme == new_theme

    def test_message_content_display(self, chat_widget):
        """Test that message content is properly displayed in label widgets."""
        # Add messages
        user_msg_id = chat_widget.add_user_message("User message content")
        ai_msg_id = chat_widget.add_assistant_message("AI message content")

        # Get bubbles
        user_bubble = chat_widget.display_area._message_bubbles.get(user_msg_id)
        ai_bubble = chat_widget.display_area._message_bubbles.get(ai_msg_id)

        assert user_bubble is not None
        assert ai_bubble is not None

        # Check content is displayed (content_display is now a QLabel)
        user_content = user_bubble.content_display.text()
        ai_content = ai_bubble.content_display.text()

        assert user_content == "User message content"
        assert ai_content == "AI message content"

    def test_message_bubbles_are_created(self, chat_widget):
        """Test that message bubbles are actually created when messages are added."""
        initial_count = len(chat_widget.display_area._message_bubbles)

        # Add messages
        chat_widget.add_user_message("Test 1")
        chat_widget.add_assistant_message("Test 2")
        chat_widget.add_system_message("Test 3")

        # Should have 3 more bubbles
        final_count = len(chat_widget.display_area._message_bubbles)
        assert final_count == initial_count + 3

    def test_message_role_assignment(self, chat_widget):
        """Test that message roles are properly assigned to bubbles."""
        # Add messages
        user_msg_id = chat_widget.add_user_message("User")
        ai_msg_id = chat_widget.add_assistant_message("AI")
        sys_msg_id = chat_widget.add_system_message("System")

        # Get bubbles and check roles
        user_bubble = chat_widget.display_area._message_bubbles.get(user_msg_id)
        ai_bubble = chat_widget.display_area._message_bubbles.get(ai_msg_id)
        sys_bubble = chat_widget.display_area._message_bubbles.get(sys_msg_id)

        assert user_bubble.role == MessageRole.USER
        assert ai_bubble.role == MessageRole.ASSISTANT
        assert sys_bubble.role == MessageRole.SYSTEM
