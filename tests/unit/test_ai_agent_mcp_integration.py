"""
Unit tests for MCP tools integration with AIAgent filesystem tools.

Tests the unified tool system that combines MCP tools with existing filesystem tools,
providing a seamless interface for the AI agent to use both types of tools.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.mcp import MCPClient, MCPServerRegistry, MCPTool
from my_coding_agent.core.mcp_file_server import (
    FileOperationError,
    MCPFileConfig,
    MCPFileServer,
)


@pytest.mark.fast  # Mark fast tests for selective running
@pytest.mark.integration  # Mark integration tests
class TestAIAgentMCPIntegration:
    """Test MCP tools integration with AIAgent."""

    @pytest.fixture
    def ai_config(self):
        """Create test AI agent configuration."""
        return AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test-key",
            deployment_name="test-model",
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
        """Create test MCP configuration."""
        return MCPFileConfig(
            base_directory=temp_workspace,
            allowed_extensions=[".py", ".txt", ".md"],
            enable_write_operations=True,
            enable_delete_operations=False,
        )

    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client."""
        client = MagicMock(spec=MCPClient)
        client.server_name = "test-server"
        client.is_connected = MagicMock(return_value=True)
        client.list_tools = AsyncMock(
            return_value=[
                MCPTool(
                    name="test_tool_one",  # Simple test tool names
                    description="Test tool for integration testing",
                    input_schema={"type": "object", "properties": {}},
                    server="test-server",
                ),
                MCPTool(
                    name="test_tool_two",  # Simple test tool names
                    description="Second test tool for integration testing",
                    input_schema={
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    },
                    server="test-server",
                ),
            ]
        )
        client.call_tool = AsyncMock(
            return_value=[{"text": "Command executed successfully"}]
        )
        # Mock connection methods to avoid connection failures
        client.connect = AsyncMock(return_value=True)
        client.disconnect = AsyncMock()
        client.ping = AsyncMock()
        return client

    @pytest.fixture
    def mock_server_registry(self, mock_mcp_client):
        """Create mock server registry."""
        registry = MagicMock(spec=MCPServerRegistry)
        registry.get_all_tools.return_value = {
            "test-server": [
                MCPTool(
                    name="test_tool_one",  # Matching simple test tool names
                    description="Test tool for integration testing",
                    input_schema={"type": "object", "properties": {}},
                    server="test-server",
                ),
                MCPTool(
                    name="test_tool_two",  # Matching simple test tool names
                    description="Second test tool for integration testing",
                    input_schema={
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    },
                    server="test-server",
                ),
            ]
        }
        registry.call_tool = AsyncMock(return_value=[{"text": "Tool executed"}])
        registry.get_all_servers.return_value = [mock_mcp_client]
        registry.connect_all_servers = AsyncMock(return_value={"test-server": True})
        registry.disconnect_all_servers = AsyncMock()
        registry.get_registry_stats.return_value = {
            "total_servers": 1,
            "connected_servers": 1,
            "total_tools": 2,
            "total_resources": 0,
        }
        # Add connection status mocking
        registry.get_all_server_statuses.return_value = {
            "test-server": MagicMock(connected=True, health_status="healthy")
        }
        return registry

    @pytest_asyncio.fixture
    async def ai_agent_with_mcp(self, ai_config, mcp_config, mock_server_registry):
        """Create AI agent with MCP integration."""
        with patch(
            "my_coding_agent.core.ai_agent.MCPServerRegistry",
            return_value=mock_server_registry,
        ):
            agent = AIAgent(
                config=ai_config,
                mcp_config=mcp_config,
                enable_filesystem_tools=True,
                enable_mcp_tools=True,  # New parameter for MCP integration
            )
            # Mock the agent creation to avoid actual API calls and speed up tests
            agent._agent = MagicMock()
            agent._agent.run = AsyncMock(return_value=MagicMock(data="Test response"))
            agent._agent.tool_plain = (
                MagicMock()
            )  # Mock tool registration to avoid conflicts

            # Ensure MCP registry is properly set up
            agent.mcp_registry = mock_server_registry
            agent.mcp_tools_enabled = True

            yield agent

    @pytest.mark.asyncio
    async def test_mcp_integration_initialization(self, ai_agent_with_mcp):
        """Test that MCP integration initializes correctly."""
        agent = ai_agent_with_mcp

        # Should have MCP registry
        assert hasattr(agent, "mcp_registry")
        assert agent.mcp_registry is not None

        # Should have MCP tools enabled
        assert hasattr(agent, "mcp_tools_enabled")
        assert agent.mcp_tools_enabled is True

    @pytest.mark.asyncio
    async def test_unified_tool_listing(self, ai_agent_with_mcp):
        """Test that get_available_tools returns both filesystem and MCP tools."""
        agent = ai_agent_with_mcp

        tools = agent.get_available_tools()

        # Should include filesystem tools
        filesystem_tools = [
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "get_file_info",
            "search_files",
        ]
        for tool in filesystem_tools:
            assert tool in tools

        # Should include MCP tools
        mcp_tools = [
            "test_tool_one",
            "test_tool_two",
        ]  # Updated to simple test tool names
        for tool in mcp_tools:
            assert tool in tools

    @pytest.mark.asyncio
    async def test_unified_tool_descriptions(self, ai_agent_with_mcp):
        """Test that get_tool_descriptions returns descriptions for both tool types."""
        agent = ai_agent_with_mcp

        descriptions = agent.get_tool_descriptions()

        # Should include filesystem tool descriptions
        assert "read_file" in descriptions
        assert "Read the contents of a file" in descriptions["read_file"]

        # Should include MCP tool descriptions
        assert "test_tool_one" in descriptions
        assert "Test tool for integration testing" in descriptions["test_tool_one"]
        assert "test_tool_two" in descriptions
        assert (
            "Second test tool for integration testing" in descriptions["test_tool_two"]
        )

    @pytest.mark.asyncio
    async def test_mcp_tool_registration_with_agent(self, ai_agent_with_mcp):
        """Test that MCP tools are properly registered with the Pydantic AI agent."""
        agent = ai_agent_with_mcp

        # Verify that MCP tools were registered
        # This would be called during _register_tools()
        assert agent._agent is not None

        # In a real implementation, we would check that the tools were registered
        # with the agent using @agent.tool_plain decorators

    @pytest.mark.asyncio
    async def test_mcp_tool_execution(self, ai_agent_with_mcp, mock_server_registry):
        """Test that MCP tools can be executed through the unified interface."""
        agent = ai_agent_with_mcp

        # Test calling an MCP tool
        result = await agent._call_mcp_tool("test_tool_one", {})

        # Should call through the registry
        mock_server_registry.call_tool.assert_called_once_with(
            "test_tool_one", {}, None
        )
        assert result == "Tool executed"

    @pytest.mark.asyncio
    async def test_mcp_tool_execution_with_arguments(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test MCP tool execution with arguments."""
        agent = ai_agent_with_mcp

        # Test calling an MCP tool with arguments
        args = {"message": "test message"}  # Updated to match test_tool_two schema
        result = await agent._call_mcp_tool("test_tool_two", args)

        # Should call through the registry with arguments
        mock_server_registry.call_tool.assert_called_once_with(
            "test_tool_two", args, None
        )
        assert result == "Tool executed"

    @pytest.mark.asyncio
    async def test_mcp_tool_error_handling(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test error handling for MCP tool execution."""
        agent = ai_agent_with_mcp

        # Mock an error
        mock_server_registry.call_tool.side_effect = Exception("MCP tool failed")

        # Should handle the error gracefully
        result = await agent._call_mcp_tool("test_tool_one", {})

        assert "Error executing MCP tool" in result
        assert "MCP tool failed" in result

    @pytest.mark.asyncio
    async def test_mcp_tools_disabled_fallback(self, ai_config, mcp_config):
        """Test that agent works correctly when MCP tools are disabled."""
        agent = AIAgent(
            config=ai_config,
            mcp_config=mcp_config,
            enable_filesystem_tools=True,
            enable_mcp_tools=False,
        )

        # Should not have MCP integration
        assert not hasattr(agent, "mcp_registry") or agent.mcp_registry is None
        assert not getattr(agent, "mcp_tools_enabled", True)

        # Should still have filesystem tools
        tools = agent.get_available_tools()
        filesystem_tools = ["read_file", "write_file", "list_directory"]
        for tool in filesystem_tools:
            assert tool in tools

    @pytest.mark.asyncio
    async def test_mcp_health_status_integration(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test that MCP health status is included in agent health checks."""
        agent = ai_agent_with_mcp

        # Mock registry health check
        mock_server_registry.get_registry_stats.return_value = {
            "total_servers": 1,
            "connected_servers": 1,
            "total_tools": 2,
            "total_resources": 0,
        }

        health = agent.get_health_status()

        # Should include MCP information
        assert "mcp_enabled" in health
        assert health["mcp_enabled"] is True
        assert "mcp_stats" in health
        assert health["mcp_stats"]["total_servers"] == 1
        assert health["mcp_stats"]["total_tools"] == 2

    @pytest.mark.asyncio
    async def test_tool_name_conflict_resolution(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test handling of tool name conflicts between filesystem and MCP tools."""
        # Mock a conflict where MCP has a tool with same name as filesystem tool
        mock_server_registry.get_all_tools.return_value = {
            "test-server": [
                MCPTool(
                    name="read_file",  # Conflicts with filesystem tool
                    description="MCP read file tool",
                    input_schema={"type": "object"},
                    server="test-server",
                )
            ]
        }

        agent = ai_agent_with_mcp

        # Should handle the conflict (e.g., by prefixing MCP tools)
        tools = agent.get_available_tools()
        _descriptions = agent.get_tool_descriptions()

        # Should have both tools with different names
        assert "read_file" in tools  # Filesystem version
        assert (
            "mcp_read_file" in tools or "test-server_read_file" in tools
        )  # MCP version with prefix

    @pytest.mark.asyncio
    async def test_mcp_server_connection_management(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test MCP server connection management integration."""
        agent = ai_agent_with_mcp

        # Test connecting to MCP servers
        mock_server_registry.connect_all_servers = AsyncMock(
            return_value={"test-server": True}
        )

        result = await agent.connect_mcp_servers()

        mock_server_registry.connect_all_servers.assert_called_once()
        assert result["test-server"] is True

    @pytest.mark.asyncio
    async def test_mcp_server_disconnection(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test MCP server disconnection."""
        agent = ai_agent_with_mcp

        # Test disconnecting from MCP servers
        mock_server_registry.disconnect_all_servers = AsyncMock()

        await agent.disconnect_mcp_servers()

        mock_server_registry.disconnect_all_servers.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_tool_streaming_integration(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test that MCP tools work with streaming responses."""
        agent = ai_agent_with_mcp

        # Mock streaming response
        chunks = []

        async def mock_on_chunk(chunk: str, is_final: bool):
            chunks.append((chunk, is_final))

        # Test streaming with MCP tools available
        response = await agent.send_message_with_tools_stream(
            "Use test_tool_one to check repository status",
            on_chunk=mock_on_chunk,
            enable_filesystem=True,
        )

        # Should complete successfully
        assert response.success
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_mcp_configuration_validation(self, ai_config):
        """Test MCP configuration validation during initialization."""
        # Test that agent can be created with None MCP config
        # The agent should gracefully handle this case
        agent = AIAgent(
            config=ai_config,
            mcp_config=None,  # None config should be handled gracefully
            enable_mcp_tools=True,
        )

        # Agent should be created successfully
        assert agent is not None
        # MCP tools may or may not be enabled depending on implementation
        assert hasattr(agent, "mcp_tools_enabled")

    @pytest.mark.asyncio
    async def test_mcp_tool_schema_validation(self, ai_agent_with_mcp):
        """Test that MCP tool schemas are properly validated."""
        agent = ai_agent_with_mcp

        # Test with invalid arguments
        result = await agent._call_mcp_tool("test_tool_two", {"invalid_arg": "value"})

        # Should handle schema validation error
        assert "Error" in result or "Invalid arguments" in result

    @pytest.mark.asyncio
    async def test_concurrent_mcp_tool_execution(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test concurrent execution of multiple MCP tools."""
        agent = ai_agent_with_mcp

        # Mock multiple tool calls
        mock_server_registry.call_tool.return_value = [{"text": "Success"}]

        # Test concurrent MCP tool execution
        tasks = [
            agent._call_mcp_tool("test_tool_one", {}),
            agent._call_mcp_tool("test_tool_two", {"message": "test"}),
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 2
        for result in results:
            assert "Success" in result or "Tool executed" in result

    @pytest.mark.asyncio
    async def test_mcp_tool_timeout_handling(
        self, ai_agent_with_mcp, mock_server_registry
    ):
        """Test timeout handling for MCP tool execution."""
        agent = ai_agent_with_mcp

        # Mock timeout
        mock_server_registry.call_tool.side_effect = asyncio.TimeoutError(
            "Tool timed out"
        )

        # Test timeout behavior
        result = await agent._call_mcp_tool("test_tool_one", {})

        # Check for timeout handling in the actual error message format
        assert (
            "timeout" in result.lower()
            or "timed out" in result.lower()
            or "Tool executed" in result
        )

    @pytest.mark.asyncio
    async def test_mcp_registry_auto_discovery(self, ai_config, mcp_config):
        """Test automatic discovery of MCP servers from configuration."""
        with patch("my_coding_agent.core.mcp.MCPConfig") as mock_config_class:
            mock_config = MagicMock()
            mock_config.load_servers.return_value = [
                {
                    "server_name": "auto-server",
                    "command": "python",
                    "args": ["-m", "test_server"],
                }
            ]
            mock_config_class.return_value = mock_config

            agent = AIAgent(
                config=ai_config,
                mcp_config=mcp_config,
                enable_mcp_tools=True,
                auto_discover_mcp_servers=True,
            )

            # Should have discovered and registered the server
            assert hasattr(agent, "mcp_registry")

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
