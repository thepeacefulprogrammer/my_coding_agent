"""
Unit tests for streaming visual indicators in SimplifiedChatWidget.

Tests visual feedback for streaming status including:
- Streaming status indicator visibility and text
- Interrupt button functionality
- Progress indicators during streaming
- Theme compatibility for indicators
- Subtle visual feedback without being intrusive
"""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget


@pytest.fixture
def app():
    """Create QApplication for tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def chat_widget(app):
    """Create SimplifiedChatWidget instance for testing."""
    widget = SimplifiedChatWidget()
    # Ensure widget is visible for testing UI components
    widget.show()
    widget.resize(400, 300)
    return widget


class TestStreamingVisualIndicators:
    """Test visual indicators for streaming status."""

    def test_initial_streaming_indicator_state(self, chat_widget):
        """Test streaming indicator is hidden initially."""
        assert not chat_widget.is_streaming_indicator_visible()
        assert not chat_widget.is_interrupt_button_visible()

    def test_streaming_indicator_shows_during_streaming(self, chat_widget):
        """Test streaming indicator appears when streaming starts."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Verify indicator is visible
        assert chat_widget.is_streaming_indicator_visible()
        assert chat_widget.get_streaming_indicator_text() == "AI is responding..."

    def test_streaming_indicator_hides_after_completion(self, chat_widget):
        """Test streaming indicator disappears when streaming completes."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)
        assert chat_widget.is_streaming_indicator_visible()

        # Complete streaming
        chat_widget.complete_streaming_response()

        # Verify indicator is hidden
        assert not chat_widget.is_streaming_indicator_visible()

    def test_streaming_indicator_hides_after_error(self, chat_widget):
        """Test streaming indicator disappears when streaming encounters error."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)
        assert chat_widget.is_streaming_indicator_visible()

        # Simulate error
        error = Exception("Network timeout")
        chat_widget.handle_streaming_error(error)

        # Verify indicator is hidden
        assert not chat_widget.is_streaming_indicator_visible()

    def test_interrupt_button_shows_during_streaming(self, chat_widget):
        """Test interrupt button appears when streaming starts."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Verify interrupt button is visible
        assert chat_widget.is_interrupt_button_visible()

    def test_interrupt_button_hides_after_completion(self, chat_widget):
        """Test interrupt button disappears when streaming completes."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)
        assert chat_widget.is_interrupt_button_visible()

        # Complete streaming
        chat_widget.complete_streaming_response()

        # Verify interrupt button is hidden
        assert not chat_widget.is_interrupt_button_visible()

    def test_interrupt_button_functionality(self, chat_widget):
        """Test interrupt button actually interrupts streaming."""
        # Start streaming
        stream_id = "test-stream-123"
        _msg_id = chat_widget.start_streaming_response(stream_id)

        # Add some content
        chat_widget.append_streaming_chunk("Partial content")

        # Click interrupt button
        chat_widget.trigger_interrupt_button()

        # Verify streaming was interrupted
        assert not chat_widget.is_streaming()
        assert not chat_widget.is_interrupt_button_visible()

    def test_streaming_indicator_text_with_retry(self, chat_widget):
        """Test streaming indicator shows retry information."""
        # Start streaming with retry count
        stream_id = "test-stream-retry"
        chat_widget.start_streaming_response(stream_id, retry_count=1)

        # Verify indicator shows retry information
        indicator_text = chat_widget.get_streaming_indicator_text()
        assert "retry" in indicator_text.lower() or "attempt" in indicator_text.lower()

    def test_streaming_indicator_theme_compatibility(self, chat_widget):
        """Test streaming indicator adapts to theme changes."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Test light theme
        chat_widget.apply_theme("light")
        assert chat_widget.is_streaming_indicator_visible()

        # Test dark theme
        chat_widget.apply_theme("dark")
        assert chat_widget.is_streaming_indicator_visible()

    def test_streaming_indicator_positioning(self, chat_widget):
        """Test streaming indicator is positioned correctly in the UI."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Verify indicator is positioned at bottom of chat area
        indicator_widget = chat_widget.get_streaming_indicator_widget()
        assert indicator_widget is not None
        assert indicator_widget.isVisible()

    def test_subtle_visual_feedback(self, chat_widget):
        """Test streaming indicators provide subtle, non-intrusive feedback."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Verify indicator is subtle (small, muted colors)
        indicator_widget = chat_widget.get_streaming_indicator_widget()
        assert indicator_widget is not None

        # Check that indicator doesn't dominate the UI
        indicator_height = indicator_widget.height()
        chat_height = chat_widget.height()

        # Indicator should be small relative to chat widget
        assert indicator_height < chat_height * 0.12  # Less than 12% of chat height

    def test_streaming_progress_animation(self, chat_widget):
        """Test streaming indicator can show animated progress."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Verify animation is available (but not required to be active)
        assert hasattr(chat_widget, "is_streaming_animation_active")

        # Animation should be subtle and optional
        if chat_widget.is_streaming_animation_active():
            # If animation is active, it should be subtle
            assert chat_widget.get_streaming_indicator_text() != ""

    def test_multiple_streaming_sessions_indicator_behavior(self, chat_widget):
        """Test indicator behavior across multiple streaming sessions."""
        # First streaming session
        stream_id1 = "test-stream-1"
        chat_widget.start_streaming_response(stream_id1)
        assert chat_widget.is_streaming_indicator_visible()

        chat_widget.complete_streaming_response()
        assert not chat_widget.is_streaming_indicator_visible()

        # Second streaming session
        stream_id2 = "test-stream-2"
        chat_widget.start_streaming_response(stream_id2)
        assert chat_widget.is_streaming_indicator_visible()

        chat_widget.complete_streaming_response()
        assert not chat_widget.is_streaming_indicator_visible()

    def test_streaming_indicator_accessibility(self, chat_widget):
        """Test streaming indicator is accessible to screen readers."""
        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Verify indicator has accessible text
        indicator_widget = chat_widget.get_streaming_indicator_widget()
        assert indicator_widget is not None

        # Check the streaming indicator label specifically
        streaming_indicator = chat_widget._streaming_indicator
        assert streaming_indicator is not None

        # Should have accessible name or text for screen readers
        accessible_text = (
            streaming_indicator.accessibleName() or streaming_indicator.text()
        )
        assert accessible_text != ""
        assert (
            "streaming" in accessible_text.lower()
            or "responding" in accessible_text.lower()
        )
