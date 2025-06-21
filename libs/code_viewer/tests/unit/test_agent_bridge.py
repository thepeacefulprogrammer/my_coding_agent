"""
Tests for Agent Bridge Implementation (Task 2.0)

This module tests the agent bridge functionality including:
- Agent architecture library integration
- Query processing and forwarding
- Connection management and initialization
- Error handling for unavailable agent architecture
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from code_viewer.core.agent_integration import (
    AgentBridge,
    AgentIntegrationError,
)


class TestAgentBridge:
    """Test the AgentBridge class functionality."""

    def test_agent_bridge_initialization(self):
        """Test that AgentBridge can be initialized with workspace path."""
        workspace_path = Path("/test/workspace")

        # Should be able to create bridge without agent architecture available
        bridge = AgentBridge(workspace_path)

        assert bridge.workspace_path == workspace_path
        assert bridge.is_connected is False
        assert bridge.agent_available is False

    def test_agent_bridge_with_callback(self):
        """Test AgentBridge initialization with file change callback."""
        workspace_path = Path("/test/workspace")
        callback = Mock()

        bridge = AgentBridge(workspace_path, file_change_callback=callback)

        assert bridge.workspace_path == workspace_path
        assert bridge.file_change_callback == callback

    @pytest.mark.asyncio
    async def test_agent_bridge_process_query_unavailable(self):
        """Test query processing when agent architecture is unavailable."""
        workspace_path = Path("/test/workspace")
        bridge = AgentBridge(workspace_path)

        # Should raise error when agent is not available
        with pytest.raises(AgentIntegrationError, match="Agent architecture not available"):
            await bridge.process_query("Test query")

    @pytest.mark.asyncio
    async def test_agent_bridge_process_query_success(self):
        """Test successful query processing with mock agent."""
        workspace_path = Path("/test/workspace")

        # Mock agent orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process.return_value = {
            "response": "Test response",
            "status": "success"
        }

        bridge = AgentBridge(workspace_path)
        bridge._orchestrator = mock_orchestrator
        bridge._agent_available = True

        result = await bridge.process_query("Test query")

        assert result["response"] == "Test response"
        assert result["status"] == "success"
        mock_orchestrator.process.assert_called_once_with("Test query")

    @pytest.mark.asyncio
    async def test_agent_bridge_connection_management(self):
        """Test agent bridge connection initialization and cleanup."""
        workspace_path = Path("/test/workspace")
        bridge = AgentBridge(workspace_path)

        # Test connection initialization
        with patch('code_viewer.core.agent_integration.agent_bridge.import_agent_orchestrator') as mock_import:
            mock_orchestrator_class = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_import.return_value = mock_orchestrator_class

            await bridge.initialize_connection()

            assert bridge.is_connected is True
            assert bridge.agent_available is True
            mock_orchestrator_class.assert_called_once_with(
                workspace_path=workspace_path,
                change_callback=bridge._handle_file_change
            )

        # Test connection cleanup
        await bridge.cleanup_connection()
        assert bridge.is_connected is False

    def test_agent_bridge_file_change_handling(self):
        """Test file change callback handling."""
        workspace_path = Path("/test/workspace")
        callback = Mock()
        bridge = AgentBridge(workspace_path, file_change_callback=callback)

        # Test file change notification
        bridge._handle_file_change("/test/file.py", "modified")

        callback.assert_called_once_with("/test/file.py", "modified")

    def test_agent_bridge_configuration(self):
        """Test agent bridge configuration management."""
        workspace_path = Path("/test/workspace")
        config = {
            "agent_timeout": 30,
            "retry_attempts": 3,
            "enable_streaming": True
        }

        bridge = AgentBridge(workspace_path, config=config)

        assert bridge.config["agent_timeout"] == 30
        assert bridge.config["retry_attempts"] == 3
        assert bridge.config["enable_streaming"] is True

    @pytest.mark.asyncio
    async def test_agent_bridge_error_handling(self):
        """Test comprehensive error handling scenarios."""
        workspace_path = Path("/test/workspace")
        bridge = AgentBridge(workspace_path)

        # Test import error handling
        with patch('code_viewer.core.agent_integration.agent_bridge.import_agent_orchestrator') as mock_import:
            mock_import.side_effect = ImportError("Agent architecture not found")

            with pytest.raises(AgentIntegrationError, match="Failed to import agent architecture"):
                await bridge.initialize_connection()

        # Test query processing error
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process.side_effect = Exception("Agent processing error")
        bridge._orchestrator = mock_orchestrator
        bridge._agent_available = True

        with pytest.raises(AgentIntegrationError, match="Agent query processing failed"):
            await bridge.process_query("Test query")

    @pytest.mark.asyncio
    async def test_agent_bridge_retry_logic(self):
        """Test retry logic for failed queries."""
        workspace_path = Path("/test/workspace")
        config = {"retry_attempts": 3}
        bridge = AgentBridge(workspace_path, config=config)

        # Mock orchestrator that fails twice then succeeds
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process.side_effect = [
            Exception("Temporary error"),
            Exception("Another error"),
            {"response": "Success after retry", "status": "success"}
        ]
        bridge._orchestrator = mock_orchestrator
        bridge._agent_available = True

        result = await bridge.process_query("Test query")

        assert result["response"] == "Success after retry"
        assert mock_orchestrator.process.call_count == 3


class TestAgentBridgeIntegration:
    """Test agent bridge integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self):
        """Test complete agent workflow from initialization to query processing."""
        workspace_path = Path("/test/workspace")
        file_callback = Mock()

        bridge = AgentBridge(workspace_path, file_change_callback=file_callback)

        # Mock successful agent architecture import and initialization
        with patch('code_viewer.core.agent_integration.agent_bridge.import_agent_orchestrator') as mock_import:
            mock_orchestrator_class = Mock()
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process.return_value = {
                "response": "Code analysis complete",
                "files_modified": ["/test/file.py"],
                "status": "success"
            }
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_import.return_value = mock_orchestrator_class

            # Initialize connection
            await bridge.initialize_connection()
            assert bridge.agent_available is True

            # Process query
            result = await bridge.process_query("Analyze this code")
            assert result["response"] == "Code analysis complete"

            # Simulate file change from agent
            bridge._handle_file_change("/test/file.py", "modified")
            file_callback.assert_called_once_with("/test/file.py", "modified")

            # Cleanup
            await bridge.cleanup_connection()
            assert bridge.is_connected is False


class TestAgentBridgeUtilities:
    """Test agent bridge utility methods."""

    def test_agent_bridge_status_properties(self):
        """Test status properties of agent bridge."""
        workspace_path = Path("/test/workspace")
        bridge = AgentBridge(workspace_path)

        # Initially not connected
        assert bridge.is_connected is False
        assert bridge.agent_available is False
        assert bridge.status == "disconnected"

        # Mock connected state
        bridge._is_connected = True
        bridge._agent_available = True
        assert bridge.status == "connected"

    def test_agent_bridge_configuration_validation(self):
        """Test configuration validation."""
        workspace_path = Path("/test/workspace")

        # Valid configuration
        valid_config = {
            "agent_timeout": 30,
            "retry_attempts": 3,
            "enable_streaming": True
        }
        bridge = AgentBridge(workspace_path, config=valid_config)
        assert bridge.config == valid_config

        # Invalid configuration should use defaults
        invalid_config = {
            "agent_timeout": -1,  # Invalid negative timeout
            "retry_attempts": "invalid",  # Invalid type
        }
        bridge = AgentBridge(workspace_path, config=invalid_config)
        # Should fall back to defaults for invalid values
        assert bridge.config["agent_timeout"] == 30  # Default
        assert bridge.config["retry_attempts"] == 3   # Default


if __name__ == "__main__":
    # Run tests to verify current implementation
    pytest.main([__file__, "-v"])
