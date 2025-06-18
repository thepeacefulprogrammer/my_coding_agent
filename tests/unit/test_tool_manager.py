"""Tests for ToolManager focused tool management functionality."""

import pytest

from my_coding_agent.core.ai_services.tool_manager import ToolManager


class TestToolManager:
    """Test cases for ToolManager."""

    @pytest.fixture
    def tool_manager(self):
        """Create a fresh ToolManager instance."""
        return ToolManager()

    def test_initialization(self, tool_manager):
        """Test ToolManager initialization."""
        assert tool_manager.get_available_tools() == []
        assert tool_manager.get_tool_descriptions() == {}
        assert not tool_manager._filesystem_tools_enabled
        assert not tool_manager._mcp_tools_enabled
        assert not tool_manager._project_history_enabled
        assert not tool_manager._memory_enabled

    def test_enable_filesystem_tools(self, tool_manager):
        """Test enabling filesystem tools."""
        tool_manager.enable_filesystem_tools(True)

        tools = tool_manager.get_available_tools()
        expected_tools = [
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "get_file_info",
            "search_files",
        ]

        assert len(tools) == 6
        for tool in expected_tools:
            assert tool in tools
            assert tool_manager.is_tool_available(tool)

        descriptions = tool_manager.get_tool_descriptions()
        assert len(descriptions) == 6
        assert "Read the contents of a file" in descriptions["read_file"]

    def test_enable_mcp_tools(self, tool_manager):
        """Test enabling MCP tools."""
        tool_manager.enable_mcp_tools(True)

        tools = tool_manager.get_available_tools()
        expected_tools = [
            "get_mcp_server_status",
            "list_mcp_servers",
            "connect_mcp_server",
            "disconnect_mcp_server",
        ]

        assert len(tools) == 4
        for tool in expected_tools:
            assert tool in tools
            assert tool_manager.is_tool_available(tool)

    def test_enable_project_history_tools_requires_memory(self, tool_manager):
        """Test that project history tools require memory to be enabled."""
        # Enable project history without memory
        tool_manager.enable_project_history_tools(True)

        # Should not add tools without memory enabled
        assert len(tool_manager.get_available_tools()) == 0

        # Enable memory
        tool_manager.enable_memory_tools(True)

        # Now should have project history tools
        tools = tool_manager.get_available_tools()
        expected_tools = [
            "get_file_project_history",
            "search_project_history",
            "get_recent_project_changes",
            "get_project_timeline",
        ]

        assert len(tools) == 4
        for tool in expected_tools:
            assert tool in tools

    def test_enable_memory_tools_alone(self, tool_manager):
        """Test enabling memory tools alone doesn't add project history."""
        tool_manager.enable_memory_tools(True)

        # Memory alone shouldn't add any tools
        assert len(tool_manager.get_available_tools()) == 0

        # Need to also enable project history
        tool_manager.enable_project_history_tools(True)

        # Now should have tools
        assert len(tool_manager.get_available_tools()) == 4

    def test_disable_tools(self, tool_manager):
        """Test disabling tools removes them."""
        # Enable all tools
        tool_manager.enable_filesystem_tools(True)
        tool_manager.enable_mcp_tools(True)
        tool_manager.enable_memory_tools(True)
        tool_manager.enable_project_history_tools(True)

        # Should have all tools
        assert len(tool_manager.get_available_tools()) == 14  # 6 + 4 + 4

        # Disable filesystem tools
        tool_manager.enable_filesystem_tools(False)
        assert len(tool_manager.get_available_tools()) == 8  # 4 + 4
        assert not tool_manager.is_tool_available("read_file")

        # Disable MCP tools
        tool_manager.enable_mcp_tools(False)
        assert len(tool_manager.get_available_tools()) == 4  # Just project history
        assert not tool_manager.is_tool_available("get_mcp_server_status")

    def test_get_tool_categories(self, tool_manager):
        """Test getting tools organized by category."""
        # Initially no categories
        assert tool_manager.get_tool_categories() == {}

        # Enable different tool types
        tool_manager.enable_filesystem_tools(True)
        tool_manager.enable_mcp_tools(True)
        tool_manager.enable_memory_tools(True)
        tool_manager.enable_project_history_tools(True)

        categories = tool_manager.get_tool_categories()
        assert len(categories) == 3
        assert "filesystem" in categories
        assert "mcp" in categories
        assert "project_history" in categories

    def test_get_stats(self, tool_manager):
        """Test getting tool manager statistics."""
        # Initial stats
        stats = tool_manager.get_stats()
        expected_stats = {
            "total_tools": 0,
            "filesystem_enabled": False,
            "mcp_enabled": False,
            "project_history_enabled": False,
            "memory_enabled": False,
            "categories": 0,
        }
        assert stats == expected_stats

    def test_validate_tool_configuration(self, tool_manager):
        """Test tool configuration validation."""
        # No tools enabled
        issues = tool_manager.validate_tool_configuration()
        assert len(issues) == 2
        assert "No tool categories are enabled" in issues
        assert "No tools are currently available" in issues

        # Project history without memory
        tool_manager.enable_project_history_tools(True)
        issues = tool_manager.validate_tool_configuration()
        assert "Project history tools require memory to be enabled" in issues

        # Enable memory
        tool_manager.enable_memory_tools(True)
        issues = tool_manager.validate_tool_configuration()
        # Should have no issues now
        assert len(issues) == 0

    def test_is_tool_available(self, tool_manager):
        """Test checking if specific tools are available."""
        assert not tool_manager.is_tool_available("read_file")
        assert not tool_manager.is_tool_available("nonexistent_tool")

        tool_manager.enable_filesystem_tools(True)
        assert tool_manager.is_tool_available("read_file")
        assert not tool_manager.is_tool_available("get_mcp_server_status")

        tool_manager.enable_mcp_tools(True)
        assert tool_manager.is_tool_available("get_mcp_server_status")

    def test_reset(self, tool_manager):
        """Test resetting the tool manager."""
        # Enable everything
        tool_manager.enable_filesystem_tools(True)
        tool_manager.enable_mcp_tools(True)
        tool_manager.enable_memory_tools(True)
        tool_manager.enable_project_history_tools(True)

        # Verify tools are enabled
        assert len(tool_manager.get_available_tools()) > 0
        assert tool_manager._filesystem_tools_enabled

        # Reset
        tool_manager.reset()

        # Verify everything is reset
        assert len(tool_manager.get_available_tools()) == 0
        assert not tool_manager._filesystem_tools_enabled

    def test_get_descriptions_returns_copy(self, tool_manager):
        """Test that get_tool_descriptions returns a copy, not reference."""
        tool_manager.enable_filesystem_tools(True)

        descriptions1 = tool_manager.get_tool_descriptions()
        descriptions2 = tool_manager.get_tool_descriptions()

        # Should be equal but not the same object
        assert descriptions1 == descriptions2
        assert descriptions1 is not descriptions2

        # Modifying one shouldn't affect the other
        descriptions1["test"] = "test_value"
        descriptions2 = tool_manager.get_tool_descriptions()
        assert "test" not in descriptions2

    def test_get_available_tools_returns_copy(self, tool_manager):
        """Test that get_available_tools returns a copy, not reference."""
        tool_manager.enable_filesystem_tools(True)

        tools1 = tool_manager.get_available_tools()
        tools2 = tool_manager.get_available_tools()

        # Should be equal but not the same object
        assert tools1 == tools2
        assert tools1 is not tools2

        # Modifying one shouldn't affect the other
        tools1.append("test_tool")
        tools2 = tool_manager.get_available_tools()
        assert "test_tool" not in tools2

    def test_multiple_enable_calls(self, tool_manager):
        """Test that multiple enable calls work correctly."""
        # Enable filesystem tools multiple times
        tool_manager.enable_filesystem_tools(True)
        initial_count = len(tool_manager.get_available_tools())

        tool_manager.enable_filesystem_tools(True)
        assert len(tool_manager.get_available_tools()) == initial_count

        # Disable and re-enable
        tool_manager.enable_filesystem_tools(False)
        assert len(tool_manager.get_available_tools()) == 0

        tool_manager.enable_filesystem_tools(True)
        assert len(tool_manager.get_available_tools()) == initial_count

    def test_tool_categories_with_partial_enablement(self, tool_manager):
        """Test tool categories with only some tools enabled."""
        # Enable only filesystem tools
        tool_manager.enable_filesystem_tools(True)

        categories = tool_manager.get_tool_categories()
        assert len(categories) == 1
        assert "filesystem" in categories
        assert "mcp" not in categories
        assert "project_history" not in categories

        # Add MCP tools
        tool_manager.enable_mcp_tools(True)
        categories = tool_manager.get_tool_categories()
        assert len(categories) == 2
        assert "filesystem" in categories
        assert "mcp" in categories
        assert "project_history" not in categories
