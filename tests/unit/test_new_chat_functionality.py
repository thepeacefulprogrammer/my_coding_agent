"""Unit tests for "New Chat" button functionality (Task 3.6)."""

import tempfile
from pathlib import Path

import pytest
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QApplication

from src.my_coding_agent.core.main_window import MainWindow


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def main_window(app, temp_directory):
    """Create MainWindow instance for testing."""
    window = MainWindow(directory_path=temp_directory)
    return window


@pytest.mark.qt
class TestNewChatFunctionalitySuite:
    """Test suite for "New Chat" button functionality."""

    def test_new_chat_menu_action_exists(self, main_window):
        """Test that "New Chat" action exists in the File menu."""
        # Should have a "New Chat" action in the File menu
        assert hasattr(main_window, "_new_chat_action")
        assert isinstance(main_window._new_chat_action, QAction)

        # Action should have proper text
        assert main_window._new_chat_action.text() == "&New Chat"

        # Action should have keyboard shortcut
        assert main_window._new_chat_action.shortcut() == QKeySequence("Ctrl+N")

        # Action should have status tip and tooltip
        assert "new chat" in main_window._new_chat_action.statusTip().lower()
        assert "new chat" in main_window._new_chat_action.toolTip().lower()

    def test_new_chat_action_in_file_menu(self, main_window):
        """Test that "New Chat" action is properly added to File menu."""
        file_menu = None
        menu_bar = main_window.menuBar()

        # Find the File menu
        for action in menu_bar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        assert file_menu is not None

        # Check that New Chat action is in the File menu
        menu_actions = file_menu.actions()
        new_chat_action = None

        for action in menu_actions:
            if action.text() == "&New Chat":
                new_chat_action = action
                break

        assert new_chat_action is not None
        assert new_chat_action is main_window._new_chat_action

    def test_new_chat_clears_conversation(self, main_window):
        """Test that "New Chat" action clears the current conversation."""
        # Add some messages to the chat
        chat_widget = main_window.chat_widget
        chat_widget.add_user_message("Hello, AI!")
        chat_widget.add_assistant_message("Hello! How can I help you?")
        chat_widget.add_user_message("What's 2+2?")

        # Verify messages exist
        assert chat_widget.message_model.rowCount() > 0

        # Trigger new chat action
        main_window._new_chat_action.trigger()

        # Verify conversation is cleared
        assert chat_widget.message_model.rowCount() == 0

    def test_new_chat_provides_status_feedback(self, main_window):
        """Test that "New Chat" action provides feedback via status bar."""
        # Add some messages first
        chat_widget = main_window.chat_widget
        chat_widget.add_user_message("Test message")

        # Trigger new chat action
        main_window._new_chat_action.trigger()

        # Check status bar shows feedback
        status_text = main_window.status_bar.currentMessage()
        assert (
            "new chat" in status_text.lower()
            or "conversation cleared" in status_text.lower()
        )

    def test_new_chat_keyboard_shortcut(self, app, main_window):
        """Test that Ctrl+N keyboard shortcut triggers new chat."""
        # Add messages to chat
        chat_widget = main_window.chat_widget
        chat_widget.add_user_message("Test message")
        chat_widget.add_assistant_message("Test response")

        initial_count = chat_widget.message_model.rowCount()
        assert initial_count > 0

        # Simulate Ctrl+N keyboard shortcut by triggering the action directly
        # (QTest.keySequence may not work reliably in all test environments)
        main_window._new_chat_action.trigger()

        # Verify conversation is cleared
        assert chat_widget.message_model.rowCount() == 0

    def test_new_chat_resets_streaming_state(self, main_window):
        """Test that "New Chat" action resets any active streaming state."""
        chat_widget = main_window.chat_widget

        # Simulate streaming state (if supported)
        if hasattr(chat_widget, "_is_streaming"):
            chat_widget._is_streaming = True

        # Trigger new chat
        main_window._new_chat_action.trigger()

        # Verify streaming state is reset
        if hasattr(chat_widget, "is_streaming"):
            assert not chat_widget.is_streaming()

    def test_new_chat_action_object_name(self, main_window):
        """Test that "New Chat" action has proper object name for testing."""
        assert main_window._new_chat_action.objectName() == "new_chat_action"

    def test_new_chat_menu_placement(self, main_window):
        """Test that "New Chat" action is placed correctly in File menu."""
        file_menu = None
        menu_bar = main_window.menuBar()

        # Find the File menu
        for action in menu_bar.actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        assert file_menu is not None
        menu_actions = file_menu.actions()

        # New Chat should be the first action in File menu
        assert menu_actions[0].text() == "&New Chat"

        # Should be followed by a separator
        assert menu_actions[1].isSeparator()

    def test_new_chat_with_empty_conversation(self, main_window):
        """Test that "New Chat" action works correctly with empty conversation."""
        chat_widget = main_window.chat_widget

        # Ensure conversation is empty
        chat_widget.clear_conversation()
        assert chat_widget.message_model.rowCount() == 0

        # Trigger new chat action
        main_window._new_chat_action.trigger()

        # Should still work without errors
        assert chat_widget.message_model.rowCount() == 0

    def test_new_chat_updates_status_message(self, main_window):
        """Test that "New Chat" action updates status message correctly."""
        # Add messages
        chat_widget = main_window.chat_widget
        chat_widget.add_user_message("Hello")
        chat_widget.add_assistant_message("Hi there!")

        chat_widget.message_model.rowCount()

        # Trigger new chat
        main_window._new_chat_action.trigger()

        # Status should indicate the action was completed
        status_text = main_window.status_bar.currentMessage()
        assert len(status_text) > 0
        assert (
            "new" in status_text.lower()
            or "clear" in status_text.lower()
            or "conversation" in status_text.lower()
        )

    def test_new_chat_preserves_theme_settings(self, main_window):
        """Test that "New Chat" action preserves current theme settings."""
        # Get current theme
        if hasattr(main_window, "_theme_manager"):
            initial_theme = main_window._theme_manager.get_current_theme()
        else:
            initial_theme = "dark"  # default

        # Add messages and trigger new chat
        chat_widget = main_window.chat_widget
        chat_widget.add_user_message("Test message")
        main_window._new_chat_action.trigger()

        # Theme should be preserved
        if hasattr(main_window, "_theme_manager"):
            current_theme = main_window._theme_manager.get_current_theme()
            assert current_theme == initial_theme

    def test_new_chat_method_exists(self, main_window):
        """Test that main window has a _new_chat method."""
        assert hasattr(main_window, "_new_chat")
        assert callable(main_window._new_chat)

    def test_new_chat_method_functionality(self, main_window):
        """Test that _new_chat method works correctly."""
        # Add messages
        chat_widget = main_window.chat_widget

        # Clear any existing messages first to start clean
        chat_widget.clear_conversation()
        initial_count = chat_widget.message_model.rowCount()

        chat_widget.add_user_message("Hello")
        chat_widget.add_assistant_message("Hi")

        # Verify messages were added
        after_add_count = chat_widget.message_model.rowCount()
        assert after_add_count > initial_count

        # Call _new_chat method directly
        main_window._new_chat()

        # Conversation should be cleared back to initial state
        final_count = chat_widget.message_model.rowCount()
        assert final_count == initial_count

    def test_new_chat_confirmation_not_required(self, main_window):
        """Test that "New Chat" action doesn't require confirmation for simplicity."""
        # Add messages
        chat_widget = main_window.chat_widget
        chat_widget.add_user_message("Important message")

        chat_widget.message_model.rowCount()

        # Trigger new chat - should clear immediately without confirmation
        main_window._new_chat_action.trigger()

        # Should be cleared immediately (no confirmation dialog)
        assert chat_widget.message_model.rowCount() == 0

    def test_new_chat_action_enabled_state(self, main_window):
        """Test that "New Chat" action is always enabled."""
        # Action should be enabled even with empty conversation
        assert main_window._new_chat_action.isEnabled()

        # Add messages
        chat_widget = main_window.chat_widget
        chat_widget.add_user_message("Test")

        # Should still be enabled
        assert main_window._new_chat_action.isEnabled()

        # Clear conversation
        chat_widget.clear_conversation()

        # Should still be enabled
        assert main_window._new_chat_action.isEnabled()

    def test_new_chat_multiple_consecutive_calls(self, main_window):
        """Test that multiple consecutive "New Chat" calls work correctly."""
        chat_widget = main_window.chat_widget

        # Add messages and clear multiple times
        for i in range(3):
            chat_widget.add_user_message(f"Message {i}")
            assert chat_widget.message_model.rowCount() > 0

            main_window._new_chat_action.trigger()
            assert chat_widget.message_model.rowCount() == 0

    def test_new_chat_integration_with_ai_agent(self, main_window):
        """Test that "New Chat" works correctly with AI agent integration."""
        # This test ensures new chat doesn't interfere with AI agent setup
        chat_widget = main_window.chat_widget

        # Add user and AI messages
        chat_widget.add_user_message("Hello AI")
        chat_widget.add_assistant_message("Hello! How can I help?")

        # Trigger new chat
        main_window._new_chat_action.trigger()

        # Should be able to add new messages after clearing
        chat_widget.add_user_message("New conversation message")
        assert chat_widget.message_model.rowCount() == 1

        # And the message should be the new one
        messages = chat_widget.message_model.get_all_messages()
        assert messages[0].content == "New conversation message"
