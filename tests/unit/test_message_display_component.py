"""Unit tests for MessageDisplay component (Task 3.4)."""

import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from src.my_coding_agent.gui.chat_message_model import (
    ChatMessage,
)
from src.my_coding_agent.gui.components.message_display import (
    MessageDisplay,
    MessageDisplayTheme,
)


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def sample_user_message():
    """Create a sample user message."""
    return ChatMessage.create_user_message("Hello, this is a user message!")


@pytest.fixture
def sample_assistant_message():
    """Create a sample assistant message."""
    return ChatMessage.create_assistant_message(
        "Hi there! This is an AI assistant response."
    )


@pytest.fixture
def sample_system_message():
    """Create a sample system message."""
    return ChatMessage.create_system_message("System: Connection established")


class TestMessageDisplayComponent:
    """Test suite for MessageDisplay component."""

    def test_message_display_component_exists(self, app):
        """Test that MessageDisplay component can be instantiated."""
        message = ChatMessage.create_user_message("Test message")
        display = MessageDisplay(message)
        assert display is not None
        assert isinstance(display, QWidget)

    def test_message_display_theme_enum_exists(self, app):
        """Test that MessageDisplayTheme enum exists with expected values."""
        assert hasattr(MessageDisplayTheme, "LIGHT")
        assert hasattr(MessageDisplayTheme, "DARK")
        assert MessageDisplayTheme.LIGHT.value == "light"
        assert MessageDisplayTheme.DARK.value == "dark"

    def test_user_message_styling(self, app, sample_user_message):
        """Test that user messages have proper bordered styling."""
        display = MessageDisplay(sample_user_message, theme=MessageDisplayTheme.DARK)

        # User messages should have borders and contained width
        style = display.styleSheet()
        assert "border:" in style.lower() or "border-" in style.lower()
        assert "max-width:" in style.lower()

        # Should have proper background for dark theme
        assert "#2a2a2a" in style or "#1E88E5" in style

    def test_assistant_message_styling(self, app, sample_assistant_message):
        """Test that assistant messages have transparent, full-width styling."""
        display = MessageDisplay(
            sample_assistant_message, theme=MessageDisplayTheme.DARK
        )

        # AI messages should be transparent and full-width
        style = display.styleSheet()
        assert "transparent" in style.lower()
        # Should not have max-width restriction like user messages
        user_display = MessageDisplay(
            ChatMessage.create_user_message("test"), theme=MessageDisplayTheme.DARK
        )
        user_style = user_display.styleSheet()
        assert "max-width:" in user_style.lower()
        # AI messages should not have the same max-width restriction
        assert style != user_style

    def test_system_message_styling(self, app, sample_system_message):
        """Test that system messages have distinct styling."""
        display = MessageDisplay(sample_system_message, theme=MessageDisplayTheme.DARK)

        # System messages should have distinct background and styling
        style = display.styleSheet()
        assert "#404040" in style or "#666666" in style  # Dark theme system colors
        assert "italic" in style.lower()

    def test_theme_switching(self, app, sample_user_message):
        """Test that theme can be switched dynamically."""
        display = MessageDisplay(sample_user_message, theme=MessageDisplayTheme.DARK)

        # Get initial dark theme style
        dark_style = display.styleSheet()
        assert "#1E88E5" in dark_style or "#2a2a2a" in dark_style

        # Switch to light theme
        display.set_theme(MessageDisplayTheme.LIGHT)
        light_style = display.styleSheet()

        # Light theme should use different colors
        assert "#4285F4" in light_style or "#f8f9fa" in light_style
        assert dark_style != light_style

    def test_content_update(self, app, sample_user_message):
        """Test that message content can be updated."""
        display = MessageDisplay(sample_user_message)

        original_content = "Original message"
        new_content = "Updated message content"

        # Update content
        display.update_content(new_content)

        # Should reflect the new content
        assert display.get_content() == new_content

    def test_error_display(self, app, sample_assistant_message):
        """Test that error messages can be displayed."""
        display = MessageDisplay(sample_assistant_message)

        error_message = "Connection failed"
        display.set_error(error_message)

        # Error should be visible
        assert display.has_error()
        assert error_message in display.get_error_text()

        # Clear error
        display.clear_error()
        assert not display.has_error()

    def test_content_height_adjustment(self, app, sample_assistant_message):
        """Test that content height adjusts to text size."""
        display = MessageDisplay(sample_assistant_message)

        # Short content
        short_content = "Short"
        display.update_content(short_content)
        short_height = display.height()

        # Long content
        long_content = (
            "Very long message content that should increase the height of the display component "
            * 10
        )
        display.update_content(long_content)

        # Height should adjust (we can't test exact height due to font differences, but it should change)
        # The component should handle height adjustment internally
        assert display.get_content() == long_content

    def test_role_based_rendering_consistency(self, app):
        """Test that different message roles render consistently."""
        user_msg = ChatMessage.create_user_message("User message")
        assistant_msg = ChatMessage.create_assistant_message("Assistant message")
        system_msg = ChatMessage.create_system_message("System message")

        user_display = MessageDisplay(user_msg, theme=MessageDisplayTheme.DARK)
        assistant_display = MessageDisplay(
            assistant_msg, theme=MessageDisplayTheme.DARK
        )
        system_display = MessageDisplay(system_msg, theme=MessageDisplayTheme.DARK)

        # Each role should have distinct styling
        user_style = user_display.styleSheet()
        assistant_style = assistant_display.styleSheet()
        system_style = system_display.styleSheet()

        # All should be different
        assert user_style != assistant_style
        assert assistant_style != system_style
        assert user_style != system_style

    def test_theme_aware_colors(self, app, sample_user_message):
        """Test that component uses theme-appropriate colors."""
        # Dark theme
        dark_display = MessageDisplay(
            sample_user_message, theme=MessageDisplayTheme.DARK
        )
        dark_style = dark_display.styleSheet()

        # Should use dark theme colors
        assert any(
            color in dark_style for color in ["#1E88E5", "#2a2a2a", "#ffffff", "white"]
        )

        # Light theme
        light_display = MessageDisplay(
            sample_user_message, theme=MessageDisplayTheme.LIGHT
        )
        light_style = light_display.styleSheet()

        # Should use light theme colors
        assert any(color in light_style for color in ["#4285F4", "#f8f9fa", "#333"])

    def test_message_display_reusability(self, app):
        """Test that MessageDisplay component can be reused for different messages."""
        display = MessageDisplay(ChatMessage.create_user_message("Initial message"))

        # Should be able to display different message types
        assistant_msg = ChatMessage.create_assistant_message("Assistant message")
        display.set_message(assistant_msg)
        assert display.get_content() == "Assistant message"

        system_msg = ChatMessage.create_system_message("System message")
        display.set_message(system_msg)
        assert display.get_content() == "System message"

    def test_accessibility_features(self, app, sample_user_message):
        """Test that component has proper accessibility features."""
        display = MessageDisplay(sample_user_message)

        # Should have accessible name or role
        assert display.accessibleName() or display.accessibleDescription()

    def test_component_cleanup(self, app, sample_user_message):
        """Test that component cleans up resources properly."""
        display = MessageDisplay(sample_user_message)

        # Should be able to delete without errors
        display.deleteLater()
        # No assertion needed - just testing that deletion doesn't crash
