"""Test MCP tool visualization integration into chat display."""

import pytest
from PyQt6.QtWidgets import QApplication
from src.my_coding_agent.core.main_window import MainWindow
from src.my_coding_agent.gui.chat_message_model import ChatMessageModel
from src.my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget
from src.my_coding_agent.gui.components.mcp_tool_visualization import MCPToolCallWidget


class TestMCPToolIntegration:
    """Test integration of MCP tool visualization into chat display."""

    @pytest.fixture
    def chat_widget(self, qtbot):
        """Create a chat widget for testing."""
        message_model = ChatMessageModel()
        widget = SimplifiedChatWidget(auto_adapt_theme=False)
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def main_window(self, qtbot):
        """Create a main window for testing."""
        window = MainWindow(directory_path=".")
        qtbot.addWidget(window)
        return window

    def test_chat_widget_has_tool_call_signals(self, chat_widget):
        """Test that chat widget has signals for tool call visualization."""
        # Should have signals for tool call lifecycle
        assert hasattr(chat_widget, "tool_call_started")
        assert hasattr(chat_widget, "tool_call_completed")
        assert hasattr(chat_widget, "tool_call_failed")

    def test_main_window_has_tool_call_signals(self, main_window):
        """Test that main window has signals for tool call events."""
        # Should have signals for tool call lifecycle
        assert hasattr(main_window, "tool_call_started_signal")
        assert hasattr(main_window, "tool_call_completed_signal")
        assert hasattr(main_window, "tool_call_failed_signal")

    def test_tool_call_started_creates_widget(self, chat_widget, qtbot):
        """Test that starting a tool call creates a visualization widget."""
        tool_call_data = {
            "id": "test-tool-call-1",
            "name": "resolve-library-id",
            "parameters": {"libraryName": "pydantic-ai"},
            "server": "context7",
            "status": "pending",
        }

        # Start tool call
        chat_widget.start_tool_call(tool_call_data)

        # Should create and display a tool call widget
        tool_widgets = chat_widget.findChildren(MCPToolCallWidget)
        assert len(tool_widgets) == 1

        tool_widget = tool_widgets[0]
        assert tool_widget.tool_call["id"] == "test-tool-call-1"
        assert tool_widget.tool_call["name"] == "resolve-library-id"
        assert tool_widget.isVisible()

    def test_tool_call_completed_updates_widget(self, chat_widget, qtbot):
        """Test that completing a tool call updates the visualization widget."""
        # Start tool call
        tool_call_data = {
            "id": "test-tool-call-1",
            "name": "resolve-library-id",
            "parameters": {"libraryName": "pydantic-ai"},
            "server": "context7",
            "status": "pending",
        }
        chat_widget.start_tool_call(tool_call_data)

        # Complete tool call
        result_data = {
            "id": "test-tool-call-1",
            "status": "success",
            "result": {"library_id": "/pydantic/pydantic-ai"},
            "execution_time": 1.25,
        }
        chat_widget.complete_tool_call(result_data)

        # Widget should be updated with result
        tool_widgets = chat_widget.findChildren(MCPToolCallWidget)
        tool_widget = tool_widgets[0]

        assert tool_widget.tool_call["status"] == "success"
        assert "result" in tool_widget.tool_call
        assert tool_widget.tool_call["execution_time"] == 1.25

    def test_tool_call_failed_updates_widget(self, chat_widget, qtbot):
        """Test that failing a tool call updates the visualization widget with error."""
        # Start tool call
        tool_call_data = {
            "id": "test-tool-call-1",
            "name": "resolve-library-id",
            "parameters": {},
            "server": "context7",
            "status": "pending",
        }
        chat_widget.start_tool_call(tool_call_data)

        # Fail tool call
        error_data = {
            "id": "test-tool-call-1",
            "status": "error",
            "error": "Invalid arguments: libraryName is required",
            "execution_time": 0.5,
        }
        chat_widget.fail_tool_call(error_data)

        # Widget should be updated with error
        tool_widgets = chat_widget.findChildren(MCPToolCallWidget)
        tool_widget = tool_widgets[0]

        assert tool_widget.tool_call["status"] == "error"
        assert "error" in tool_widget.tool_call
        assert tool_widget.tool_call["execution_time"] == 0.5

    def test_multiple_tool_calls_handled_correctly(self, chat_widget, qtbot):
        """Test that multiple concurrent tool calls are handled correctly."""
        # Start first tool call
        tool_call_1 = {
            "id": "tool-1",
            "name": "resolve-library-id",
            "parameters": {"libraryName": "pydantic-ai"},
            "server": "context7",
            "status": "pending",
        }
        chat_widget.start_tool_call(tool_call_1)

        # Start second tool call
        tool_call_2 = {
            "id": "tool-2",
            "name": "get-library-docs",
            "parameters": {"context7CompatibleLibraryID": "/pydantic/pydantic-ai"},
            "server": "context7",
            "status": "pending",
        }
        chat_widget.start_tool_call(tool_call_2)

        # Should have two tool widgets
        tool_widgets = chat_widget.findChildren(MCPToolCallWidget)
        assert len(tool_widgets) == 2

        # Complete first tool call
        chat_widget.complete_tool_call(
            {
                "id": "tool-1",
                "status": "success",
                "result": {"library_id": "/pydantic/pydantic-ai"},
            }
        )

        # First widget should be updated, second should still be pending
        tool_1_widget = next(w for w in tool_widgets if w.tool_call["id"] == "tool-1")
        tool_2_widget = next(w for w in tool_widgets if w.tool_call["id"] == "tool-2")

        assert tool_1_widget.tool_call["status"] == "success"
        assert tool_2_widget.tool_call["status"] == "pending"

    def test_signal_connections_main_window_to_chat(self, main_window, qtbot):
        """Test that main window signals are properly connected to chat widget."""
        # Main window should have tool call signals connected to chat widget
        chat_widget = main_window._chat_widget

        # Mock tool call data
        tool_call_data = {
            "id": "test-tool-call",
            "name": "resolve-library-id",
            "parameters": {"libraryName": "pydantic-ai"},
            "server": "context7",
            "status": "pending",
        }

        # Emit signal from main window
        main_window.tool_call_started_signal.emit(tool_call_data)

        # Process events to ensure signal is handled
        QApplication.processEvents()

        # Chat widget should have received and processed the signal
        tool_widgets = chat_widget.findChildren(MCPToolCallWidget)
        assert len(tool_widgets) == 1
