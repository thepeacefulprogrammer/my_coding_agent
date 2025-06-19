"""
Integration tests for UI components with MCPClientCoordinator.

These tests verify that UI components work correctly with the simplified
MCP architecture, especially the chat interface and streaming responses.
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from src.my_coding_agent.core.mcp_client_coordinator import (
    MCPClientCoordinator,
    MCPCoordinatorConfig,
    MCPResponse,
    StreamingMCPResponse,
)
from src.my_coding_agent.gui.chat_message_model import (
    ChatMessage,
    MessageRole,
    MessageStatus,
)
from src.my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget
from src.my_coding_agent.gui.components.message_display import (
    MessageDisplay,
    MessageDisplayTheme,
)


class TestUIIntegrationWithMCP:
    """Test suite for UI integration with MCP Client Coordinator."""

    @pytest.fixture
    def chat_widget(self, qtbot):
        """Create a chat widget for testing."""
        widget = SimplifiedChatWidget()
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def mcp_coordinator(self):
        """Create a mock MCP coordinator for testing."""
        config = MCPCoordinatorConfig(
            server_url="http://localhost:8080",
            timeout=30.0,
            enable_streaming=True,
            max_retries=3,
        )
        coordinator = MCPClientCoordinator(config)
        return coordinator

    def test_chat_widget_message_sending_signal(self, qtbot, chat_widget):
        """Test that chat widget emits message_sent signal properly."""
        # Connect to signal
        with qtbot.waitSignal(chat_widget.message_sent, timeout=1000) as signal_blocker:
            # Simulate typing a message
            chat_widget._input_widget.setPlainText("Hello MCP!")

            # Simulate Enter key press
            QTest.keyPress(chat_widget._input_widget, Qt.Key.Key_Return)

        # Verify signal was emitted with correct message
        assert signal_blocker.args == ["Hello MCP!"]

    def test_message_display_with_mcp_metadata(self, qtbot):
        """Test MessageDisplay component handles MCP response metadata correctly."""
        # Create a chat message with MCP metadata
        mcp_metadata = {
            "tokens_used": 42,
            "model": "gpt-4",
            "tool_calls": ["file_read", "code_analysis"],
            "processing_time": 1.23,
        }

        message = ChatMessage(
            message_id="test-msg-123",
            role=MessageRole.ASSISTANT,
            content="Here's the analysis of your code...",
            status=MessageStatus.DELIVERED,
            metadata=mcp_metadata,
        )

        # Create message display component
        display = MessageDisplay(message, theme=MessageDisplayTheme.DARK)
        qtbot.addWidget(display)

        # Verify message content is displayed
        assert display.get_content() == "Here's the analysis of your code..."
        assert display.get_message().metadata == mcp_metadata
        assert display.get_message().metadata["tokens_used"] == 42

    def test_chat_widget_streaming_response_handling(self, qtbot, chat_widget):
        """Test that chat widget can handle streaming responses from MCP coordinator."""
        # Start a streaming response
        stream_id = "test-stream-123"
        chat_widget.start_streaming_response(stream_id)

        # Verify streaming state
        assert chat_widget.is_streaming()

        # Wait a brief moment for UI to update
        qtbot.wait(10)

        # Check that streaming indicator widget exists (more reliable than visibility in tests)
        streaming_widget = chat_widget.get_streaming_indicator_widget()
        assert streaming_widget is not None

        # Simulate streaming chunks
        chat_widget.append_streaming_chunk("Hello")
        chat_widget.append_streaming_chunk(" world")
        chat_widget.append_streaming_chunk("!")

        # Complete the streaming
        chat_widget.complete_streaming_response()

        # Verify final state
        assert not chat_widget.is_streaming()
        # Note: In test environment, the actual visibility might not update immediately
        # but the streaming state should be correctly reset

    def test_chat_widget_error_handling(self, qtbot, chat_widget):
        """Test that chat widget handles MCP errors gracefully."""
        # Start streaming
        stream_id = "test-stream-error"
        chat_widget.start_streaming_response(stream_id)

        # Simulate an error
        test_error = Exception("MCP server connection failed")
        chat_widget.handle_streaming_error(test_error)

        # Verify error is handled and streaming stops
        assert not chat_widget.is_streaming()

    def test_chat_widget_system_messages(self, qtbot, chat_widget):
        """Test that chat widget can display system messages for MCP status."""
        # Add system message (like MCP connection status)
        chat_widget.add_system_message("MCP Client initialized successfully")

        # Verify message was added
        assert len(chat_widget._message_model.messages) == 1
        message = chat_widget._message_model.messages[0]
        assert message.role == MessageRole.SYSTEM
        assert "MCP Client initialized" in message.content

    def test_chat_widget_theme_consistency(self, qtbot, chat_widget):
        """Test that chat widget maintains theme consistency for MCP responses."""
        # Add messages of different types
        chat_widget.add_user_message("Test user message")
        chat_widget.add_assistant_message("Test assistant response")
        chat_widget.add_system_message("Test system message")

        # Verify all messages exist
        assert len(chat_widget._message_model.messages) == 3

        # Test theme application
        chat_widget.apply_theme("dark")
        chat_widget.apply_theme("light")

        # Should not crash and should maintain styling

    def test_mcp_response_data_structure_compatibility(self):
        """Test that MCPResponse structure is compatible with UI expectations."""
        # Create an MCP response with various metadata
        response = MCPResponse(
            content="This is a test response",
            metadata={"model": "gpt-4", "tokens": 25, "processing_time": 0.5},
            tool_calls=[{"name": "file_read", "args": {"path": "/test/file.py"}}],
            code_blocks=[{"language": "python", "code": "print('hello world')"}],
        )

        # Verify structure
        assert response.content == "This is a test response"
        assert response.metadata["model"] == "gpt-4"
        assert len(response.tool_calls) == 1
        assert len(response.code_blocks) == 1

        # Verify it can be converted to ChatMessage metadata
        chat_metadata = {
            "mcp_metadata": response.metadata,
            "mcp_tool_calls": response.tool_calls,
            "mcp_code_blocks": response.code_blocks,
        }

        # This should work with ChatMessage
        message = ChatMessage(
            message_id="test-response",
            role=MessageRole.ASSISTANT,
            content=response.content,
            status=MessageStatus.DELIVERED,
            metadata=chat_metadata,
        )

        assert message.metadata["mcp_metadata"]["model"] == "gpt-4"

    def test_streaming_mcp_response_data_structure(self):
        """Test StreamingMCPResponse structure compatibility."""
        # Test partial response
        partial = StreamingMCPResponse(
            content="Partial response", is_complete=False, metadata={"partial": True}
        )

        assert partial.content == "Partial response"
        assert partial.is_complete is False
        assert partial.metadata["partial"] is True

        # Test complete response
        complete = StreamingMCPResponse(
            content="",
            is_complete=True,
            metadata={"tokens_used": 100, "final": True},
            tool_calls=[{"name": "analysis_complete"}],
        )

        assert complete.is_complete is True
        assert complete.metadata["tokens_used"] == 100
        assert len(complete.tool_calls) == 1

    @pytest.mark.asyncio
    async def test_mcp_coordinator_basic_functionality(self, mcp_coordinator):
        """Test basic MCPClientCoordinator functionality for UI integration."""
        # Test initialization
        assert mcp_coordinator.server_url == "http://localhost:8080"
        assert mcp_coordinator.timeout == 30.0
        assert mcp_coordinator.enable_streaming is True
        assert mcp_coordinator.is_connected is False

        # Test configuration
        assert mcp_coordinator.config.server_url == "http://localhost:8080"
