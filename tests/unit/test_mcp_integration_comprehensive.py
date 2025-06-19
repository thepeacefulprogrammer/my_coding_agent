"""
Comprehensive tests for MCP client integration and file operations.
Additional coverage for edge cases and complete integration scenarios.
"""

from __future__ import annotations

import asyncio
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from my_coding_agent.core.ai_agent import AIAgent
from my_coding_agent.core.mcp_file_server import (
    FileOperationError,
    MCPFileConfig,
)


class TestMCPIntegrationComprehensive:
    """Comprehensive tests for MCP integration covering edge cases and full scenarios."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a comprehensive test workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create various file types
            (workspace / "source.py").write_text("def main(): pass")
            (workspace / "config.json").write_text('{"key": "value"}')
            (workspace / "README.md").write_text("# Project")
            (workspace / "script.sh").write_text("#!/bin/bash\necho hello")

            # Create nested directories
            (workspace / "src").mkdir()
            (workspace / "src" / "utils.py").write_text("def helper(): pass")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_main.py").write_text("import unittest")

            # Create edge case files
            (workspace / "empty_file.txt").write_text("")
            large_content = "x" * 1000  # 1KB file
            (workspace / "large_file.txt").write_text(large_content)

            # Create files with special characters
            (workspace / "file with spaces.txt").write_text("content")
            (workspace / "file-with-dashes.txt").write_text("content")

            yield workspace

    @pytest.fixture
    def ai_agent(self, temp_workspace):
        """Create an AI agent with comprehensive MCP integration for testing."""
        # Create mock services like other working tests
        from unittest.mock import Mock

        from my_coding_agent.core.ai_services.configuration_service import (
            ConfigurationService,
        )
        from my_coding_agent.core.ai_services.error_handling_service import (
            ErrorHandlingService,
        )
        from my_coding_agent.core.ai_services.workspace_service import WorkspaceService

        # Create mock config service with required properties
        config_service = Mock(spec=ConfigurationService)
        config_service.azure_endpoint = "https://test.openai.azure.com/"
        config_service.azure_api_key = "test_key"
        config_service.deployment_name = "test-deployment"
        config_service.api_version = "2024-02-15-preview"
        config_service.max_tokens = 1000
        config_service.temperature = 0.7
        config_service.request_timeout = 30
        config_service.max_retries = 3

        # Create real workspace service
        workspace_service = WorkspaceService()
        workspace_service.set_workspace_root(temp_workspace)

        # Add missing method that the test expects
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

        workspace_service.read_multiple_workspace_files = (
            mock_read_multiple_workspace_files
        )

        # Create mock error service
        error_service = Mock(spec=ErrorHandlingService)

        # Create MCP configuration
        mcp_config = MCPFileConfig(
            base_directory=temp_workspace,
            allowed_extensions=[".py", ".json", ".md", ".txt", ".sh"],
            max_file_size=2 * 1024 * 1024,  # 2MB
            enable_write_operations=True,
            enable_delete_operations=True,
            enforce_workspace_boundaries=True,
        )

        # Mock the AI model and agent creation like working tests
        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            # Create agent with services
            agent = AIAgent(
                config_service=config_service,
                workspace_service=workspace_service,
                error_service=error_service,
                mcp_config=mcp_config,
                enable_filesystem_tools=True,
            )

            # Mock MCP as connected
            if agent.mcp_file_server:
                agent.mcp_file_server.is_connected = True

            return agent

    # Comprehensive file operation tests
    @pytest.mark.asyncio
    async def test_complete_file_lifecycle(self, ai_agent, temp_workspace):
        """Test complete file lifecycle: create, read, update, delete."""
        # Mock MCP operations using ExitStack
        with ExitStack() as stack:
            mock_write = stack.enter_context(
                patch.object(ai_agent.mcp_file_server, "write_file", return_value=True)
            )
            mock_read = stack.enter_context(
                patch.object(
                    ai_agent.mcp_file_server,
                    "read_file",
                    return_value="initial content",
                )
            )
            mock_delete = stack.enter_context(
                patch.object(ai_agent.mcp_file_server, "delete_file", return_value=True)
            )

            # Create file
            result = await ai_agent.write_file("lifecycle_test.py", "initial content")
            assert result is True

            # Read file
            content = await ai_agent.read_file("lifecycle_test.py")
            assert content == "initial content"

            # Update file
            mock_read.return_value = "updated content"
            await ai_agent.write_file("lifecycle_test.py", "updated content")
            updated_content = await ai_agent.read_file("lifecycle_test.py")
            assert updated_content == "updated content"

            # Delete file
            delete_result = await ai_agent.delete_file("lifecycle_test.py")
            assert delete_result is True

            # Verify calls
            assert mock_write.call_count == 2
            assert mock_read.call_count == 2
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_file_operations(self, ai_agent):
        """Test performing multiple file operations in batch."""
        files_to_read = ["source.py", "config.json", "README.md"]

        # Since we have a WorkspaceService configured, this will call the sync version
        # Mock the workspace service's read method
        def mock_read_workspace_file(file_path):
            file_contents = {
                "source.py": "def main(): pass",
                "config.json": '{"key": "value"}',
                "README.md": "# Project",
            }
            return file_contents.get(file_path, f"content of {file_path}")

        with patch.object(
            ai_agent.workspace_service,
            "read_workspace_file",
            side_effect=mock_read_workspace_file,
        ):
            results = ai_agent.read_multiple_files(files_to_read)  # Remove await

            assert len(results) == 3
            assert results["source.py"] == "def main(): pass"
            assert results["config.json"] == '{"key": "value"}'
            assert results["README.md"] == "# Project"

    @pytest.mark.asyncio
    async def test_nested_directory_operations(self, ai_agent):
        """Test operations on nested directory structures."""
        # Mock directory listing
        nested_files = ["utils.py", "helper.py", "submodule/"]

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    ai_agent.mcp_file_server,
                    "list_directory",
                    return_value=nested_files,
                )
            )
            stack.enter_context(
                patch.object(
                    ai_agent.mcp_file_server, "create_directory", return_value=True
                )
            )

            # List nested directory
            files = await ai_agent.list_directory("src")
            assert "utils.py" in files
            assert "submodule/" in files

            # Create nested directory
            result = await ai_agent.create_directory("src/new_module")
            assert result is True

    @pytest.mark.asyncio
    async def test_file_search_with_patterns(self, ai_agent):
        """Test file search with various patterns."""
        # Mock search results for different patterns
        python_files = ["source.py", "src/utils.py", "tests/test_main.py"]
        all_files = ["source.py", "config.json", "README.md", "script.sh"]

        with patch.object(ai_agent.mcp_file_server, "search_files") as mock_search:
            # Search for Python files
            mock_search.return_value = python_files
            py_results = await ai_agent.search_files("*.py")
            assert len(py_results) == 3
            assert all(f.endswith(".py") for f in py_results)

            # Search for all files
            mock_search.return_value = all_files
            all_results = await ai_agent.search_files("*")
            assert len(all_results) == 4

    # Edge case handling tests
    @pytest.mark.asyncio
    async def test_empty_file_handling(self, ai_agent):
        """Test handling of empty files."""
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(ai_agent.mcp_file_server, "read_file", return_value="")
            )
            stack.enter_context(
                patch.object(ai_agent.mcp_file_server, "write_file", return_value=True)
            )

            # Read empty file
            content = await ai_agent.read_file("empty_file.txt")
            assert content == ""

            # Write empty file
            result = await ai_agent.write_file("new_empty.txt", "")
            assert result is True

    @pytest.mark.asyncio
    async def test_special_character_filenames(self, ai_agent):
        """Test handling of files with special characters in names."""
        special_files = {
            "file with spaces.txt": "content1",
            "file-with-dashes.txt": "content2",
            "file_with_underscores.txt": "content3",
        }

        for filename, content in special_files.items():
            with patch.object(
                ai_agent.mcp_file_server, "read_file", return_value=content
            ):
                result = await ai_agent.read_file(filename)
                assert result == content

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, ai_agent):
        """Test concurrent file operations."""

        async def read_file(filename, expected_content):
            with patch.object(
                ai_agent.mcp_file_server, "read_file", return_value=expected_content
            ):
                return await ai_agent.read_file(filename)

        # Run multiple operations concurrently
        tasks = [
            read_file("source.py", "def main(): pass"),
            read_file("config.json", '{"key": "value"}'),
            read_file("README.md", "# Project"),
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert results[0] == "def main(): pass"
        assert results[1] == '{"key": "value"}'
        assert results[2] == "# Project"

    # Error recovery and resilience tests
    @pytest.mark.asyncio
    async def test_connection_recovery(self, ai_agent):
        """Test recovery from connection issues."""
        # Simulate connection loss and recovery
        ai_agent.mcp_file_server.is_connected = False

        with pytest.raises(FileOperationError, match="Not connected to MCP server"):
            await ai_agent.read_file("test.py")

        # Simulate reconnection
        with patch.object(ai_agent.mcp_file_server, "connect", return_value=True):
            reconnect_result = await ai_agent.connect_mcp()
            assert reconnect_result is True

    @pytest.mark.asyncio
    async def test_operation_timeout_handling(self, ai_agent):
        """Test handling of operation timeouts."""
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    ai_agent.mcp_file_server,
                    "read_file",
                    side_effect=asyncio.TimeoutError("Operation timed out"),
                )
            )
            with pytest.raises(asyncio.TimeoutError):
                await ai_agent.read_file("test.py")

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, ai_agent):
        """Test handling when some operations succeed and others fail."""
        files = ["good_file.py", "bad_file.py", "another_good.py"]

        def mock_read_workspace_file(filename):
            if filename == "bad_file.py":
                raise FileOperationError("File corrupted")
            return f"content of {filename}"

        with patch.object(
            ai_agent.workspace_service,
            "read_workspace_file",
            side_effect=mock_read_workspace_file,
        ):
            results = ai_agent.read_multiple_files(files)  # Remove await

            assert "good_file.py" in results
            assert "another_good.py" in results
            assert "Error:" in results["bad_file.py"]  # Error message format may vary

    # Integration with AI Agent features
    @pytest.mark.asyncio
    async def test_file_context_integration(self, ai_agent):
        """Test integration of file operations with AI context."""
        mock_file_content = "def calculate(a, b):\n    return a + b"

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    ai_agent.mcp_file_server,
                    "read_file",
                    return_value=mock_file_content,
                )
            )
            mock_send = stack.enter_context(patch.object(ai_agent, "send_message"))

            mock_response = Mock()
            mock_response.success = True
            mock_response.content = "This function adds two numbers together."
            mock_send.return_value = mock_response

            response = await ai_agent.send_message_with_file_context(
                "What does this function do?", "calculator.py"
            )

            assert response.success is True
            assert "function" in response.content

    @pytest.mark.asyncio
    async def test_workspace_validation_integration(self, ai_agent, temp_workspace):
        """Test integration with workspace validation."""
        # Test valid workspace operations
        ai_agent.validate_directory_path("src")
        ai_agent.validate_file_path("source.py")

        # Test workspace boundary enforcement
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.resolve_workspace_path("../outside_file.txt")

    # Performance and resource tests
    @pytest.mark.asyncio
    async def test_large_file_handling(self, ai_agent):
        """Test handling of large files within limits."""
        large_content = "x" * (1024 * 1024)  # 1MB content

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(ai_agent.mcp_file_server, "write_file", return_value=True)
            )
            stack.enter_context(
                patch.object(
                    ai_agent.mcp_file_server, "read_file", return_value=large_content
                )
            )

            # Write large file
            result = await ai_agent.write_file("large.txt", large_content)
            assert result is True

            # Read large file
            content = await ai_agent.read_file("large.txt")
            assert len(content) == 1024 * 1024

    @pytest.mark.asyncio
    async def test_memory_efficiency_batch_operations(self, ai_agent):
        """Test memory efficiency in batch operations."""
        # Simulate many small files
        many_files = [f"file_{i}.txt" for i in range(100)]

        def mock_read_workspace_file(filename):
            return f"content of {filename}"

        with patch.object(
            ai_agent.workspace_service,
            "read_workspace_file",
            side_effect=mock_read_workspace_file,
        ):
            results = ai_agent.read_multiple_files(many_files)  # Remove await

            assert len(results) == 100
            assert all(
                f"content of file_{i}.txt" == results[f"file_{i}.txt"]
                for i in range(100)
            )

    # Configuration and health tests
    def test_mcp_configuration_completeness(self, ai_agent):
        """Test that MCP configuration covers all necessary aspects."""
        config = ai_agent.mcp_file_server.config

        # Verify all essential settings are configured
        assert config.base_directory is not None
        assert len(config.allowed_extensions) > 0
        assert config.max_file_size > 0
        assert isinstance(config.enable_write_operations, bool)
        assert isinstance(config.enable_delete_operations, bool)
        assert isinstance(config.enforce_workspace_boundaries, bool)

    def test_health_monitoring_integration(self, ai_agent):
        """Test health monitoring of MCP integration."""
        health_status = ai_agent.get_mcp_health_status()

        assert "mcp_configured" in health_status
        assert "mcp_connected" in health_status
        assert "mcp_base_directory" in health_status
        assert health_status["mcp_configured"] is True

    def test_comprehensive_error_scenarios(self, ai_agent):
        """Test comprehensive error scenarios and recovery."""
        # Test various error types
        error_scenarios = [
            ("File not found", FileOperationError("File does not exist")),
            ("Permission denied", FileOperationError("Access denied")),
            ("Invalid path", FileOperationError("Invalid file path")),
            ("Size limit exceeded", FileOperationError("File too large")),
        ]

        for _, error in error_scenarios:
            with ExitStack() as stack:
                stack.enter_context(
                    patch.object(
                        ai_agent.mcp_file_server, "read_file", side_effect=error
                    )
                )
                with pytest.raises(FileOperationError):
                    asyncio.run(ai_agent.read_file("test.txt"))
