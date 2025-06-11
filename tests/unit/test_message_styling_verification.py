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

        # Check that user message has border styling
        style_sheet = bubble.styleSheet()
        assert "border:" in style_sheet or "border-radius:" in style_sheet
        assert "SimplifiedMessageBubble" in style_sheet

        # User messages should have max-width constraints
        assert "max-width:" in style_sheet

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
        assert "background-color: transparent" in style_sheet
        assert "border: none" in style_sheet

        # AI messages should NOT have max-width constraints
        assert "max-width:" not in style_sheet

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

        # Get their styling
        user_style = user_bubble.styleSheet()
        ai_style = ai_bubble.styleSheet()

        # They should have different styling
        assert user_style != ai_style

        # User should have borders, AI should not
        assert "border:" in user_style or "border-radius:" in user_style
        assert "border: none" in ai_style

        # User should have background color, AI should be transparent
        assert "border: 2px solid" in user_style or "border-radius:" in user_style
        assert "background-color: transparent" in ai_style

    def test_system_message_has_distinct_styling(self, chat_widget):
        """Test that system messages have their own distinct styling."""
        # Add a system message
        sys_msg_id = chat_widget.add_system_message("This is a system message")

        # Get the message bubble
        bubble = chat_widget.display_area._message_bubbles.get(sys_msg_id)
        assert bubble is not None

        # Check that system message has distinct styling
        style_sheet = bubble.styleSheet()
        assert "SimplifiedMessageBubble" in style_sheet

        # System messages should have their own background (different from AI transparent)
        # AI messages use "background-color: transparent" for the bubble itself
        # System messages have a colored background like #404040
        assert "#404040" in style_sheet or "#fff3cd" in style_sheet

        # Should have some kind of border or background
        assert "border:" in style_sheet or "background-color:" in style_sheet

    def test_theme_affects_message_styling(self, chat_widget):
        """Test that changing theme affects message styling."""
        # Add a user message
        user_msg_id = chat_widget.add_user_message("Test message")
        bubble = chat_widget.display_area._message_bubbles.get(user_msg_id)
        assert bubble is not None

        # Get styling in dark theme
        dark_style = bubble.styleSheet()

        # Apply light theme
        chat_widget.apply_theme("light")

        # Get styling in light theme
        light_style = bubble.styleSheet()

        # Styling should be different between themes
        assert dark_style != light_style

    def test_message_content_display(self, chat_widget):
        """Test that message content is properly displayed in text widgets."""
        # Add messages
        user_msg_id = chat_widget.add_user_message("User message content")
        ai_msg_id = chat_widget.add_assistant_message("AI message content")

        # Get bubbles
        user_bubble = chat_widget.display_area._message_bubbles.get(user_msg_id)
        ai_bubble = chat_widget.display_area._message_bubbles.get(ai_msg_id)

        assert user_bubble is not None
        assert ai_bubble is not None

        # Check content is displayed
        user_content = user_bubble.content_display.toPlainText()
        ai_content = ai_bubble.content_display.toPlainText()

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
