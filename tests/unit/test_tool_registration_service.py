"""Test suite for ToolRegistrationService."""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from src.my_coding_agent.core.ai_services.tool_registration_service import (
    ToolRegistrationService,
)


class TestToolRegistrationServiceInitialization:
    """Test ToolRegistrationService initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        service = ToolRegistrationService()

        assert service.filesystem_tools_enabled is False
        assert service.mcp_tools_enabled is False
        assert service.mcp_file_server is None
        assert service.mcp_registry is None
        assert service._mcp_tool_prefix == "mcp_"
        assert service._mcp_status_tool_registered is False
        assert service._environment_tool_registered is False

    def test_init_with_enabled_tools(self):
        """Test initialization with tools enabled."""
        mock_file_server = MagicMock()
        mock_registry = MagicMock()

        service = ToolRegistrationService(
            filesystem_tools_enabled=True,
            mcp_tools_enabled=True,
            mcp_file_server=mock_file_server,
            mcp_registry=mock_registry,
        )

        assert service.filesystem_tools_enabled is True
        assert service.mcp_tools_enabled is True
        assert service.mcp_file_server is mock_file_server
        assert service.mcp_registry is mock_registry

    def test_init_logging(self, caplog):
        """Test that initialization logs appropriate message."""
        with caplog.at_level(logging.INFO):
            ToolRegistrationService(
                filesystem_tools_enabled=True, mcp_tools_enabled=False
            )

        assert "ToolRegistrationService initialized" in caplog.text
        assert "filesystem: True" in caplog.text
        assert "mcp: False" in caplog.text


class TestToolRegistrationServiceMainRegistration:
    """Test main tool registration functionality."""

    def test_register_all_tools_filesystem_only(self):
        """Test registering all tools with only filesystem enabled."""
        mock_agent = MagicMock()
        service = ToolRegistrationService(filesystem_tools_enabled=True)

        with patch.object(service, "register_filesystem_tools") as mock_fs:
            with patch.object(service, "register_environment_tool") as mock_env:
                service.register_all_tools(mock_agent)

                mock_fs.assert_called_once_with(mock_agent)
                mock_env.assert_called_once_with(mock_agent)

    def test_register_all_tools_mcp_only(self):
        """Test registering all tools with only MCP enabled."""
        mock_agent = MagicMock()
        service = ToolRegistrationService(mcp_tools_enabled=True)

        with patch.object(service, "register_mcp_tools") as mock_mcp:
            with patch.object(service, "register_mcp_status_tool") as mock_status:
                with patch.object(service, "register_environment_tool") as mock_env:
                    service.register_all_tools(mock_agent)

                    mock_mcp.assert_called_once_with(mock_agent)
                    mock_status.assert_called_once_with(mock_agent)
                    mock_env.assert_called_once_with(mock_agent)

    def test_register_all_tools_both_enabled(self):
        """Test registering all tools with both filesystem and MCP enabled."""
        mock_agent = MagicMock()
        service = ToolRegistrationService(
            filesystem_tools_enabled=True, mcp_tools_enabled=True
        )

        with patch.object(service, "register_filesystem_tools") as mock_fs:
            with patch.object(service, "register_mcp_tools") as mock_mcp:
                with patch.object(service, "register_mcp_status_tool") as mock_status:
                    with patch.object(service, "register_environment_tool") as mock_env:
                        service.register_all_tools(mock_agent)

                        mock_fs.assert_called_once_with(mock_agent)
                        mock_mcp.assert_called_once_with(mock_agent)
                        mock_status.assert_called_once_with(mock_agent)
                        mock_env.assert_called_once_with(mock_agent)

    def test_register_all_tools_none_enabled(self):
        """Test registering all tools with none enabled."""
        mock_agent = MagicMock()
        service = ToolRegistrationService()

        with patch.object(service, "register_environment_tool") as mock_env:
            service.register_all_tools(mock_agent)

            # Only environment tool should be registered
            mock_env.assert_called_once_with(mock_agent)


class TestToolRegistrationServiceFilesystemTools:
    """Test filesystem tool registration."""

    def test_register_filesystem_tools_disabled(self):
        """Test filesystem tools registration when disabled."""
        mock_agent = MagicMock()
        service = ToolRegistrationService(filesystem_tools_enabled=False)

        service.register_filesystem_tools(mock_agent)

        # Should not register any tools
        mock_agent.tool_plain.assert_not_called()

    def test_register_filesystem_tools_success(self, caplog):
        """Test successful filesystem tools registration."""
        mock_agent = MagicMock()
        service = ToolRegistrationService(filesystem_tools_enabled=True)

        with caplog.at_level(logging.INFO):
            service.register_filesystem_tools(mock_agent)

        # Should register 6 filesystem tools
        assert mock_agent.tool_plain.call_count == 6
        assert "Filesystem tools registered successfully" in caplog.text

    def test_register_filesystem_tools_error(self, caplog):
        """Test filesystem tools registration error handling."""
        mock_agent = MagicMock()
        mock_agent.tool_plain.side_effect = Exception("Tool registration failed")
        service = ToolRegistrationService(filesystem_tools_enabled=True)

        with caplog.at_level(logging.ERROR):
            service.register_filesystem_tools(mock_agent)

        assert "Failed to register filesystem tools" in caplog.text
        assert service.filesystem_tools_enabled is False


class TestToolRegistrationServiceMCPTools:
    """Test MCP tool registration."""

    def test_register_mcp_tools_disabled(self):
        """Test MCP tools registration when disabled."""
        mock_agent = MagicMock()
        service = ToolRegistrationService(mcp_tools_enabled=False)

        service.register_mcp_tools(mock_agent)

        # Should not register any tools
        mock_agent.tool_plain.assert_not_called()

    def test_register_mcp_tools_no_registry(self):
        """Test MCP tools registration with no registry."""
        mock_agent = MagicMock()
        service = ToolRegistrationService(mcp_tools_enabled=True, mcp_registry=None)

        service.register_mcp_tools(mock_agent)

        # Should not register any tools
        mock_agent.tool_plain.assert_not_called()

    def test_register_mcp_tools_success(self, caplog):
        """Test successful MCP tools registration."""
        mock_agent = MagicMock()
        mock_registry = MagicMock()

        # Mock tool data
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool description"
        mock_tool.input_schema = {"properties": {}, "required": []}

        mock_registry.get_all_tools.return_value = {"test_server": [mock_tool]}

        service = ToolRegistrationService(
            mcp_tools_enabled=True, mcp_registry=mock_registry
        )

        with patch.object(service, "_create_mcp_tool_function") as mock_create:
            with caplog.at_level(logging.INFO):
                service.register_mcp_tools(mock_agent)

        mock_create.assert_called_once()
        assert "Registered 1 MCP tools successfully" in caplog.text

    def test_register_mcp_tools_with_conflicts(self, caplog):
        """Test MCP tools registration with name conflicts."""
        mock_agent = MagicMock()
        mock_registry = MagicMock()

        # Mock tool with filesystem conflict
        mock_tool = MagicMock()
        mock_tool.name = "read_file"  # Conflicts with filesystem tool
        mock_tool.description = "Test tool description"
        mock_tool.input_schema = {"properties": {}, "required": []}

        mock_registry.get_all_tools.return_value = {"test_server": [mock_tool]}

        service = ToolRegistrationService(
            filesystem_tools_enabled=True,
            mcp_tools_enabled=True,
            mcp_registry=mock_registry,
        )

        with patch.object(service, "_create_mcp_tool_function") as mock_create:
            service.register_mcp_tools(mock_agent)

        # Should call with prefixed name
        mock_create.assert_called_once()
        call_args = mock_create.call_args[0]
        assert call_args[1] == "mcp_read_file"  # prefixed tool name

    def test_register_mcp_tools_error(self, caplog):
        """Test MCP tools registration error handling."""
        mock_agent = MagicMock()
        mock_registry = MagicMock()
        mock_registry.get_all_tools.side_effect = Exception("Registry error")

        service = ToolRegistrationService(
            mcp_tools_enabled=True, mcp_registry=mock_registry
        )

        with caplog.at_level(logging.ERROR):
            service.register_mcp_tools(mock_agent)

        assert "Failed to register MCP tools" in caplog.text
        assert service.mcp_tools_enabled is False


class TestToolRegistrationServiceStatusAndEnvironmentTools:
    """Test status and environment tool registration."""

    def test_register_mcp_status_tool_success(self, caplog):
        """Test successful MCP status tool registration."""
        mock_agent = MagicMock()
        service = ToolRegistrationService()

        with caplog.at_level(logging.INFO):
            service.register_mcp_status_tool(mock_agent)

        mock_agent.tool_plain.assert_called_once()
        assert service._mcp_status_tool_registered is True
        assert "MCP server status tool registered successfully" in caplog.text

    def test_register_mcp_status_tool_already_registered(self, caplog):
        """Test MCP status tool registration when already registered."""
        mock_agent = MagicMock()
        service = ToolRegistrationService()
        service._mcp_status_tool_registered = True

        with caplog.at_level(logging.DEBUG):
            service.register_mcp_status_tool(mock_agent)

        mock_agent.tool_plain.assert_not_called()
        assert "MCP status tool already registered" in caplog.text

    def test_register_mcp_status_tool_error(self, caplog):
        """Test MCP status tool registration error handling."""
        mock_agent = MagicMock()
        mock_agent.tool_plain.side_effect = Exception("Registration failed")
        service = ToolRegistrationService()

        with caplog.at_level(logging.ERROR):
            service.register_mcp_status_tool(mock_agent)

        assert "Failed to register MCP server status tool" in caplog.text

    def test_register_environment_tool_success(self, caplog):
        """Test successful environment tool registration."""
        mock_agent = MagicMock()
        service = ToolRegistrationService()

        with caplog.at_level(logging.INFO):
            service.register_environment_tool(mock_agent)

        mock_agent.tool_plain.assert_called_once()
        assert service._environment_tool_registered is True
        assert "Environment tool registered successfully" in caplog.text

    def test_register_environment_tool_already_registered(self, caplog):
        """Test environment tool registration when already registered."""
        mock_agent = MagicMock()
        service = ToolRegistrationService()
        service._environment_tool_registered = True

        with caplog.at_level(logging.DEBUG):
            service.register_environment_tool(mock_agent)

        mock_agent.tool_plain.assert_not_called()
        assert "Environment tool already registered" in caplog.text

    def test_register_environment_tool_error(self, caplog):
        """Test environment tool registration error handling."""
        mock_agent = MagicMock()
        mock_agent.tool_plain.side_effect = Exception("Registration failed")
        service = ToolRegistrationService()

        with caplog.at_level(logging.ERROR):
            service.register_environment_tool(mock_agent)

        assert "Failed to register environment tool" in caplog.text


class TestToolRegistrationServiceToolDiscovery:
    """Test tool discovery and description methods."""

    def test_get_available_tools_none_enabled(self):
        """Test getting available tools when none are enabled."""
        service = ToolRegistrationService()

        tools = service.get_available_tools()

        assert tools == []

    def test_get_available_tools_filesystem_only(self):
        """Test getting available tools with filesystem only."""
        service = ToolRegistrationService(filesystem_tools_enabled=True)

        tools = service.get_available_tools()

        expected_tools = [
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "get_file_info",
            "search_files",
        ]
        assert all(tool in tools for tool in expected_tools)

    def test_get_available_tools_with_mcp(self):
        """Test getting available tools with MCP tools."""
        mock_registry = MagicMock()
        service = ToolRegistrationService(
            mcp_tools_enabled=True, mcp_registry=mock_registry
        )

        with patch.object(
            service, "_get_mcp_tools", return_value=["mcp_tool1", "mcp_tool2"]
        ):
            tools = service.get_available_tools()

        assert "mcp_tool1" in tools
        assert "mcp_tool2" in tools

    def test_get_available_tools_with_status_and_env(self):
        """Test getting available tools with status and environment tools."""
        service = ToolRegistrationService()
        service._mcp_status_tool_registered = True
        service._environment_tool_registered = True

        tools = service.get_available_tools()

        assert "get_mcp_server_status" in tools
        assert "get_environment_variable" in tools

    def test_get_tool_descriptions_none_enabled(self):
        """Test getting tool descriptions when none are enabled."""
        service = ToolRegistrationService()

        descriptions = service.get_tool_descriptions()

        assert descriptions == {}

    def test_get_tool_descriptions_filesystem_only(self):
        """Test getting tool descriptions with filesystem only."""
        service = ToolRegistrationService(filesystem_tools_enabled=True)

        descriptions = service.get_tool_descriptions()

        assert "read_file" in descriptions
        assert "Write content to a file" in descriptions["write_file"]

    def test_get_tool_descriptions_with_mcp(self):
        """Test getting tool descriptions with MCP tools."""
        mock_registry = MagicMock()
        service = ToolRegistrationService(
            mcp_tools_enabled=True, mcp_registry=mock_registry
        )

        mock_descriptions = {"mcp_tool1": "MCP tool description"}
        with patch.object(
            service, "_get_mcp_tool_descriptions", return_value=mock_descriptions
        ):
            descriptions = service.get_tool_descriptions()

        assert descriptions == mock_descriptions

    def test_get_tool_descriptions_with_status_and_env(self):
        """Test getting tool descriptions with status and environment tools."""
        service = ToolRegistrationService()
        service._mcp_status_tool_registered = True
        service._environment_tool_registered = True

        descriptions = service.get_tool_descriptions()

        assert "get_mcp_server_status" in descriptions
        assert "get_environment_variable" in descriptions


class TestToolRegistrationServiceMCPHelpers:
    """Test MCP helper methods."""

    def test_get_mcp_tools_no_registry(self):
        """Test getting MCP tools with no registry."""
        service = ToolRegistrationService()

        tools = service._get_mcp_tools()

        assert tools == []

    def test_get_mcp_tools_with_registry(self):
        """Test getting MCP tools with registry."""
        mock_registry = MagicMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        mock_registry.get_all_tools.return_value = {"server1": [mock_tool]}

        service = ToolRegistrationService(mcp_registry=mock_registry)

        tools = service._get_mcp_tools()

        assert "test_tool" in tools

    def test_get_mcp_tools_with_conflicts(self):
        """Test getting MCP tools with filesystem conflicts."""
        mock_registry = MagicMock()
        mock_tool = MagicMock()
        mock_tool.name = "read_file"  # Conflicts with filesystem

        mock_registry.get_all_tools.return_value = {"server1": [mock_tool]}

        service = ToolRegistrationService(
            filesystem_tools_enabled=True, mcp_registry=mock_registry
        )

        tools = service._get_mcp_tools()

        assert "mcp_read_file" in tools

    def test_get_mcp_tool_descriptions_no_registry(self):
        """Test getting MCP tool descriptions with no registry."""
        service = ToolRegistrationService()

        descriptions = service._get_mcp_tool_descriptions()

        assert descriptions == {}

    def test_get_mcp_tool_descriptions_with_registry(self):
        """Test getting MCP tool descriptions with registry."""
        mock_registry = MagicMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test description"

        mock_registry.get_all_tools.return_value = {"server1": [mock_tool]}

        service = ToolRegistrationService(mcp_registry=mock_registry)

        descriptions = service._get_mcp_tool_descriptions()

        assert "test_tool" in descriptions
        assert "Test description (from server1)" in descriptions["test_tool"]


class TestToolRegistrationServiceFilesystemImplementations:
    """Test filesystem tool implementations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_server = MagicMock()
        self.mock_file_server.is_connected = True
        self.service = ToolRegistrationService(
            filesystem_tools_enabled=True, mcp_file_server=self.mock_file_server
        )

    @pytest.mark.asyncio
    async def test_tool_read_file_success(self):
        """Test successful file reading."""
        self.mock_file_server.read_file.return_value = "file content"

        result = await self.service._tool_read_file("test.txt")

        assert result == "file content"
        self.mock_file_server.read_file.assert_called_once_with("test.txt")

    @pytest.mark.asyncio
    async def test_tool_read_file_not_connected(self):
        """Test file reading when server not connected."""
        self.mock_file_server.is_connected = False

        result = await self.service._tool_read_file("test.txt")

        assert "MCP file server not connected" in result

    @pytest.mark.asyncio
    async def test_tool_read_file_error(self):
        """Test file reading with error."""
        self.mock_file_server.read_file.side_effect = Exception("Read error")

        result = await self.service._tool_read_file("test.txt")

        assert "Error reading file" in result

    @pytest.mark.asyncio
    async def test_tool_write_file_success(self):
        """Test successful file writing."""
        self.mock_file_server.write_file.return_value = True

        result = await self.service._tool_write_file("test.txt", "content")

        assert result == "File written successfully"
        self.mock_file_server.write_file.assert_called_once_with("test.txt", "content")

    @pytest.mark.asyncio
    async def test_tool_write_file_failure(self):
        """Test file writing failure."""
        self.mock_file_server.write_file.return_value = False

        result = await self.service._tool_write_file("test.txt", "content")

        assert "Failed to write file" in result

    @pytest.mark.asyncio
    async def test_tool_list_directory_success(self):
        """Test successful directory listing."""
        self.mock_file_server.list_directory.return_value = [
            {"name": "file1.txt", "type": "file", "size": 100},
            {"name": "dir1", "type": "directory"},
        ]

        result = await self.service._tool_list_directory(".")

        assert "Contents of '.'" in result
        assert "📄 file1.txt (100 bytes)" in result
        assert "📁 dir1" in result

    @pytest.mark.asyncio
    async def test_tool_list_directory_empty(self):
        """Test directory listing when empty."""
        self.mock_file_server.list_directory.return_value = []

        result = await self.service._tool_list_directory(".")

        assert "empty or does not exist" in result

    @pytest.mark.asyncio
    async def test_tool_create_directory_success(self):
        """Test successful directory creation."""
        self.mock_file_server.create_directory.return_value = True

        result = await self.service._tool_create_directory("new_dir")

        assert "created successfully" in result

    @pytest.mark.asyncio
    async def test_tool_get_file_info_success(self):
        """Test successful file info retrieval."""
        self.mock_file_server.get_file_info.return_value = {
            "size": 1024,
            "modified": "2023-01-01",
        }

        result = await self.service._tool_get_file_info("test.txt")

        assert "File Information for 'test.txt'" in result
        assert "Size: 1024" in result

    @pytest.mark.asyncio
    async def test_tool_search_files_success(self):
        """Test successful file search."""
        self.mock_file_server.search_files.return_value = ["file1.py", "file2.py"]

        result = await self.service._tool_search_files("*.py", ".")

        assert "Files matching '*.py'" in result
        assert "📄 file1.py" in result
        assert "📄 file2.py" in result

    @pytest.mark.asyncio
    async def test_tool_search_files_no_results(self):
        """Test file search with no results."""
        self.mock_file_server.search_files.return_value = []

        result = await self.service._tool_search_files("*.py", ".")

        assert "No files matching pattern" in result


class TestToolRegistrationServiceMCPImplementations:
    """Test MCP tool implementations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = MagicMock()
        self.service = ToolRegistrationService(
            mcp_tools_enabled=True, mcp_registry=self.mock_registry
        )

    @pytest.mark.asyncio
    async def test_call_mcp_tool_success(self):
        """Test successful MCP tool call."""
        self.mock_registry.call_tool.return_value = "tool result"

        result = await self.service._call_mcp_tool(
            "test_tool", {"arg": "value"}, "server1"
        )

        assert result == "tool result"
        self.mock_registry.call_tool.assert_called_once_with(
            "test_tool", {"arg": "value"}, "server1"
        )

    @pytest.mark.asyncio
    async def test_call_mcp_tool_no_registry(self):
        """Test MCP tool call with no registry."""
        service = ToolRegistrationService()

        result = await service._call_mcp_tool("test_tool", {})

        assert "MCP registry not available" in result

    @pytest.mark.asyncio
    async def test_call_mcp_tool_error(self):
        """Test MCP tool call with error."""
        self.mock_registry.call_tool.side_effect = Exception("Tool error")

        result = await self.service._call_mcp_tool("test_tool", {})

        assert "Error:" in result

    @pytest.mark.asyncio
    async def test_tool_get_mcp_server_status_success(self):
        """Test successful MCP server status retrieval."""
        self.mock_registry.get_server_status.return_value = {
            "server1": {
                "status": "connected",
                "connected": True,
                "tools": ["tool1", "tool2"],
            }
        }

        result = await self.service._tool_get_mcp_server_status()

        assert "MCP Server Status:" in result
        assert "Server: server1" in result
        assert "Status: connected" in result
        assert "Connected: True" in result
        assert "Tools: 2 available" in result

    @pytest.mark.asyncio
    async def test_tool_get_mcp_server_status_no_registry(self):
        """Test MCP server status with no registry."""
        service = ToolRegistrationService()

        result = await service._tool_get_mcp_server_status()

        assert "MCP Registry: Not initialized" in result

    @pytest.mark.asyncio
    async def test_tool_get_mcp_server_status_no_servers(self):
        """Test MCP server status with no servers."""
        self.mock_registry.get_server_status.return_value = {}

        result = await self.service._tool_get_mcp_server_status()

        assert "No MCP servers registered" in result

    @pytest.mark.asyncio
    async def test_tool_get_environment_variable_success(self):
        """Test successful environment variable retrieval."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = await self.service._tool_get_environment_variable("TEST_VAR")

        assert "TEST_VAR" in result
        assert "test_value" in result

    @pytest.mark.asyncio
    async def test_tool_get_environment_variable_not_set(self):
        """Test environment variable retrieval when not set."""
        result = await self.service._tool_get_environment_variable("NONEXISTENT_VAR")

        assert "is not set" in result

    @pytest.mark.asyncio
    async def test_tool_get_environment_variable_sensitive(self):
        """Test environment variable retrieval for sensitive variables."""
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            result = await self.service._tool_get_environment_variable("API_KEY")

        assert "value masked for security" in result
        assert "secret123" not in result


class TestToolRegistrationServiceMCPToolCreation:
    """Test MCP tool function creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_registry = MagicMock()
        self.service = ToolRegistrationService(
            mcp_tools_enabled=True, mcp_registry=self.mock_registry
        )

    def test_create_mcp_tool_function(self):
        """Test creating MCP tool function."""
        mock_agent = MagicMock()

        input_schema = {
            "properties": {"arg1": {"type": "string"}},
            "required": ["arg1"],
        }

        self.service._create_mcp_tool_function(
            mock_agent,
            "test_tool",
            "original_tool",
            "Tool description",
            input_schema,
            "server1",
        )

        # Should register the tool
        mock_agent.tool_plain.assert_called_once()

        # Check the registered function arguments
        call_args = mock_agent.tool_plain.call_args
        assert call_args[1]["name"] == "test_tool"
        assert call_args[1]["description"] == "Tool description"


class TestToolRegistrationServiceErrorHandling:
    """Test comprehensive error handling."""

    def test_filesystem_tool_error_disables_tools(self, caplog):
        """Test that filesystem tool error disables the feature."""
        mock_agent = MagicMock()
        mock_agent.tool_plain.side_effect = Exception("Registration failed")

        service = ToolRegistrationService(filesystem_tools_enabled=True)

        with caplog.at_level(logging.ERROR):
            service.register_filesystem_tools(mock_agent)

        assert service.filesystem_tools_enabled is False
        assert "Failed to register filesystem tools" in caplog.text

    def test_mcp_tool_error_disables_tools(self, caplog):
        """Test that MCP tool error disables the feature."""
        mock_agent = MagicMock()
        mock_registry = MagicMock()
        mock_registry.get_all_tools.side_effect = Exception("Registry failed")

        service = ToolRegistrationService(
            mcp_tools_enabled=True, mcp_registry=mock_registry
        )

        with caplog.at_level(logging.ERROR):
            service.register_mcp_tools(mock_agent)

        assert service.mcp_tools_enabled is False
        assert "Failed to register MCP tools" in caplog.text
