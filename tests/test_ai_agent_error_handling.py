"""
Tests for AI Agent file operation error handling and validation.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from src.my_coding_agent.core.mcp_file_server import FileOperationError, MCPFileConfig


class TestFileOperationErrorHandling:
    """Test comprehensive error handling and validation for file operations."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            # Create some test structure
            (workspace / "src").mkdir()
            (workspace / "tests").mkdir()
            (workspace / "src" / "test_file.py").write_text("# Test file")
            (workspace / "README.md").write_text("# Test project")

            # Create a read-only file for permission testing
            readonly_file = workspace / "readonly.txt"
            readonly_file.write_text("readonly content")
            readonly_file.chmod(0o444)  # Read-only

            yield workspace

    @pytest.fixture
    def ai_agent(self, temp_workspace):
        """Create AI Agent instance with temporary workspace."""

        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test_deployment",
            },
        ):
            config = AIAgentConfig.from_env()
            mcp_config = MCPFileConfig(base_directory=str(temp_workspace))
            agent = AIAgent(config, mcp_config, enable_filesystem_tools=True)
            agent.set_workspace_root(temp_workspace)

            # Mock the MCP server as connected for testing
            if agent.mcp_file_server:
                agent.mcp_file_server.is_connected = True

            return agent

    # File path validation tests
    def test_validate_file_path_empty(self, ai_agent):
        """Test validation of empty file paths."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            ai_agent.validate_file_path("")

        with pytest.raises(ValueError, match="File path cannot be empty"):
            ai_agent.validate_file_path("   ")

    def test_validate_file_path_invalid_characters(self, ai_agent):
        """Test validation of file paths with invalid characters."""
        invalid_paths = [
            "file\x00name.txt",  # Null byte
            "file<name.txt",  # Less than
            "file>name.txt",  # Greater than
            "file|name.txt",  # Pipe
            'file"name.txt',  # Quote
            "file*name.txt",  # Asterisk
            "file?name.txt",  # Question mark
        ]

        for invalid_path in invalid_paths:
            with pytest.raises(ValueError, match="Invalid characters in file path"):
                ai_agent.validate_file_path(invalid_path)

    def test_validate_file_path_too_long(self, ai_agent):
        """Test validation of excessively long file paths."""
        long_path = "a" * 300  # Very long path
        with pytest.raises(ValueError, match="File path too long"):
            ai_agent.validate_file_path(long_path)

    def test_validate_file_path_reserved_names(self, ai_agent):
        """Test validation of reserved file names."""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]

        for reserved in reserved_names:
            with pytest.raises(ValueError, match="Reserved file name"):
                ai_agent.validate_file_path(reserved)

            with pytest.raises(ValueError, match="Reserved file name"):
                ai_agent.validate_file_path(f"{reserved}.txt")

    # File extension validation tests
    def test_validate_file_extension_allowed(self, ai_agent):
        """Test validation of allowed file extensions."""
        # Should not raise
        ai_agent.validate_file_extension("test.py")
        ai_agent.validate_file_extension("config.json")
        ai_agent.validate_file_extension("README.md")

    def test_validate_file_extension_blocked(self, ai_agent):
        """Test validation of blocked file extensions."""
        blocked_extensions = [".exe", ".bat", ".cmd", ".scr", ".pif", ".dll"]

        for ext in blocked_extensions:
            with pytest.raises(ValueError, match="File extension not allowed"):
                ai_agent.validate_file_extension(f"test{ext}")

    def test_validate_file_extension_no_extension(self, ai_agent):
        """Test validation of files without extension."""
        # Should be allowed for certain files
        ai_agent.validate_file_extension("Makefile")
        ai_agent.validate_file_extension("Dockerfile")

        # Should be blocked for generic files
        with pytest.raises(ValueError, match="File extension required"):
            ai_agent.validate_file_extension("random_file")

    # File size validation tests
    def test_validate_file_size_within_limit(self, ai_agent):
        """Test validation of file size within limits."""
        content = "x" * 1000  # 1KB
        ai_agent.validate_file_size(content)  # Should not raise

    def test_validate_file_size_exceeds_limit(self, ai_agent):
        """Test validation of file size exceeding limits."""
        content = "x" * (11 * 1024 * 1024)  # 11MB (exceeds default 10MB limit)
        with pytest.raises(ValueError, match="File size exceeds maximum allowed"):
            ai_agent.validate_file_size(content)

    def test_validate_file_size_empty_file(self, ai_agent):
        """Test validation of empty file."""
        ai_agent.validate_file_size("")  # Should be allowed

    # Directory validation tests
    def test_validate_directory_path_valid(self, ai_agent, temp_workspace):
        """Test validation of valid directory paths."""
        ai_agent.validate_directory_path("src")
        ai_agent.validate_directory_path("tests")
        ai_agent.validate_directory_path(".")

    def test_validate_directory_path_nonexistent(self, ai_agent):
        """Test validation of non-existent directory paths."""
        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            ai_agent.validate_directory_path("nonexistent_dir")

    def test_validate_directory_path_is_file(self, ai_agent):
        """Test validation when directory path points to a file."""
        with pytest.raises(ValueError, match="Path is not a directory"):
            ai_agent.validate_directory_path("README.md")

    # Error handling for file operations
    def test_read_file_not_found(self, ai_agent):
        """Test error handling when reading non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            ai_agent.read_workspace_file("nonexistent.txt")

    def test_read_file_permission_denied(self, ai_agent, temp_workspace):
        """Test error handling when reading file with permission issues."""
        # Create a file and remove read permissions
        no_read_file = temp_workspace / "no_read.txt"
        no_read_file.write_text("secret")
        no_read_file.chmod(0o000)  # No permissions

        try:
            with pytest.raises(PermissionError):
                ai_agent.read_workspace_file("no_read.txt")
        finally:
            # Cleanup - restore permissions so file can be deleted
            no_read_file.chmod(0o644)

    def test_write_file_permission_denied(self, ai_agent, temp_workspace):
        """Test error handling when writing to read-only directory."""
        # Create a read-only directory
        readonly_dir = temp_workspace / "readonly_dir"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        try:
            with pytest.raises(PermissionError):
                ai_agent.write_workspace_file("readonly_dir/test.txt", "content")
        finally:
            # Cleanup - restore permissions
            readonly_dir.chmod(0o755)

    def test_write_file_disk_full_simulation(self, ai_agent):
        """Test error handling when disk is full (simulated)."""
        with patch(
            "pathlib.Path.write_text", side_effect=OSError("No space left on device")
        ):
            with pytest.raises(OSError, match="No space left on device"):
                ai_agent.write_workspace_file("test.txt", "content")

    def test_delete_file_not_found(self, ai_agent):
        """Test error handling when deleting non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            ai_agent.delete_workspace_file("nonexistent.txt")

    def test_delete_file_permission_denied(self, ai_agent, temp_workspace):
        """Test error handling when deleting file without permissions."""
        # Create a file in a read-only directory
        readonly_dir = temp_workspace / "readonly_dir"
        readonly_dir.mkdir()
        test_file = readonly_dir / "test.txt"
        test_file.write_text("content")
        readonly_dir.chmod(0o444)  # Read-only

        try:
            with pytest.raises(PermissionError):
                ai_agent.delete_workspace_file("readonly_dir/test.txt")
        finally:
            # Cleanup
            readonly_dir.chmod(0o755)

    # MCP connection error handling
    @pytest.mark.asyncio
    async def test_mcp_connection_lost(self, ai_agent):
        """Test error handling when MCP connection is lost."""
        # Simulate MCP disconnection
        if ai_agent.mcp_file_server:
            ai_agent.mcp_file_server.is_connected = False

        with pytest.raises(FileOperationError, match="Not connected to MCP server"):
            await ai_agent.read_file("test.txt")

    @pytest.mark.asyncio
    async def test_mcp_server_error(self, ai_agent):
        """Test error handling when MCP server returns error."""
        if ai_agent.mcp_file_server:
            # Mock the MCP server to raise an error
            ai_agent.mcp_file_server.read_file = AsyncMock(
                side_effect=FileOperationError("Server internal error")
            )

            with pytest.raises(FileOperationError, match="Server internal error"):
                await ai_agent.read_file("test.txt")

    @pytest.mark.asyncio
    async def test_mcp_timeout_error(self, ai_agent):
        """Test error handling when MCP operations timeout."""
        if ai_agent.mcp_file_server:
            # Mock the MCP server to timeout
            ai_agent.mcp_file_server.read_file = AsyncMock(
                side_effect=asyncio.TimeoutError("Operation timed out")
            )

            with pytest.raises(asyncio.TimeoutError, match="Operation timed out"):
                await ai_agent.read_file("test.txt")

    # Content validation tests
    def test_validate_file_content_encoding(self, ai_agent):
        """Test validation of file content encoding."""
        # Valid UTF-8 content
        ai_agent.validate_file_content("Hello, 世界!")  # Should not raise
        ai_agent.validate_file_content("Regular ASCII text")  # Should not raise
        ai_agent.validate_file_content("")  # Empty content should be allowed

    def test_validate_file_content_dangerous_patterns(self, ai_agent):
        """Test validation of potentially dangerous file content."""
        dangerous_patterns = [
            "eval(",
            "exec(",
            "__import__",
            "subprocess.call",
            "os.system",
        ]

        for pattern in dangerous_patterns:
            with pytest.raises(
                ValueError, match="Potentially dangerous content detected"
            ):
                ai_agent.validate_file_content(f"some code with {pattern}('malicious')")

    # Batch operation error handling
    def test_batch_read_partial_failure(self, ai_agent, temp_workspace):
        """Test error handling in batch operations with partial failures."""
        file_paths = ["src/test_file.py", "nonexistent.txt", "README.md"]

        # Should handle partial failures gracefully
        results = ai_agent.read_multiple_workspace_files(file_paths, fail_fast=False)

        assert "src/test_file.py" in results
        assert "README.md" in results
        assert "nonexistent.txt" in results
        assert "Error:" in results["nonexistent.txt"]

    def test_batch_read_fail_fast(self, ai_agent, temp_workspace):
        """Test error handling in batch operations with fail-fast mode."""
        file_paths = ["src/test_file.py", "nonexistent.txt", "README.md"]

        # Should fail on first error
        with pytest.raises(FileNotFoundError):
            ai_agent.read_multiple_workspace_files(file_paths, fail_fast=True)

    # Recovery and retry tests
    @pytest.mark.asyncio
    async def test_automatic_retry_on_transient_error(self, ai_agent):
        """Test automatic retry mechanism for transient errors."""
        if ai_agent.mcp_file_server:
            # Mock to fail twice then succeed
            call_count = 0

            async def mock_read_file(path):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise FileOperationError("Transient network error")
                return "file content"

            ai_agent.mcp_file_server.read_file = mock_read_file

            # Should eventually succeed after retries
            result = await ai_agent.read_file_with_retry("test.txt", max_retries=3)
            assert result == "file content"
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, ai_agent):
        """Test behavior when retry attempts are exhausted."""
        if ai_agent.mcp_file_server:
            # Mock to always fail
            ai_agent.mcp_file_server.read_file = AsyncMock(
                side_effect=FileOperationError("Persistent error")
            )

            with pytest.raises(FileOperationError, match="Persistent error"):
                await ai_agent.read_file_with_retry("test.txt", max_retries=2)
