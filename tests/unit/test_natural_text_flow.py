"""
Unit tests for natural text flow implementation (Task 3.1).

Tests that AI assistant messages display with natural text flow instead of bubbles,
while user messages retain their bubble styling.
"""

from my_coding_agent.gui.chat_message_model import (
    ChatMessage,
    MessageRole,
    MessageStatus,
)
from my_coding_agent.gui.chat_widget import MessageBubble


class TestNaturalTextFlow:
    """Test natural text flow implementation for AI messages."""

    def test_assistant_message_natural_flow_light_theme(self, qapp):
        """Test that assistant messages have natural text flow styling in light theme."""
        message = ChatMessage(
            content="This is an AI response with natural text flow.",
            role=MessageRole.ASSISTANT,
            status=MessageStatus.SENT,
        )

        bubble = MessageBubble(message)
        bubble.apply_theme("light")

        # Check that the bubble has transparent background and no border styling
        style = bubble.styleSheet()
        assert "background-color: transparent" in style
        assert "border: none" in style
        assert "border-radius: 0px" in style

        # Verify maximum width is removed for natural flow
        assert bubble.maximumWidth() == 16777215  # Qt's max width value

    def test_assistant_message_natural_flow_dark_theme(self, qapp):
        """Test that assistant messages have natural text flow styling in dark theme."""
        message = ChatMessage(
            content="This is an AI response with natural text flow in dark theme.",
            role=MessageRole.ASSISTANT,
            status=MessageStatus.SENT,
        )

        bubble = MessageBubble(message)
        bubble.apply_theme("dark")

        # Check that the bubble has transparent background and no border styling
        style = bubble.styleSheet()
        assert "background-color: transparent" in style
        assert "border: none" in style
        assert "border-radius: 0px" in style

        # Verify maximum width is removed for natural flow
        assert bubble.maximumWidth() == 16777215

    def test_user_message_retains_bubble_styling(self, qapp):
        """Test that user messages still have bubble styling."""
        message = ChatMessage(
            content="This is a user message that should keep bubble styling.",
            role=MessageRole.USER,
            status=MessageStatus.SENT,
        )

        bubble = MessageBubble(message)
        bubble.apply_theme("light")

        # Check that user messages still have bubble styling (left-aligned with border)
        style = bubble.styleSheet()
        # Should have border for distinction (new styling)
        assert "border:" in style or "border " in style  # Border for distinction
        assert "border-radius:" in style  # Should have border-radius
        assert "background-color" in style  # Should have background color
        # Should be left-aligned (no margin-left for right alignment)
        assert "margin-left" not in style or "margin-left: 0" in style

    def test_system_message_retains_existing_styling(self, qapp):
        """Test that system messages retain their existing styling."""
        message = ChatMessage(
            content="This is a system message.",
            role=MessageRole.SYSTEM,
            status=MessageStatus.SENT,
        )

        bubble = MessageBubble(message)
        bubble.apply_theme("light")

        # Check that system messages retain existing styling (updated border-radius)
        style = bubble.styleSheet()
        assert "#fff3cd" in style  # Yellow background
        assert "border-radius: 8px" in style  # Updated border-radius

    def test_content_display_unchanged(self, qapp):
        """Test that content display functionality is unchanged."""
        content = "Test message content for natural text flow."
        message = ChatMessage(
            content=content, role=MessageRole.ASSISTANT, status=MessageStatus.SENT
        )

        bubble = MessageBubble(message)

        # Content should be displayed correctly
        assert bubble.get_displayed_content() == content

        # Content updates should work
        new_content = "Updated content for testing."
        bubble.update_content(new_content)
        assert bubble.get_displayed_content() == new_content

    def test_natural_flow_alignment(self, qapp):
        """Test that assistant messages have proper alignment for natural flow."""
        message = ChatMessage(
            content="Test alignment for natural text flow.",
            role=MessageRole.ASSISTANT,
            status=MessageStatus.SENT,
        )

        bubble = MessageBubble(message)

        # Assistant messages should be left-aligned with full width
        layout = bubble.layout()
        # The alignment is handled at the layout level, so we verify the width constraint removal
        assert bubble.maximumWidth() == 16777215

        # Compare with user message which should have width constraint
        user_message = ChatMessage(
            content="User message", role=MessageRole.USER, status=MessageStatus.SENT
        )
        user_bubble = MessageBubble(user_message)
        assert user_bubble.maximumWidth() == 600
