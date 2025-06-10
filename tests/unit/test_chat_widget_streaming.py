"""
Unit tests for chat widget streaming state management.

Tests streaming functionality including:
- Stream state tracking and visual indicators
- Real-time message updates during streaming
- Stream interruption capabilities
- Error handling during streaming
- Progress indicators and user feedback
"""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from my_coding_agent.core.streaming.stream_handler import StreamState
from my_coding_agent.gui.chat_message_model import (
    MessageRole,
    MessageStatus,
)
from my_coding_agent.gui.chat_widget import ChatWidget


@pytest.fixture
def app():
    """Create QApplication for tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def chat_widget(app):
    """Create ChatWidget instance for testing."""
    widget = ChatWidget()
    # Enable test mode for reliable indicator visibility testing
    widget.display_area.set_test_mode(True)
    return widget


class TestChatWidgetStreamingState:
    """Test streaming state management in ChatWidget."""

    def test_initial_streaming_state(self, chat_widget):
        """Test chat widget starts with no active streaming state."""
        assert not chat_widget.is_streaming()
        assert chat_widget.get_current_stream_id() is None
        assert chat_widget.get_streaming_state() == StreamState.IDLE

    def test_start_streaming_response(self, chat_widget):
        """Test starting a streaming response creates proper state."""
        # Add a user message first
        user_msg_id = chat_widget.add_user_message("Test question")

        # Start streaming response
        stream_id = "test-stream-123"
        assistant_msg_id = chat_widget.start_streaming_response(stream_id)

        # Verify streaming state
        assert chat_widget.is_streaming()
        assert chat_widget.get_current_stream_id() == stream_id
        assert chat_widget.get_streaming_state() == StreamState.STREAMING
        assert chat_widget.get_streaming_message_id() == assistant_msg_id

        # Verify message was created with streaming status
        assert chat_widget.message_model.get_message_by_id(assistant_msg_id) is not None
        message = chat_widget.message_model.get_message_by_id(assistant_msg_id)
        assert message.role == MessageRole.ASSISTANT
        assert message.content == ""  # Empty initially
        assert message.status == MessageStatus.SENDING  # Streaming status

    def test_update_streaming_content(self, chat_widget):
        """Test updating content during streaming."""
        # Start streaming
        stream_id = "test-stream-123"
        msg_id = chat_widget.start_streaming_response(stream_id)

        # Add cumulative chunks (each chunk contains the full content so far)
        chat_widget.append_streaming_chunk("Hello ")
        chat_widget.append_streaming_chunk("Hello world!")

        # Verify content shows the latest cumulative chunk
        message = chat_widget.message_model.get_message_by_id(msg_id)
        assert message.content == "Hello world!"
        assert message.status == MessageStatus.SENDING  # Still streaming

    def test_complete_streaming_response(self, chat_widget):
        """Test completing a streaming response."""
        # Start streaming
        stream_id = "test-stream-123"
        msg_id = chat_widget.start_streaming_response(stream_id)

        # Add content
        chat_widget.append_streaming_chunk("Complete response")

        # Complete streaming
        chat_widget.complete_streaming_response()

        # Verify final state
        assert not chat_widget.is_streaming()
        assert chat_widget.get_current_stream_id() is None
        assert chat_widget.get_streaming_state() == StreamState.COMPLETED

        # Verify message status
        message = chat_widget.message_model.get_message_by_id(msg_id)
        assert message.status == MessageStatus.DELIVERED
        assert message.content == "Complete response"

    def test_interrupt_streaming_response(self, chat_widget):
        """Test interrupting a streaming response."""
        # Start streaming
        stream_id = "test-stream-123"
        msg_id = chat_widget.start_streaming_response(stream_id)

        # Add some content
        chat_widget.append_streaming_chunk("Partial content")

        # Interrupt streaming
        chat_widget.interrupt_streaming_response()

        # Verify interrupted state
        assert not chat_widget.is_streaming()
        assert chat_widget.get_streaming_state() == StreamState.INTERRUPTED

        # Verify message shows interrupted status
        message = chat_widget.message_model.get_message_by_id(msg_id)
        assert message.status == MessageStatus.ERROR
        assert "interrupted" in message.error_message.lower()

    def test_streaming_error_handling(self, chat_widget):
        """Test error handling during streaming."""
        # Start streaming
        stream_id = "test-stream-123"
        msg_id = chat_widget.start_streaming_response(stream_id)

        # Add some content
        chat_widget.append_streaming_chunk("Partial content")

        # Simulate error
        error = Exception("Network timeout")
        chat_widget.handle_streaming_error(error)

        # Verify error state
        assert not chat_widget.is_streaming()
        assert chat_widget.get_streaming_state() == StreamState.ERROR

        # Verify message shows error
        message = chat_widget.message_model.get_message_by_id(msg_id)
        assert message.status == MessageStatus.ERROR
        assert "Network timeout" in message.error_message

    def test_streaming_progress_indicator(self, chat_widget):
        """Test streaming progress visual indicator."""
        # Not streaming initially
        assert not chat_widget.is_streaming_indicator_visible()

        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Should show streaming indicator
        assert chat_widget.is_streaming_indicator_visible()
        assert chat_widget.get_streaming_indicator_text() == "AI is responding..."

        # Complete streaming
        chat_widget.complete_streaming_response()

        # Indicator should be hidden
        assert not chat_widget.is_streaming_indicator_visible()

    def test_prevent_multiple_concurrent_streams(self, chat_widget):
        """Test prevention of multiple concurrent streaming responses."""
        # Start first stream
        stream_id1 = "test-stream-1"
        msg_id1 = chat_widget.start_streaming_response(stream_id1)

        # Try to start second stream - should raise error
        with pytest.raises(RuntimeError, match="Stream already active"):
            chat_widget.start_streaming_response("test-stream-2")

        # Verify first stream is still active
        assert chat_widget.get_current_stream_id() == stream_id1

    def test_streaming_with_retry_indicator(self, chat_widget):
        """Test streaming indicator shows retry information."""
        # Start streaming with retry count
        stream_id = "test-stream-retry"
        msg_id = chat_widget.start_streaming_response(stream_id, retry_count=1)

        # Should show retry information in indicator
        assert chat_widget.is_streaming_indicator_visible()
        indicator_text = chat_widget.get_streaming_indicator_text()
        assert "retry" in indicator_text.lower() or "attempt" in indicator_text.lower()

    def test_stream_interruption_button(self, chat_widget):
        """Test stream interruption button functionality."""
        # Not streaming initially - no interrupt button
        assert not chat_widget.is_interrupt_button_visible()

        # Start streaming
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Interrupt button should appear
        assert chat_widget.is_interrupt_button_visible()

        # Click interrupt button
        chat_widget.click_interrupt_button()

        # Should interrupt the stream
        assert not chat_widget.is_streaming()
        assert chat_widget.get_streaming_state() == StreamState.INTERRUPTED

    def test_streaming_state_persistence(self, chat_widget):
        """Test streaming state is properly maintained across operations."""
        # Start streaming
        stream_id = "test-stream-123"
        msg_id = chat_widget.start_streaming_response(stream_id)

        # Add user message while streaming (should be allowed)
        user_msg_id = chat_widget.add_user_message("Another question")

        # Streaming state should be preserved
        assert chat_widget.is_streaming()
        assert chat_widget.get_current_stream_id() == stream_id

        # Add more chunks
        chat_widget.append_streaming_chunk("More content")

        # Complete streaming
        chat_widget.complete_streaming_response()

        # State should be cleared
        assert not chat_widget.is_streaming()

    def test_clear_conversation_during_streaming(self, chat_widget):
        """Test clearing conversation while streaming."""
        # Start streaming
        stream_id = "test-stream-123"
        msg_id = chat_widget.start_streaming_response(stream_id)
        chat_widget.append_streaming_chunk("Some content")

        # Clear conversation
        chat_widget.clear_conversation()

        # Streaming state should be reset
        assert not chat_widget.is_streaming()
        assert chat_widget.get_streaming_state() == StreamState.IDLE
        assert chat_widget.get_current_stream_id() is None


class TestChatWidgetStreamingIntegration:
    """Test integration between ChatWidget and StreamHandler."""

    @pytest.mark.asyncio
    async def test_ai_agent_streaming_integration(self, chat_widget):
        """Test integration with AI Agent streaming."""

        # Test direct streaming integration without needing AI agent
        # Track streaming calls
        chunks_received = []

        # Start streaming
        stream_id = "test-integration-stream"
        msg_id = chat_widget.start_streaming_response(stream_id)

        # Simulate receiving cumulative chunks from AI agent
        chat_widget.append_streaming_chunk("Hello ")
        chunks_received.append("Hello ")

        chat_widget.append_streaming_chunk("Hello world!")
        chunks_received.append("Hello world!")

        # Complete streaming
        chat_widget.complete_streaming_response()

        # Verify streaming completed successfully
        assert not chat_widget.is_streaming()
        assert len(chunks_received) == 2

        # Verify final message content
        message = chat_widget.message_model.get_message_by_id(msg_id)
        assert message.content == "Hello world!"
        assert message.status == MessageStatus.DELIVERED

    def test_theme_compatibility_with_streaming(self, chat_widget):
        """Test streaming indicators work with different themes."""
        # Test light theme
        chat_widget.apply_theme("light")
        stream_id = "test-stream-theme"
        chat_widget.start_streaming_response(stream_id)

        assert chat_widget.is_streaming_indicator_visible()

        # Switch to dark theme while streaming
        chat_widget.apply_theme("dark")

        # Streaming should still work and be visible
        assert chat_widget.is_streaming_indicator_visible()
        assert chat_widget.is_streaming()

        # Complete streaming
        chat_widget.complete_streaming_response()

    def test_scroll_behavior_during_streaming(self, chat_widget):
        """Test scroll behavior while receiving streaming content."""
        # Add some messages to enable scrolling
        for i in range(10):
            chat_widget.add_user_message(f"Message {i}")

        # Scroll to top
        chat_widget.scroll_to_top()
        assert not chat_widget.is_scrolled_to_bottom()

        # Start streaming response
        stream_id = "test-stream-scroll"
        chat_widget.start_streaming_response(stream_id)

        # Add streaming content
        for i in range(5):
            chat_widget.append_streaming_chunk(f"Chunk {i} ")

        # Should auto-scroll to show new content
        assert chat_widget.is_scrolled_to_bottom()

        # Complete streaming
        chat_widget.complete_streaming_response()
        assert chat_widget.is_scrolled_to_bottom()
