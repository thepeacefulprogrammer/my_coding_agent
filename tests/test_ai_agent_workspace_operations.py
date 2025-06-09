"""
Tests for AI Agent workspace-aware file operations.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from src.my_coding_agent.core.ai_agent import AIAgent


class TestWorkspaceAwareOperations:
    """Test workspace-aware file operations that are scoped to project directory."""

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
            yield workspace

    @pytest.fixture
    def ai_agent(self, temp_workspace):
        """Create AI Agent instance with temporary workspace."""
        from src.my_coding_agent.core.ai_agent import AIAgentConfig
        from src.my_coding_agent.core.mcp_file_server import MCPFileConfig

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
            agent = AIAgent(
                config, mcp_config, enable_filesystem_tools=False
            )  # Don't need MCP for workspace tests
            agent.set_workspace_root(temp_workspace)
            return agent

    def test_set_workspace_root(self, temp_workspace):
        """Test setting workspace root directory."""
        from src.my_coding_agent.core.ai_agent import AIAgentConfig
        from src.my_coding_agent.core.mcp_file_server import MCPFileConfig

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
            agent = AIAgent(config, mcp_config, enable_filesystem_tools=False)
            agent.set_workspace_root(temp_workspace)
            assert agent.workspace_root == temp_workspace

    def test_resolve_workspace_path_valid(self, ai_agent, temp_workspace):
        """Test resolving valid paths within workspace."""
        # Test absolute path within workspace
        abs_path = temp_workspace / "src" / "test_file.py"
        resolved = ai_agent.resolve_workspace_path(str(abs_path))
        assert resolved == abs_path

        # Test relative path
        resolved = ai_agent.resolve_workspace_path("src/test_file.py")
        assert resolved == temp_workspace / "src" / "test_file.py"

        # Test current directory reference
        resolved = ai_agent.resolve_workspace_path("./README.md")
        assert resolved == temp_workspace / "README.md"

    def test_resolve_workspace_path_invalid(self, ai_agent, temp_workspace):
        """Test that paths outside workspace are rejected."""
        # Test parent directory traversal
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.resolve_workspace_path("../outside_file.txt")

        # Test absolute path outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.resolve_workspace_path("/etc/passwd")

        # Test complex traversal
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.resolve_workspace_path("src/../../outside_file.txt")

    def test_workspace_aware_read_file(self, ai_agent, temp_workspace):
        """Test reading files with workspace awareness."""
        # Should work for files within workspace
        content = ai_agent.read_workspace_file("src/test_file.py")
        assert content == "# Test file"

        # Should fail for files outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.read_workspace_file("../outside_file.txt")

    def test_workspace_aware_write_file(self, ai_agent, temp_workspace):
        """Test writing files with workspace awareness."""
        # Should work for files within workspace
        ai_agent.write_workspace_file("new_file.txt", "test content")
        assert (temp_workspace / "new_file.txt").read_text() == "test content"

        # Should fail for files outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.write_workspace_file("../outside_file.txt", "content")

    def test_workspace_aware_list_directory(self, ai_agent, temp_workspace):
        """Test listing directories with workspace awareness."""
        # Should work for directories within workspace
        files = ai_agent.list_workspace_directory("src")
        assert "test_file.py" in files

        # Should work for root directory
        files = ai_agent.list_workspace_directory(".")
        assert "README.md" in files
        assert "src" in files

        # Should fail for directories outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.list_workspace_directory("../")

    def test_workspace_aware_file_exists(self, ai_agent, temp_workspace):
        """Test checking file existence with workspace awareness."""
        # Should work for files within workspace
        assert ai_agent.workspace_file_exists("src/test_file.py") is True
        assert ai_agent.workspace_file_exists("nonexistent.txt") is False

        # Should fail for files outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.workspace_file_exists("../outside_file.txt")

    def test_workspace_aware_create_directory(self, ai_agent, temp_workspace):
        """Test creating directories with workspace awareness."""
        # Should work for directories within workspace
        ai_agent.create_workspace_directory("new_dir")
        assert (temp_workspace / "new_dir").is_dir()

        # Should work for nested directories
        ai_agent.create_workspace_directory("src/subdir")
        assert (temp_workspace / "src" / "subdir").is_dir()

        # Should fail for directories outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.create_workspace_directory("../outside_dir")

    def test_workspace_aware_delete_file(self, ai_agent, temp_workspace):
        """Test deleting files with workspace awareness."""
        # Create a test file to delete
        test_file = temp_workspace / "delete_me.txt"
        test_file.write_text("test")

        # Should work for files within workspace
        ai_agent.delete_workspace_file("delete_me.txt")
        assert not test_file.exists()

        # Should fail for files outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.delete_workspace_file("../outside_file.txt")

    def test_workspace_root_not_set(self):
        """Test that operations fail when workspace root is not set."""
        from src.my_coding_agent.core.ai_agent import AIAgentConfig
        from src.my_coding_agent.core.mcp_file_server import MCPFileConfig

        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test_deployment",
            },
        ):
            config = AIAgentConfig.from_env()
            mcp_config = MCPFileConfig(base_directory="/tmp")
            agent = AIAgent(config, mcp_config, enable_filesystem_tools=False)

            with pytest.raises(ValueError, match="Workspace root not set"):
                agent.resolve_workspace_path("test.txt")

    def test_workspace_symlink_protection(self, ai_agent, temp_workspace):
        """Test protection against symlink attacks."""
        # Create a symlink pointing outside workspace
        outside_dir = temp_workspace.parent / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret content")

        symlink_path = temp_workspace / "evil_link"
        symlink_path.symlink_to(outside_file)

        # Should reject operations on symlinks pointing outside workspace
        with pytest.raises(ValueError, match="Path is outside workspace"):
            ai_agent.read_workspace_file("evil_link")

        # Clean up
        symlink_path.unlink()
        outside_file.unlink()
        outside_dir.rmdir()
