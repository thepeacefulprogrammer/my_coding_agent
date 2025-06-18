"""Tool Manager for AI Services.

This module handles tool registration, management, and integration
for the AI services, separated from the core AI communication logic.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToolManager:
    """Manages tool registration and availability for AI services."""

    def __init__(self):
        """Initialize the tool manager."""
        self._available_tools: list[str] = []
        self._tool_descriptions: dict[str, str] = {}
        self._filesystem_tools_enabled = False
        self._mcp_tools_enabled = False
        self._project_history_enabled = False
        self._memory_enabled = False

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def enable_filesystem_tools(self, enabled: bool = True) -> None:
        """Enable or disable filesystem tools.

        Args:
            enabled: Whether to enable filesystem tools
        """
        self._filesystem_tools_enabled = enabled
        self._update_available_tools()
        self.logger.info(f"Filesystem tools {'enabled' if enabled else 'disabled'}")

    def enable_mcp_tools(self, enabled: bool = True) -> None:
        """Enable or disable MCP tools.

        Args:
            enabled: Whether to enable MCP tools
        """
        self._mcp_tools_enabled = enabled
        self._update_available_tools()
        self.logger.info(f"MCP tools {'enabled' if enabled else 'disabled'}")

    def enable_project_history_tools(self, enabled: bool = True) -> None:
        """Enable or disable project history tools.

        Args:
            enabled: Whether to enable project history tools
        """
        self._project_history_enabled = enabled
        self._update_available_tools()
        self.logger.info(
            f"Project history tools {'enabled' if enabled else 'disabled'}"
        )

    def enable_memory_tools(self, enabled: bool = True) -> None:
        """Enable or disable memory-aware tools.

        Args:
            enabled: Whether to enable memory tools
        """
        self._memory_enabled = enabled
        self._update_available_tools()
        self.logger.info(f"Memory tools {'enabled' if enabled else 'disabled'}")

    def _update_available_tools(self) -> None:
        """Update the list of available tools based on enabled features."""
        self._available_tools.clear()
        self._tool_descriptions.clear()

        # Add filesystem tools
        if self._filesystem_tools_enabled:
            self._add_filesystem_tools()

        # Add MCP tools
        if self._mcp_tools_enabled:
            self._add_mcp_tools()

        # Add project history tools
        if self._project_history_enabled and self._memory_enabled:
            self._add_project_history_tools()

        self.logger.debug(
            f"Available tools updated: {len(self._available_tools)} tools"
        )

    def _add_filesystem_tools(self) -> None:
        """Add filesystem tools to the available tools."""
        filesystem_tools = {
            "read_file": "Read the contents of a file in the workspace",
            "write_file": "Write content to a file in the workspace",
            "list_directory": "List contents of a directory in the workspace",
            "create_directory": "Create a new directory in the workspace",
            "get_file_info": "Get information about a file in the workspace",
            "search_files": "Search for files matching a pattern in the workspace",
        }

        self._available_tools.extend(filesystem_tools.keys())
        self._tool_descriptions.update(filesystem_tools)

    def _add_mcp_tools(self) -> None:
        """Add MCP tools to the available tools."""
        # Base MCP management tools
        mcp_tools = {
            "get_mcp_server_status": "Get the status of all MCP servers and their available tools",
            "list_mcp_servers": "List all configured MCP servers",
            "connect_mcp_server": "Connect to a specific MCP server",
            "disconnect_mcp_server": "Disconnect from a specific MCP server",
        }

        self._available_tools.extend(mcp_tools.keys())
        self._tool_descriptions.update(mcp_tools)

    def _add_project_history_tools(self) -> None:
        """Add project history tools to the available tools."""
        history_tools = {
            "get_file_project_history": "Get project history and evolution for a specific file",
            "search_project_history": "Search project history using semantic and text search",
            "get_recent_project_changes": "Get recent project changes within specified time period",
            "get_project_timeline": "Get project timeline showing chronological development",
        }

        self._available_tools.extend(history_tools.keys())
        self._tool_descriptions.update(history_tools)

    def get_available_tools(self) -> list[str]:
        """Get list of currently available tool names.

        Returns:
            List of tool names
        """
        return self._available_tools.copy()

    def get_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions of currently available tools.

        Returns:
            Dictionary mapping tool names to descriptions
        """
        return self._tool_descriptions.copy()

    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is available, False otherwise
        """
        return tool_name in self._available_tools

    def get_tool_categories(self) -> dict[str, list[str]]:
        """Get tools organized by category.

        Returns:
            Dictionary mapping category names to lists of tool names
        """
        categories = {}

        if self._filesystem_tools_enabled:
            categories["filesystem"] = [
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "get_file_info",
                "search_files",
            ]

        if self._mcp_tools_enabled:
            categories["mcp"] = [
                "get_mcp_server_status",
                "list_mcp_servers",
                "connect_mcp_server",
                "disconnect_mcp_server",
            ]

        if self._project_history_enabled and self._memory_enabled:
            categories["project_history"] = [
                "get_file_project_history",
                "search_project_history",
                "get_recent_project_changes",
                "get_project_timeline",
            ]

        return categories

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the tool manager.

        Returns:
            Dictionary with tool manager statistics
        """
        return {
            "total_tools": len(self._available_tools),
            "filesystem_enabled": self._filesystem_tools_enabled,
            "mcp_enabled": self._mcp_tools_enabled,
            "project_history_enabled": self._project_history_enabled,
            "memory_enabled": self._memory_enabled,
            "categories": len(self.get_tool_categories()),
        }

    def validate_tool_configuration(self) -> list[str]:
        """Validate the current tool configuration.

        Returns:
            List of validation warnings/issues
        """
        issues = []

        if self._project_history_enabled and not self._memory_enabled:
            issues.append("Project history tools require memory to be enabled")

        if not any(
            [
                self._filesystem_tools_enabled,
                self._mcp_tools_enabled,
                self._project_history_enabled,
            ]
        ):
            issues.append("No tool categories are enabled")

        if len(self._available_tools) == 0:
            issues.append("No tools are currently available")

        return issues

    def reset(self) -> None:
        """Reset the tool manager to initial state."""
        self._available_tools.clear()
        self._tool_descriptions.clear()
        self._filesystem_tools_enabled = False
        self._mcp_tools_enabled = False
        self._project_history_enabled = False
        self._memory_enabled = False
        self.logger.info("Tool manager reset to initial state")
