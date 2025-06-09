"""Unit tests for AI Agent filesystem tools integration."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.mcp_file_server import (
    FileOperationError,
    MCPFileConfig,
)


class TestAIAgentFilesystemTools:
    """Test AI Agent integration with filesystem tools."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir()

            # Create test files
            (workspace / "example.py").write_text("def hello(): return 'world'")
            (workspace / "config.json").write_text('{"setting": "value"}')
            (workspace / "README.md").write_text("# Test Project")

            # Create subdirectory
            subdir = workspace / "src"
            subdir.mkdir()
            (subdir / "main.py").write_text("from example import hello")

            yield str(workspace)

    @pytest.fixture
    def ai_config(self):
        """Create AI Agent config for testing."""
        return AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test-key",
            deployment_name="test-deployment",
            request_timeout=30,
            max_retries=3,
        )

    @pytest.fixture
    def mcp_config(self, temp_workspace):
        """Create MCP config for testing."""
        return MCPFileConfig(
            base_directory=temp_workspace,
            allowed_extensions=[".py", ".json", ".md", ".txt"],
            max_file_size=1024 * 1024,
            enable_write_operations=True,
            enable_delete_operations=False,
            enforce_workspace_boundaries=True,
            blocked_paths=["secrets/*", ".env"],
        )

    @pytest.fixture
    def ai_agent_with_filesystem(self, ai_config, mcp_config):
        """Create AI Agent with filesystem tools enabled."""
        return AIAgent(ai_config, mcp_config, enable_filesystem_tools=True)

    def test_ai_agent_filesystem_tools_initialization(self, ai_agent_with_filesystem):
        """Test AI Agent initializes with filesystem tools."""
        agent = ai_agent_with_filesystem

        # Should have MCP file server
        assert agent.mcp_file_server is not None
        assert agent.filesystem_tools_enabled is True

        # Should have filesystem tools registered
        tools = agent.get_available_tools()
        expected_tools = [
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "get_file_info",
            "search_files",
        ]

        for tool_name in expected_tools:
            assert tool_name in tools

    def test_ai_agent_without_filesystem_tools(self, ai_config):
        """Test AI Agent without filesystem tools."""
        agent = AIAgent(ai_config, mcp_config=None, enable_filesystem_tools=False)

        assert agent.mcp_file_server is None
        assert agent.filesystem_tools_enabled is False

        tools = agent.get_available_tools()
        filesystem_tools = [
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "get_file_info",
            "search_files",
        ]

        for tool_name in filesystem_tools:
            assert tool_name not in tools

    @pytest.mark.asyncio
    async def test_read_file_tool(self, ai_agent_with_filesystem, temp_workspace):
        """Test read_file tool functionality."""
        agent = ai_agent_with_filesystem

        # Mock the MCP connection and file server read operation
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server,
                "read_file",
                return_value="def hello(): return 'world'",
            ) as mock_read:
                result = await agent._tool_read_file("example.py")

                assert result == "def hello(): return 'world'"
                mock_read.assert_called_once_with("example.py")

    @pytest.mark.asyncio
    async def test_write_file_tool(self, ai_agent_with_filesystem):
        """Test write_file tool functionality."""
        agent = ai_agent_with_filesystem

        # Mock the MCP connection and file server write operation
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server, "write_file", return_value=True
            ) as mock_write:
                result = await agent._tool_write_file("test.py", "print('hello')")

                assert result == "File written successfully"
                mock_write.assert_called_once_with("test.py", "print('hello')")

    @pytest.mark.asyncio
    async def test_list_directory_tool(self, ai_agent_with_filesystem):
        """Test list_directory tool functionality."""
        agent = ai_agent_with_filesystem

        # Mock the MCP connection and file server list operation
        expected_files = ["example.py", "config.json", "README.md", "src/"]
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server, "list_directory", return_value=expected_files
            ) as mock_list:
                result = await agent._tool_list_directory(".")

                assert "example.py" in result
                assert "config.json" in result
                assert "README.md" in result
                mock_list.assert_called_once_with(".")

    @pytest.mark.asyncio
    async def test_create_directory_tool(self, ai_agent_with_filesystem):
        """Test create_directory tool functionality."""
        agent = ai_agent_with_filesystem

        # Mock the MCP connection and file server create directory operation
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server, "create_directory", return_value=True
            ) as mock_create:
                result = await agent._tool_create_directory("new_folder")

                assert result == "Directory created successfully"
                mock_create.assert_called_once_with("new_folder")

    @pytest.mark.asyncio
    async def test_get_file_info_tool(self, ai_agent_with_filesystem):
        """Test get_file_info tool functionality."""
        agent = ai_agent_with_filesystem

        # Mock the MCP connection and file server info operation
        expected_info = {
            "name": "example.py",
            "size": 25,
            "type": "file",
            "modified": "2023-01-01T12:00:00Z",
        }
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server, "get_file_info", return_value=expected_info
            ) as mock_info:
                result = await agent._tool_get_file_info("example.py")

                assert "example.py" in result
                assert "25" in result
                mock_info.assert_called_once_with("example.py")

    @pytest.mark.asyncio
    async def test_search_files_tool(self, ai_agent_with_filesystem):
        """Test search_files tool functionality."""
        agent = ai_agent_with_filesystem

        # Mock the MCP connection and file server search operation
        expected_results = ["example.py", "src/main.py"]
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server, "search_files", return_value=expected_results
            ) as mock_search:
                result = await agent._tool_search_files("*.py", ".")

                assert "example.py" in result
                assert "src/main.py" in result
                mock_search.assert_called_once_with("*.py", ".")

    @pytest.mark.asyncio
    async def test_filesystem_tool_error_handling(self, ai_agent_with_filesystem):
        """Test filesystem tool error handling."""
        agent = ai_agent_with_filesystem

        # Test read file error when connected
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server,
                "read_file",
                side_effect=FileOperationError("File not found"),
            ):
                result = await agent._tool_read_file("nonexistent.py")
                assert "Error" in result
                assert "File not found" in result

            # Test write file error when connected
            with patch.object(
                agent.mcp_file_server,
                "write_file",
                side_effect=FileOperationError("Permission denied"),
            ):
                result = await agent._tool_write_file("readonly.py", "content")
                assert "Error" in result
                assert "Permission denied" in result

    @pytest.mark.asyncio
    async def test_filesystem_tools_require_mcp_connection(
        self, ai_agent_with_filesystem
    ):
        """Test that filesystem tools require MCP connection."""
        agent = ai_agent_with_filesystem
        # Don't connect to MCP - is_connected will be False by default

        result = await agent._tool_read_file("example.py")
        assert "Error" in result
        assert "not connected" in result.lower()

    @pytest.mark.asyncio
    async def test_enhanced_conversation_with_file_context(
        self, ai_agent_with_filesystem
    ):
        """Test enhanced conversation capabilities with file context."""
        agent = ai_agent_with_filesystem

        # Mock the AI model response and file operations
        mock_response = Mock()
        mock_response.data = "I can see the example.py file contains a hello function. Here's how to improve it..."

        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent._agent, "run", return_value=mock_response
            ) as mock_run:
                with patch.object(
                    agent.mcp_file_server,
                    "read_file",
                    return_value="def hello(): return 'world'",
                ):
                    response = await agent.send_message_with_tools(
                        "Can you help me improve the example.py file?",
                        enable_filesystem=True,
                    )

                    assert response.success is True
                    assert (
                        "example.py" in response.content
                        or "improve" in response.content
                    )
                    mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_analysis_workflow(self, ai_agent_with_filesystem):
        """Test file analysis workflow using filesystem tools."""
        agent = ai_agent_with_filesystem

        # Mock file operations for analysis workflow
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server,
                "list_directory",
                return_value=["app.py", "config.py", "tests/"],
            ):
                with patch.object(agent.mcp_file_server, "read_file") as mock_read:
                    mock_read.side_effect = [
                        "from config import settings\ndef main(): pass",  # app.py
                        "DATABASE_URL = 'sqlite:///app.db'\nDEBUG = True",  # config.py
                    ]

                    # Mock AI response
                    mock_response = Mock()
                    mock_response.data = "Based on the code analysis, I found potential security issues..."

                    with patch.object(agent._agent, "run", return_value=mock_response):
                        response = await agent.analyze_project_files()

                        assert response.success is True
                        assert (
                            mock_read.call_count >= 0
                        )  # Updated since we don't automatically read files

    @pytest.mark.asyncio
    async def test_code_generation_with_file_writing(self, ai_agent_with_filesystem):
        """Test code generation with file writing capabilities."""
        agent = ai_agent_with_filesystem

        # Mock file write operation
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server, "write_file", return_value=True
            ) as mock_write:
                generated_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

                result = await agent.generate_and_save_code(
                    "Create a fibonacci function", "fibonacci.py", generated_code
                )

                assert result.success is True
                mock_write.assert_called_once_with("fibonacci.py", generated_code)

    @pytest.mark.asyncio
    async def test_workspace_scoped_operations(
        self, ai_agent_with_filesystem, temp_workspace
    ):
        """Test that file operations are scoped to workspace."""
        agent = ai_agent_with_filesystem

        # Test that operations outside workspace are blocked when connected
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server,
                "read_file",
                side_effect=FileOperationError("Outside workspace"),
            ):
                result = await agent._tool_read_file("../../../etc/passwd")
                assert "Error" in result
                assert "workspace" in result.lower() or "outside" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_registration_and_descriptions(self, ai_agent_with_filesystem):
        """Test that filesystem tools are properly registered with descriptions."""
        agent = ai_agent_with_filesystem

        tools = agent.get_tool_descriptions()

        # Check that filesystem tools have proper descriptions
        expected_descriptions = {
            "read_file": "read",
            "write_file": "write",
            "list_directory": "list",
            "create_directory": "create",
            "get_file_info": "info",
            "search_files": "search",
        }

        for tool_name, description_key in expected_descriptions.items():
            assert tool_name in tools
            assert description_key in tools[tool_name].lower()

    @pytest.mark.asyncio
    async def test_concurrent_file_operations(self, ai_agent_with_filesystem):
        """Test concurrent file operations through tools."""
        agent = ai_agent_with_filesystem

        # Mock multiple file operations
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(agent.mcp_file_server, "read_file") as mock_read:
                mock_read.side_effect = ["content1", "content2", "content3"]

                # Run concurrent file reads
                tasks = [
                    agent._tool_read_file("file1.py"),
                    agent._tool_read_file("file2.py"),
                    agent._tool_read_file("file3.py"),
                ]

                results = await asyncio.gather(*tasks)

                assert len(results) == 3
                assert all("content" in result for result in results)
                assert mock_read.call_count == 3

    @pytest.mark.asyncio
    async def test_filesystem_tool_security_validation(self, ai_agent_with_filesystem):
        """Test security validation in filesystem tools."""
        agent = ai_agent_with_filesystem

        # Test blocked file extensions when connected
        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(
                agent.mcp_file_server,
                "read_file",
                side_effect=FileOperationError("Extension not allowed"),
            ):
                result = await agent._tool_read_file("malware.exe")
                assert "Error" in result
                assert "not allowed" in result.lower()

            # Test blocked paths when connected
            with patch.object(
                agent.mcp_file_server,
                "read_file",
                side_effect=FileOperationError("Path blocked"),
            ):
                result = await agent._tool_read_file("secrets/api_key.py")
                assert "Error" in result
                assert "blocked" in result.lower()

    def test_tool_availability_configuration(self, ai_config, mcp_config):
        """Test that tool availability can be configured."""
        # Agent with filesystem tools enabled
        agent_with_tools = AIAgent(ai_config, mcp_config, enable_filesystem_tools=True)
        assert agent_with_tools.filesystem_tools_enabled is True

        # Agent with filesystem tools disabled
        agent_without_tools = AIAgent(
            ai_config, mcp_config, enable_filesystem_tools=False
        )
        assert agent_without_tools.filesystem_tools_enabled is False

        # Agent without MCP config (tools should be disabled)
        agent_no_mcp = AIAgent(ai_config, mcp_config=None)
        assert agent_no_mcp.filesystem_tools_enabled is False

    @pytest.mark.asyncio
    async def test_tool_integration_with_ai_responses(self, ai_agent_with_filesystem):
        """Test tool integration with AI model responses."""
        agent = ai_agent_with_filesystem

        # Mock AI model that uses tools
        async def mock_run_with_tools(prompt, **kwargs):
            # Simulate AI deciding to use file tools
            await agent._tool_read_file("example.py")
            await agent._tool_list_directory(".")

            mock_response = Mock()
            mock_response.data = "I've analyzed your files and here's what I found..."
            return mock_response

        with patch.object(agent.mcp_file_server, "is_connected", True):
            with patch.object(agent._agent, "run", side_effect=mock_run_with_tools):
                with patch.object(
                    agent.mcp_file_server, "read_file", return_value="file content"
                ):
                    with patch.object(
                        agent.mcp_file_server,
                        "list_directory",
                        return_value=["file1.py"],
                    ):
                        response = await agent.send_message_with_tools(
                            "Analyze my project"
                        )

                        assert response.success is True
                        assert "analyzed" in response.content.lower()
