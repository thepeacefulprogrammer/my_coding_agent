"""
End-to-end tests for complete user workflow.

These tests verify the complete user journey: connect → send → receive → display
through the entire MCP client interface.
"""

from src.my_coding_agent.config.settings import get_settings, reset_settings
from src.my_coding_agent.core.mcp_client_coordinator import (
    MCPClientCoordinator,
    MCPCoordinatorConfig,
)
from src.my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def setup_method(self):
        """Setup for each test."""
        reset_settings()

    def test_settings_loading_and_mcp_configuration(self):
        """Test settings loading and MCP configuration workflow."""
        # Get default settings
        settings = get_settings()

        # Verify MCP settings are properly configured
        assert settings.mcp_server_url == "http://localhost:8080"
        assert settings.mcp_timeout == 30.0
        assert settings.mcp_enable_streaming is True

        # Verify MCP config generation
        mcp_config = settings.get_mcp_config()
        assert mcp_config["server_url"] == settings.mcp_server_url
        assert mcp_config["timeout"] == settings.mcp_timeout
        assert mcp_config["enable_streaming"] == settings.mcp_enable_streaming

    def test_mcp_coordinator_initialization_workflow(self):
        """Test MCP coordinator initialization from settings."""
        settings = get_settings()
        mcp_config = settings.get_mcp_config()

        # Create coordinator config
        coordinator_config = MCPCoordinatorConfig(
            server_url=mcp_config["server_url"],
            timeout=mcp_config["timeout"],
            enable_streaming=mcp_config["enable_streaming"],
            max_retries=mcp_config["max_retries"],
        )

        # Initialize coordinator
        coordinator = MCPClientCoordinator(coordinator_config)

        # Verify initialization
        assert coordinator.server_url == "http://localhost:8080"
        assert coordinator.timeout == 30.0
        assert coordinator.enable_streaming is True
        assert coordinator.is_connected is False

    def test_complete_user_journey_simulation(self, qtbot):
        """Test complete user journey from start to finish."""
        # Step 1: Initialize interface
        chat_widget = SimplifiedChatWidget()
        qtbot.addWidget(chat_widget)

        # Step 2: Show connection status
        chat_widget.add_system_message("Connecting to MCP server...")

        # Step 3: Simulate successful connection
        chat_widget.add_system_message("Connected to MCP server successfully")

        # Step 4: User sends message
        user_message = "Please analyze this code for me"
        user_msg_id = chat_widget.add_user_message(user_message)
        assert user_msg_id is not None

        # Step 5: Show thinking indicator
        chat_widget.show_ai_thinking(animated=True)

        # Step 6: Simulate streaming response
        _stream_id = chat_widget.start_streaming_response("test-stream")
        chat_widget.append_streaming_chunk("I'll analyze")
        chat_widget.append_streaming_chunk(" the code")
        chat_widget.append_streaming_chunk(" for you.")
        chat_widget.complete_streaming_response()

        # Step 7: Verify final state
        assert not chat_widget.is_streaming()

        # Step 8: Add final assistant message with metadata
        assistant_msg_id = chat_widget.add_assistant_message(
            "Analysis complete. The code looks good!"
        )
        assert assistant_msg_id is not None
