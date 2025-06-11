"""Unit tests for chat input improvements (Tasks 3.7 and 3.8)."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication
from src.my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def chat_widget(app):
    """Create SimplifiedChatWidget instance for testing."""
    widget = SimplifiedChatWidget()
    return widget


class TestChatInputImprovements:
    """Test suite for chat input improvements."""

    def test_enter_key_sends_message(self, chat_widget):
        """Test that pressing Enter sends the message."""
        # Set some text in the input
        chat_widget.input_text.setPlainText("Hello, AI!")

        # Track message_sent signal
        message_sent = False
        sent_text = ""

        def on_message_sent(text):
            nonlocal message_sent, sent_text
            message_sent = True
            sent_text = text

        chat_widget.message_sent.connect(on_message_sent)

        # Simulate Enter key press
        key_event = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier
        )
        QApplication.sendEvent(chat_widget.input_text, key_event)

        # Process events
        QApplication.processEvents()

        # Verify message was sent
        assert message_sent
        assert sent_text == "Hello, AI!"

        # Verify input was cleared
        assert chat_widget.input_text.toPlainText() == ""

    def test_shift_enter_creates_newline(self, chat_widget):
        """Test that Shift+Enter creates a newline instead of sending."""
        # Set some text in the input
        chat_widget.input_text.setPlainText("Line 1")

        # Track message_sent signal
        message_sent = False

        def on_message_sent(text):
            nonlocal message_sent
            message_sent = True

        chat_widget.message_sent.connect(on_message_sent)

        # Simulate Shift+Enter key press
        key_event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.ShiftModifier,
        )
        QApplication.sendEvent(chat_widget.input_text, key_event)

        # Process events
        QApplication.processEvents()

        # Verify message was NOT sent
        assert not message_sent

        # Verify newline was added (text should contain \n)
        text = chat_widget.input_text.toPlainText()
        assert "\n" in text or len(text.split("\n")) > 1

    def test_ctrl_enter_sends_message(self, chat_widget):
        """Test that Ctrl+Enter also sends the message (alternative)."""
        # Set some text in the input
        chat_widget.input_text.setPlainText("Test message")

        # Track message_sent signal
        message_sent = False
        sent_text = ""

        def on_message_sent(text):
            nonlocal message_sent, sent_text
            message_sent = True
            sent_text = text

        chat_widget.message_sent.connect(on_message_sent)

        # Simulate Ctrl+Enter key press
        key_event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.ControlModifier,
        )
        QApplication.sendEvent(chat_widget.input_text, key_event)

        # Process events
        QApplication.processEvents()

        # Verify message was sent
        assert message_sent
        assert sent_text == "Test message"

    def test_empty_message_not_sent_on_enter(self, chat_widget):
        """Test that empty messages are not sent when pressing Enter."""
        # Ensure input is empty
        chat_widget.input_text.clear()

        # Track message_sent signal
        message_sent = False

        def on_message_sent(text):
            nonlocal message_sent
            message_sent = True

        chat_widget.message_sent.connect(on_message_sent)

        # Simulate Enter key press on empty input
        key_event = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier
        )
        QApplication.sendEvent(chat_widget.input_text, key_event)

        # Process events
        QApplication.processEvents()

        # Verify message was NOT sent
        assert not message_sent

    def test_send_button_compact_size(self, chat_widget):
        """Test that send button has a compact, reasonable size."""
        send_button = chat_widget.send_button

        # Button should be reasonably sized (not too wide)
        assert send_button.width() <= 70  # Max 70px wide
        assert send_button.height() <= 40  # Max 40px tall

        # Button should have minimum useful size
        assert send_button.width() >= 40  # At least 40px wide
        assert send_button.height() >= 25  # At least 25px tall

    def test_input_text_takes_most_space(self, chat_widget):
        """Test that input text area takes up most of the available space."""
        input_text = chat_widget.input_text
        send_button = chat_widget.send_button

        # Input should be significantly wider than send button
        assert input_text.width() > send_button.width() * 2

        # Input should expand to fill available space
        # (exact ratio depends on layout, but input should dominate)
        total_width = input_text.width() + send_button.width()
        input_ratio = input_text.width() / total_width
        assert input_ratio >= 0.70  # Input takes at least 70% of space

    def test_send_button_text_and_styling(self, chat_widget):
        """Test that send button has appropriate text and styling."""
        send_button = chat_widget.send_button

        # Button should have "Send" text or an icon
        assert send_button.text() in ["Send", "→", "⏎"] or len(send_button.text()) > 0

        # Button should have some styling applied
        style_sheet = send_button.styleSheet()
        assert len(style_sheet) > 0  # Should have some styling

    def test_input_height_constraints(self, chat_widget):
        """Test that input text area has reasonable height constraints."""
        input_text = chat_widget.input_text

        # Should have a maximum height to prevent it from growing too large
        assert input_text.maximumHeight() > 0
        assert input_text.maximumHeight() <= 150  # Reasonable max height

        # Should allow for multiple lines but not unlimited growth
        assert input_text.maximumHeight() >= 60  # At least space for 2-3 lines
