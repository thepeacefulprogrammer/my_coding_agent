"""Unit tests for AI Agent MCP file server integration."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.mcp_file_server import (
    FileOperationError,
    MCPFileConfig,
    MCPFileServer,
)


class TestAIAgentMCPIntegration:
    """Test the AI Agent integration with MCP file server."""

    @pytest.fixture
    def ai_config(self):
        """Create AI Agent config for testing."""
        return AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test-key",
            deployment_name="test-deployment",
            api_version="2024-02-15-preview",
            max_tokens=1000,
            temperature=0.5,
            request_timeout=30,
            max_retries=3,
        )

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello, World!')")

            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            sub_file = subdir / "data.json"
            sub_file.write_text('{"key": "value"}')

            yield temp_dir

    @pytest.fixture
    def mcp_config(self, temp_workspace):
        """Create MCP file config for testing."""
        return MCPFileConfig(
            base_directory=temp_workspace,
            allowed_extensions=[".py", ".json", ".md", ".txt"],
            max_file_size=1024 * 1024,  # 1MB
            enable_write_operations=True,
            enable_delete_operations=False,
        )

    @pytest.fixture
    def ai_agent_with_mcp(self, ai_config, mcp_config):
        """Create AI Agent with MCP integration for testing."""
        with (
            patch("my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("my_coding_agent.core.ai_agent.Agent"),
        ):
            agent = AIAgent(ai_config)
            agent.mcp_file_server = MCPFileServer(mcp_config)
            return agent

    def test_ai_agent_mcp_initialization(self, ai_agent_with_mcp):
        """Test AI Agent initialization with MCP file server."""
        assert hasattr(ai_agent_with_mcp, "mcp_file_server")
        assert ai_agent_with_mcp.mcp_file_server is not None
        assert isinstance(ai_agent_with_mcp.mcp_file_server, MCPFileServer)

    @pytest.mark.asyncio
    async def test_ai_agent_file_operations_available(self, ai_agent_with_mcp):
        """Test that AI Agent has file operation methods available."""
        # Check if the MCP file operation methods are available
        assert hasattr(ai_agent_with_mcp, "read_file")
        assert hasattr(ai_agent_with_mcp, "write_file")
        assert hasattr(ai_agent_with_mcp, "list_directory")
        assert hasattr(ai_agent_with_mcp, "delete_file")
        assert hasattr(ai_agent_with_mcp, "create_directory")
        assert hasattr(ai_agent_with_mcp, "get_file_info")
        assert hasattr(ai_agent_with_mcp, "search_files")

    @pytest.mark.asyncio
    async def test_ai_agent_read_file_through_mcp(self, ai_agent_with_mcp):
        """Test AI Agent reading file through MCP."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[
                    Mock(type="text", text="def hello():\n    print('Hello, World!')")
                ]
            )
        )
        ai_agent_with_mcp.mcp_file_server.client_session = mock_session

        content = await ai_agent_with_mcp.read_file("test.py")

        assert content == "def hello():\n    print('Hello, World!')"

    @pytest.mark.asyncio
    async def test_ai_agent_write_file_through_mcp(self, ai_agent_with_mcp):
        """Test AI Agent writing file through MCP."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="File written successfully")]
            )
        )
        ai_agent_with_mcp.mcp_file_server.client_session = mock_session

        result = await ai_agent_with_mcp.write_file("new_file.py", "print('New file')")

        assert result is True

    @pytest.mark.asyncio
    async def test_ai_agent_list_directory_through_mcp(self, ai_agent_with_mcp):
        """Test AI Agent listing directory through MCP."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="test.py\nsubdir/\ndata.json")]
            )
        )
        ai_agent_with_mcp.mcp_file_server.client_session = mock_session

        files = await ai_agent_with_mcp.list_directory(".")

        assert "test.py" in files
        assert "subdir/" in files

    @pytest.mark.asyncio
    async def test_ai_agent_mcp_connection_management(self, ai_agent_with_mcp):
        """Test AI Agent MCP connection management."""
        # Mock the connect method
        with (
            patch.object(
                ai_agent_with_mcp.mcp_file_server, "connect", new_callable=AsyncMock
            ) as mock_connect,
            patch.object(
                ai_agent_with_mcp.mcp_file_server, "disconnect", new_callable=AsyncMock
            ) as mock_disconnect,
        ):
            mock_connect.return_value = True

            # Test connection
            result = await ai_agent_with_mcp.connect_mcp()
            assert result is True
            mock_connect.assert_called_once()

            # Test disconnection
            await ai_agent_with_mcp.disconnect_mcp()
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_agent_mcp_error_handling(self, ai_agent_with_mcp):
        """Test AI Agent MCP error handling."""
        # Mock MCP server not connected
        ai_agent_with_mcp.mcp_file_server.is_connected = False

        with pytest.raises(FileOperationError, match="Not connected to MCP server"):
            await ai_agent_with_mcp.read_file("test.py")

    @pytest.mark.asyncio
    async def test_ai_agent_file_context_for_chat(self, ai_agent_with_mcp):
        """Test AI Agent using file context for chat."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[
                    Mock(type="text", text="def hello():\n    print('Hello, World!')")
                ]
            )
        )
        ai_agent_with_mcp.mcp_file_server.client_session = mock_session

        # Mock AI agent response
        mock_result = Mock()
        mock_result.data = "This is a simple hello function that prints 'Hello, World!' to the console."
        mock_usage = Mock()
        mock_usage.total_tokens = 150
        mock_result.usage.return_value = mock_usage

        with patch.object(
            ai_agent_with_mcp._agent,
            "run",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await ai_agent_with_mcp.send_message_with_file_context(
                "Explain what this code does", "test.py"
            )

            assert response.success is True
            assert "hello function" in response.content

    @pytest.mark.asyncio
    async def test_ai_agent_workspace_aware_operations(
        self, ai_agent_with_mcp, temp_workspace
    ):
        """Test AI Agent workspace-aware file operations."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True

        # Test workspace boundaries
        with pytest.raises(FileOperationError, match="path traversal not allowed"):
            await ai_agent_with_mcp.read_file("../../../etc/passwd")

    @pytest.mark.asyncio
    async def test_ai_agent_bulk_file_operations(self, ai_agent_with_mcp):
        """Test AI Agent bulk file operations."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="test.py\nsubdir/data.json")]
            )
        )
        ai_agent_with_mcp.mcp_file_server.client_session = mock_session

        files = ["test.py", "subdir/data.json"]
        file_contents = await ai_agent_with_mcp.read_multiple_files(files)

        assert len(file_contents) == 2
        assert "test.py" in file_contents
        assert "subdir/data.json" in file_contents

    @pytest.mark.asyncio
    async def test_ai_agent_search_files_integration(self, ai_agent_with_mcp):
        """Test AI Agent search files integration."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(content=[Mock(type="text", text="test.py\nmodule.py")])
        )
        ai_agent_with_mcp.mcp_file_server.client_session = mock_session

        python_files = await ai_agent_with_mcp.search_files("*.py")

        assert "test.py" in python_files
        assert "module.py" in python_files

    @pytest.mark.asyncio
    async def test_ai_agent_enhanced_chat_with_file_ops(self, ai_agent_with_mcp):
        """Test AI Agent enhanced chat with file operation capabilities."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[
                    Mock(type="text", text="def hello():\n    print('Hello, World!')")
                ]
            )
        )
        ai_agent_with_mcp.mcp_file_server.client_session = mock_session

        # Mock AI agent to recognize file operation requests
        mock_result = Mock()
        mock_result.data = "I can see the hello function in test.py. It's a simple function that prints a greeting."
        mock_usage = Mock()
        mock_usage.total_tokens = 200
        mock_result.usage.return_value = mock_usage

        with patch.object(
            ai_agent_with_mcp._agent,
            "run",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = await ai_agent_with_mcp.send_enhanced_message(
                "Can you read test.py and tell me what it does?"
            )

            assert response.success is True
            assert "hello function" in response.content

    def test_ai_agent_mcp_health_status(self, ai_agent_with_mcp):
        """Test AI Agent MCP health status reporting."""
        status = ai_agent_with_mcp.get_mcp_health_status()

        assert "mcp_connected" in status
        assert "mcp_base_directory" in status
        assert "mcp_allowed_extensions" in status
        assert "mcp_write_enabled" in status
        assert "mcp_delete_enabled" in status

    @pytest.mark.asyncio
    async def test_ai_agent_mcp_context_manager(self, ai_agent_with_mcp):
        """Test AI Agent using MCP as context manager."""
        with (
            patch.object(
                ai_agent_with_mcp.mcp_file_server, "connect", new_callable=AsyncMock
            ) as mock_connect,
            patch.object(
                ai_agent_with_mcp.mcp_file_server, "disconnect", new_callable=AsyncMock
            ) as mock_disconnect,
        ):
            mock_connect.return_value = True

            async with ai_agent_with_mcp.mcp_context():
                # Simulate some file operations
                pass

            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_agent_mcp_file_validation(self, ai_agent_with_mcp):
        """Test AI Agent MCP file validation."""
        # Mock MCP server as connected
        ai_agent_with_mcp.mcp_file_server.is_connected = True

        # Mock the file validation to raise an error for invalid extension
        with (
            patch.object(
                ai_agent_with_mcp.mcp_file_server,
                "read_file",
                side_effect=FileOperationError("File extension .exe not allowed"),
            ),
            pytest.raises(FileOperationError, match="File extension .exe not allowed"),
        ):
            await ai_agent_with_mcp.read_file("malware.exe")

    @pytest.mark.asyncio
    async def test_ai_agent_mcp_configuration_update(
        self, ai_agent_with_mcp, temp_workspace
    ):
        """Test AI Agent MCP configuration updates."""
        # Test updating MCP configuration
        new_config = MCPFileConfig(
            base_directory=temp_workspace,
            allowed_extensions=[".py", ".md"],
            max_file_size=512 * 1024,  # 512KB
            enable_write_operations=False,
            enable_delete_operations=True,
        )

        ai_agent_with_mcp.update_mcp_config(new_config)

        assert ai_agent_with_mcp.mcp_file_server.config.max_file_size == 512 * 1024
        assert ai_agent_with_mcp.mcp_file_server.config.enable_write_operations is False
        assert ai_agent_with_mcp.mcp_file_server.config.enable_delete_operations is True
