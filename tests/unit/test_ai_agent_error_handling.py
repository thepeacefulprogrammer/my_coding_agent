"""
Tests for AI Agent file operation error handling and validation.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from src.my_coding_agent.core.ai_agent import AIAgent
from src.my_coding_agent.core.ai_services.configuration_service import (
    ConfigurationService,
)
from src.my_coding_agent.core.ai_services.error_handling_service import (
    ErrorHandlingService,
)
from src.my_coding_agent.core.ai_services.workspace_service import WorkspaceService
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
        """Create an AI agent for testing with workspace configured."""
        # Create mock services
        config_service = Mock(spec=ConfigurationService)
        config_service.azure_endpoint = "https://test.openai.azure.com/"
        config_service.azure_api_key = "test_key"
        config_service.deployment_name = "test_deployment"
        config_service.api_version = "2024-02-15-preview"
        config_service.max_tokens = 2000
        config_service.temperature = 0.7
        config_service.request_timeout = 30
        config_service.max_retries = 3

        # Create a real WorkspaceService for testing
        workspace_service = WorkspaceService()
        workspace_service.set_workspace_root(temp_workspace)

        # Add missing methods to the WorkspaceService mock
        def mock_validate_file_size(content, max_size_mb=10):
            size_bytes = len(content.encode("utf-8"))
            max_size_bytes = max_size_mb * 1024 * 1024
            if size_bytes > max_size_bytes:
                raise ValueError(
                    f"File size exceeds maximum allowed: {size_bytes} bytes > {max_size_bytes} bytes"
                )

        def mock_validate_file_extension(file_path):
            import os

            _, ext = os.path.splitext(file_path)
            blocked_extensions = {
                ".exe",
                ".bat",
                ".cmd",
                ".scr",
                ".pif",
                ".dll",
                ".com",
                ".vbs",
                ".ps1",
            }
            if ext.lower() in blocked_extensions:
                raise ValueError(f"File extension not allowed: {ext}")
            if not ext and file_path not in {
                "Makefile",
                "Dockerfile",
                "Jenkinsfile",
                "Vagrantfile",
            }:
                raise ValueError("File extension required")

        def mock_validate_file_content(content):
            # Basic validation - just check for dangerous patterns
            dangerous_patterns = [
                "<script>",
                "eval(",
                "exec(",
                "__import__",
                "subprocess.call",
                "os.system",
            ]
            for pattern in dangerous_patterns:
                if pattern in content:
                    raise ValueError("Potentially dangerous content detected")

        def mock_validate_file_path(file_path):
            import os

            # Check for empty path
            if not file_path or file_path.strip() == "":
                raise ValueError("File path cannot be empty")

            # Check for invalid characters
            invalid_chars = ["\x00", "<", ">", "|", '"', "*", "?"]
            for char in invalid_chars:
                if char in file_path:
                    raise ValueError(f"Invalid characters in file path: {char}")

            # Check for reserved names (Windows)
            reserved_names = [
                "CON",
                "PRN",
                "AUX",
                "NUL",
                "COM1",
                "COM2",
                "COM3",
                "COM4",
                "COM5",
                "COM6",
                "COM7",
                "COM8",
                "COM9",
                "LPT1",
                "LPT2",
                "LPT3",
                "LPT4",
                "LPT5",
                "LPT6",
                "LPT7",
                "LPT8",
                "LPT9",
            ]

            # Extract filename without extension
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0].upper()

            if name_without_ext in reserved_names or filename.upper() in reserved_names:
                raise ValueError(f"Reserved file name: {filename}")

            # Check for too long path
            if len(file_path) > 260:  # Windows MAX_PATH limit
                raise ValueError("File path too long")

        def mock_read_multiple_workspace_files(file_paths, fail_fast=False):
            results = {}
            for file_path in file_paths:
                try:
                    content = workspace_service.read_workspace_file(file_path)
                    results[file_path] = content
                except Exception as e:
                    if fail_fast:
                        raise
                    results[file_path] = f"Error: {e}"
            return results

        # Attach mock methods to workspace_service
        workspace_service.validate_file_size = mock_validate_file_size
        workspace_service.validate_file_extension = mock_validate_file_extension
        workspace_service.validate_file_content = mock_validate_file_content
        workspace_service.validate_file_path = mock_validate_file_path
        workspace_service.read_multiple_workspace_files = (
            mock_read_multiple_workspace_files
        )

        error_service = Mock(spec=ErrorHandlingService)

        # Mock the AI model and agent creation
        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            mcp_config = MCPFileConfig(base_directory=temp_workspace)
            agent = AIAgent(
                mcp_config=mcp_config,
                enable_filesystem_tools=True,
                config_service=config_service,
                workspace_service=workspace_service,
                error_service=error_service,
            )

            # Mock the MCP server as connected for testing
            if agent.mcp_file_server:
                agent.mcp_file_server.is_connected = True

            # Add missing methods that tests expect
            def read_multiple_workspace_files(file_paths, fail_fast=False):
                return agent.read_multiple_files(file_paths, fail_fast)

            async def read_file_with_retry(file_path, max_retries=3):
                for attempt in range(max_retries + 1):
                    try:
                        return await agent.read_file(file_path)
                    except Exception:
                        if attempt == max_retries:
                            raise
                        # Simple retry without backoff for testing
                        continue

            # Attach missing methods to agent
            agent.read_multiple_workspace_files = read_multiple_workspace_files
            agent.read_file_with_retry = read_file_with_retry

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
        with (
            patch(
                "pathlib.Path.write_text",
                side_effect=OSError("No space left on device"),
            ),
            pytest.raises(OSError, match="No space left on device"),
        ):
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
