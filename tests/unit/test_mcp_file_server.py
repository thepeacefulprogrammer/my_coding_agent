"""Unit tests for MCP File Server integration."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from my_coding_agent.core.mcp_file_server import (
    FileOperationError,
    MCPFileConfig,
    MCPFileServer,
)


class TestMCPFileConfig:
    """Test the MCP File Server configuration class."""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values."""
        config = MCPFileConfig()

        assert config.base_directory == Path.cwd()
        assert config.allowed_extensions == [
            ".py",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".cfg",
        ]
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.enable_write_operations is True
        assert config.enable_delete_operations is False
        assert config.follow_symlinks is False

    def test_config_with_custom_values(self):
        """Test creating config with custom values."""
        custom_path = Path("/tmp")  # Use existing directory for testing
        config = MCPFileConfig(
            base_directory=custom_path,
            allowed_extensions=[".py", ".js"],
            max_file_size=5 * 1024 * 1024,
            enable_write_operations=False,
            enable_delete_operations=True,
            follow_symlinks=True,
        )

        assert config.base_directory == custom_path
        assert config.allowed_extensions == [".py", ".js"]
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.enable_write_operations is False
        assert config.enable_delete_operations is True
        assert config.follow_symlinks is True


class TestMCPFileServer:
    """Test the MCP File Server class."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('Hello, World!')")

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
            allowed_extensions=[".py", ".json", ".md"],
            max_file_size=1024 * 1024,  # 1MB
        )

    @pytest.fixture
    def mcp_server(self, mcp_config):
        """Create MCP file server instance for testing."""
        return MCPFileServer(mcp_config)

    def test_server_initialization(self, mcp_server, temp_workspace):
        """Test MCP server initialization."""
        assert mcp_server.config.base_directory == Path(temp_workspace)
        assert mcp_server.is_connected is False
        assert mcp_server.client_session is None

    @pytest.mark.asyncio
    async def test_connect_to_mcp_server_success(self, mcp_server):
        """Test successful connection to MCP server."""
        # Mock a successful MCP client connection
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_read_stream = AsyncMock()
        mock_write_stream = AsyncMock()

        with patch("my_coding_agent.core.mcp_file_server.ClientSession") as mock_client:
            mock_client.return_value = mock_session

            with patch("mcp.client.stdio.stdio_client") as mock_stdio:
                # Create an async context manager mock
                mock_stdio_instance = AsyncMock()
                mock_stdio_instance.__aenter__ = AsyncMock(
                    return_value=(mock_read_stream, mock_write_stream)
                )
                mock_stdio_instance.__aexit__ = AsyncMock(return_value=None)
                mock_stdio.return_value = mock_stdio_instance

                result = await mcp_server.connect()

                assert result is True
                assert mcp_server.is_connected is True
                # Verify the session was created and initialized
                mock_client.assert_called_once_with(mock_read_stream, mock_write_stream)
                mock_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_to_mcp_server_failure(self, mcp_server):
        """Test failed connection to MCP server."""
        # Test case where base directory access fails (should return False)
        with patch("os.access", return_value=False):
            result = await mcp_server.connect()

            assert result is False
            assert mcp_server.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_from_mcp_server(self, mcp_server):
        """Test disconnecting from MCP server."""
        # Mock a connected state
        mcp_server.is_connected = True
        mcp_server.client_session = AsyncMock()
        mcp_server._read_stream = AsyncMock()
        mcp_server._write_stream = AsyncMock()

        await mcp_server.disconnect()

        assert mcp_server.is_connected is False
        assert mcp_server.client_session is None

    @pytest.mark.asyncio
    async def test_read_file_success(self, mcp_server, temp_workspace):
        """Test successful file reading."""
        # Setup connected state
        mcp_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="print('Hello, World!')")]
            )
        )
        mcp_server.client_session = mock_session

        file_path = "test.py"
        content = await mcp_server.read_file(file_path)

        assert content == "print('Hello, World!')"
        mock_session.call_tool.assert_called_once_with(
            "read_file", {"path": os.path.join(temp_workspace, file_path)}
        )

    @pytest.mark.asyncio
    async def test_read_file_not_connected(self, mcp_server):
        """Test reading file when not connected."""
        with pytest.raises(FileOperationError, match="Not connected to MCP server"):
            await mcp_server.read_file("test.py")

    @pytest.mark.asyncio
    async def test_read_file_invalid_extension(self, mcp_server):
        """Test reading file with invalid extension."""
        mcp_server.is_connected = True

        with pytest.raises(FileOperationError, match="File extension .exe not allowed"):
            await mcp_server.read_file("malware.exe")

    @pytest.mark.asyncio
    async def test_read_file_path_traversal_attack(self, mcp_server):
        """Test protection against path traversal attacks."""
        mcp_server.is_connected = True

        with pytest.raises(FileOperationError, match="Access denied"):
            await mcp_server.read_file("../../../etc/passwd")

    @pytest.mark.asyncio
    async def test_write_file_success(self, mcp_server, temp_workspace):
        """Test successful file writing."""
        # Setup connected state
        mcp_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="File written successfully")]
            )
        )
        mcp_server.client_session = mock_session

        file_path = "new_file.py"
        content = "def hello():\n    print('Hello!')"

        result = await mcp_server.write_file(file_path, content)

        assert result is True
        mock_session.call_tool.assert_called_once_with(
            "write_file",
            {"path": os.path.join(temp_workspace, file_path), "content": content},
        )

    @pytest.mark.asyncio
    async def test_write_file_disabled(self, mcp_server):
        """Test writing file when write operations are disabled."""
        mcp_server.config.enable_write_operations = False
        mcp_server.is_connected = True

        with pytest.raises(FileOperationError, match="Write operations not permitted"):
            await mcp_server.write_file("test.py", "content")

    @pytest.mark.asyncio
    async def test_write_file_content_too_large(self, mcp_server):
        """Test writing file with content exceeding max size."""
        mcp_server.is_connected = True
        large_content = "x" * (mcp_server.config.max_file_size + 1)

        with pytest.raises(FileOperationError, match="File size.*exceeds limit"):
            await mcp_server.write_file("large_file.py", large_content)

    @pytest.mark.asyncio
    async def test_list_directory_success(self, mcp_server, temp_workspace):
        """Test successful directory listing."""
        # Setup connected state
        mcp_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="test.py\nsubdir/\nsubdir/data.json")]
            )
        )
        mcp_server.client_session = mock_session

        files = await mcp_server.list_directory(".")

        assert "test.py" in files
        assert "subdir/" in files
        mock_session.call_tool.assert_called_once_with(
            "list_directory", {"path": temp_workspace}
        )

    @pytest.mark.asyncio
    async def test_delete_file_success(self, mcp_server, temp_workspace):
        """Test successful file deletion."""
        # Enable delete operations
        mcp_server.config.enable_delete_operations = True
        mcp_server.is_connected = True

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="File deleted successfully")]
            )
        )
        mcp_server.client_session = mock_session

        result = await mcp_server.delete_file("test.py")

        assert result is True
        mock_session.call_tool.assert_called_once_with(
            "delete_file", {"path": os.path.join(temp_workspace, "test.py")}
        )

    @pytest.mark.asyncio
    async def test_delete_file_disabled(self, mcp_server):
        """Test deleting file when delete operations are disabled."""
        mcp_server.is_connected = True

        with pytest.raises(FileOperationError, match="Delete operations not permitted"):
            await mcp_server.delete_file("test.py")

    @pytest.mark.asyncio
    async def test_create_directory_success(self, mcp_server, temp_workspace):
        """Test successful directory creation."""
        mcp_server.is_connected = True
        mcp_server.config.enable_write_operations = True

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="Directory created successfully")]
            )
        )
        mcp_server.client_session = mock_session

        result = await mcp_server.create_directory("new_dir")

        assert result is True
        mock_session.call_tool.assert_called_once_with(
            "create_directory", {"path": os.path.join(temp_workspace, "new_dir")}
        )

    @pytest.mark.asyncio
    async def test_get_file_info_success(self, mcp_server, temp_workspace):
        """Test getting file information."""
        mcp_server.is_connected = True

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[
                    Mock(
                        type="text",
                        text='{"size": 1024, "modified": "2024-01-01T12:00:00Z", "is_directory": false}',
                    )
                ]
            )
        )
        mcp_server.client_session = mock_session

        info = await mcp_server.get_file_info("test.py")

        assert info["size"] == 1024
        assert info["is_directory"] is False
        mock_session.call_tool.assert_called_once_with(
            "get_file_info", {"path": os.path.join(temp_workspace, "test.py")}
        )

    @pytest.mark.asyncio
    async def test_search_files_success(self, mcp_server, temp_workspace):
        """Test searching for files."""
        mcp_server.is_connected = True

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=Mock(
                content=[Mock(type="text", text="test.py\nsubdir/data.json")]
            )
        )
        mcp_server.client_session = mock_session

        results = await mcp_server.search_files("*.py")

        assert "test.py" in results
        mock_session.call_tool.assert_called_once_with(
            "search_files", {"pattern": "*.py", "base_path": temp_workspace}
        )

    def test_validate_file_path_valid(self, mcp_server):
        """Test validation of valid file paths."""
        # These should not raise exceptions
        mcp_server._validate_file_path("test.py")
        mcp_server._validate_file_path("subdir/file.json")
        mcp_server._validate_file_path("deep/nested/path/file.md")

    def test_validate_file_path_invalid_extension(self, mcp_server):
        """Test validation rejects invalid extensions."""
        with pytest.raises(FileOperationError, match="File extension .exe not allowed"):
            mcp_server._validate_file_path("malware.exe")

    def test_validate_file_path_traversal_attempts(self, mcp_server):
        """Test validation blocks path traversal attempts."""
        dangerous_paths = [
            ("../../../etc/passwd", "path traversal not allowed"),
            ("..\\..\\windows\\system32", "path traversal not allowed"),
            ("/etc/passwd", "absolute path not allowed"),
            ("test/../../../secret.txt", "path traversal not allowed"),
        ]

        for path, expected_message in dangerous_paths:
            with pytest.raises(FileOperationError, match=expected_message):
                mcp_server._validate_file_path(path)

        # Windows drive letters (only test on Windows or simulate)
        import os

        if os.name == "nt":
            with pytest.raises(FileOperationError, match="absolute path not allowed"):
                mcp_server._validate_file_path("C:\\Windows\\System32")

    def test_get_absolute_path(self, mcp_server, temp_workspace):
        """Test conversion to absolute paths."""
        abs_path = mcp_server._get_absolute_path("test.py")
        expected = os.path.join(temp_workspace, "test.py")
        assert abs_path == expected

    def test_get_health_status(self, mcp_server):
        """Test getting server health status."""
        status = mcp_server.get_health_status()

        assert "connected" in status
        assert "base_directory" in status
        assert "allowed_extensions" in status
        assert "max_file_size" in status
        assert "write_enabled" in status
        assert "delete_enabled" in status

    @pytest.mark.asyncio
    async def test_error_handling_during_operations(self, mcp_server):
        """Test error handling during file operations."""
        mcp_server.is_connected = True
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            side_effect=Exception("MCP operation failed")
        )
        mcp_server.client_session = mock_session

        with pytest.raises(FileOperationError, match="Failed to read file"):
            await mcp_server.read_file("test.py")

    @pytest.mark.asyncio
    async def test_context_manager_behavior(self, mcp_server):
        """Test MCP server as context manager."""
        with (
            patch.object(mcp_server, "connect", new_callable=AsyncMock) as mock_connect,
            patch.object(
                mcp_server, "disconnect", new_callable=AsyncMock
            ) as mock_disconnect,
        ):
            mock_connect.return_value = True

            # The context manager should call connect and set is_connected
            async def mock_connect_side_effect():
                mcp_server.is_connected = True
                return True

            mock_connect.side_effect = mock_connect_side_effect

            async with mcp_server:
                assert mcp_server.is_connected is True

            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_connection_failure(self, mcp_server):
        """Test context manager when connection fails."""
        with patch.object(
            mcp_server, "connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = False

            with pytest.raises(
                FileOperationError, match="Failed to connect to MCP server"
            ):
                async with mcp_server:
                    pass


class TestFileOperationError:
    """Test the custom FileOperationError exception."""

    def test_error_creation_with_message(self):
        """Test creating error with message."""
        error = FileOperationError("Test error message")
        assert str(error) == "Test error message"

    def test_error_creation_with_cause(self):
        """Test creating error with underlying cause."""
        cause = ValueError("Original error")
        error = FileOperationError("Wrapper error", cause)
        assert str(error) == "Wrapper error"
        assert error.__cause__ == cause
