"""Tool Registration and Management Service.

This service handles all tool registration and management functionality for the AI Agent,
including filesystem tools, MCP tools, status tools, and environment tools.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToolRegistrationService:
    """Service for registering and managing AI agent tools."""

    def __init__(
        self,
        filesystem_tools_enabled: bool = False,
        mcp_tools_enabled: bool = False,
        mcp_file_server=None,
        mcp_registry=None,
    ) -> None:
        """Initialize the ToolRegistrationService.

        Args:
            filesystem_tools_enabled: Whether to enable filesystem tools
            mcp_tools_enabled: Whether to enable MCP tools
            mcp_file_server: MCP file server instance
            mcp_registry: MCP server registry instance
        """
        self.filesystem_tools_enabled = filesystem_tools_enabled
        self.mcp_tools_enabled = mcp_tools_enabled
        self.mcp_file_server = mcp_file_server
        self.mcp_registry = mcp_registry

        # Tool tracking
        self._mcp_tool_prefix = "mcp_"
        self._mcp_status_tool_registered = False
        self._environment_tool_registered = False

        logger.info(
            f"ToolRegistrationService initialized - "
            f"filesystem: {filesystem_tools_enabled}, "
            f"mcp: {mcp_tools_enabled}"
        )

    def register_all_tools(self, agent) -> None:
        """Register all enabled tools with the agent.

        Args:
            agent: The Pydantic AI agent instance
        """
        # Register filesystem tools
        if self.filesystem_tools_enabled:
            self.register_filesystem_tools(agent)

        # Register MCP tools
        if self.mcp_tools_enabled:
            self.register_mcp_tools(agent)
            self.register_mcp_status_tool(agent)

        # Always register environment tool
        self.register_environment_tool(agent)

    def register_filesystem_tools(self, agent) -> None:
        """Register filesystem tools with the agent.

        Args:
            agent: The Pydantic AI agent instance
        """
        if not self.filesystem_tools_enabled:
            return

        try:
            # Read file tool
            @agent.tool_plain
            async def read_file(file_path: str) -> str:
                """Read the contents of a file in the workspace.

                Args:
                    file_path: Relative path to the file

                Returns:
                    File contents as string
                """
                return await self._tool_read_file(file_path)

            # Write file tool
            @agent.tool_plain
            async def write_file(file_path: str, content: str) -> str:
                """Write content to a file in the workspace.

                Args:
                    file_path: Relative path to the file
                    content: Content to write

                Returns:
                    Success message or error
                """
                return await self._tool_write_file(file_path, content)

            # List directory tool
            @agent.tool_plain
            async def list_directory(dir_path: str = ".") -> str:
                """List contents of a directory in the workspace.

                Args:
                    dir_path: Relative path to the directory (default: current directory)

                Returns:
                    Directory contents as formatted string
                """
                return await self._tool_list_directory(dir_path)

            # Create directory tool
            @agent.tool_plain
            async def create_directory(dir_path: str) -> str:
                """Create a new directory in the workspace.

                Args:
                    dir_path: Relative path to the directory to create

                Returns:
                    Success message or error
                """
                return await self._tool_create_directory(dir_path)

            # Get file info tool
            @agent.tool_plain
            async def get_file_info(file_path: str) -> str:
                """Get information about a file in the workspace.

                Args:
                    file_path: Relative path to the file

                Returns:
                    File information as formatted string
                """
                return await self._tool_get_file_info(file_path)

            # Search files tool
            @agent.tool_plain
            async def search_files(pattern: str, dir_path: str = ".") -> str:
                """Search for files matching a pattern in the workspace.

                Args:
                    pattern: Search pattern (e.g., "*.py")
                    dir_path: Directory to search in (default: current directory)

                Returns:
                    List of matching files as formatted string
                """
                return await self._tool_search_files(pattern, dir_path)

            logger.info("Filesystem tools registered successfully")

        except Exception as e:
            logger.error(f"Failed to register filesystem tools: {e}")
            self.filesystem_tools_enabled = False

    def register_mcp_tools(self, agent) -> None:
        """Register MCP tools with the agent.

        Args:
            agent: The Pydantic AI agent instance
        """
        if not self.mcp_tools_enabled or not self.mcp_registry:
            return

        try:
            filesystem_tools = set()
            if self.filesystem_tools_enabled:
                filesystem_tools = {
                    "read_file",
                    "write_file",
                    "list_directory",
                    "create_directory",
                    "get_file_info",
                    "search_files",
                }

            all_tools = self.mcp_registry.get_all_tools()
            registered_count = 0
            registered_tool_names = set()

            # First pass: collect all tool names to identify conflicts
            tool_name_counts = {}
            for _server_name, tools in all_tools.items():
                for tool in tools:
                    tool_name_counts[tool.name] = tool_name_counts.get(tool.name, 0) + 1

            for server_name, tools in all_tools.items():
                for tool in tools:
                    tool_name = tool.name
                    original_name = tool_name

                    # Handle name conflicts with filesystem tools
                    if tool_name in filesystem_tools:
                        tool_name = f"{self._mcp_tool_prefix}{tool.name}"

                    # Handle name conflicts with other MCP tools
                    if tool_name_counts.get(original_name, 0) > 1:
                        tool_name = f"{server_name}_{tool.name}"
                        logger.info(
                            f"Tool name conflict resolved: '{original_name}' -> '{tool_name}' (from {server_name})"
                        )

                    # If still conflicts, add a counter
                    counter = 1
                    base_tool_name = tool_name
                    while tool_name in registered_tool_names:
                        tool_name = f"{base_tool_name}_{counter}"
                        counter += 1

                    # Create the tool function dynamically
                    self._create_mcp_tool_function(
                        agent,
                        tool_name,
                        original_name,
                        tool.description,
                        tool.input_schema,
                        server_name,
                    )
                    registered_tool_names.add(tool_name)
                    registered_count += 1

            logger.info(f"Registered {registered_count} MCP tools successfully")

        except Exception as e:
            logger.error(f"Failed to register MCP tools: {e}")
            import traceback

            logger.debug(
                f"MCP tool registration error traceback: {traceback.format_exc()}"
            )
            self.mcp_tools_enabled = False

    def register_mcp_status_tool(self, agent) -> None:
        """Register MCP server status tool with the agent.

        Args:
            agent: The Pydantic AI agent instance
        """
        if self._mcp_status_tool_registered:
            logger.debug("MCP status tool already registered, skipping")
            return

        try:

            @agent.tool_plain
            async def internal_mcp_server_status_check() -> str:
                """Get the status of all MCP servers and their available tools.

                Returns:
                    Formatted string with server status information
                """
                return await self._tool_get_mcp_server_status()

            self._mcp_status_tool_registered = True
            logger.info("MCP server status tool registered successfully")

        except Exception as e:
            logger.error(f"Failed to register MCP server status tool: {e}")

    def register_environment_tool(self, agent) -> None:
        """Register environment variable tool with the agent.

        Args:
            agent: The Pydantic AI agent instance
        """
        if self._environment_tool_registered:
            logger.debug("Environment tool already registered, skipping")
            return

        try:

            @agent.tool_plain
            async def internal_get_environment_variable(variable_name: str) -> str:
                """Get the value of an environment variable.

                Args:
                    variable_name: Name of the environment variable

                Returns:
                    Environment variable value or error message
                """
                return await self._tool_get_environment_variable(variable_name)

            self._environment_tool_registered = True
            logger.info("Environment tool registered successfully")

        except Exception as e:
            logger.error(f"Failed to register environment tool: {e}")

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names.

        Returns:
            List of tool names
        """
        tools = []

        # Add filesystem tools
        if self.filesystem_tools_enabled:
            tools.extend(
                [
                    "read_file",
                    "write_file",
                    "list_directory",
                    "create_directory",
                    "get_file_info",
                    "search_files",
                ]
            )

        # Add MCP tools
        if self.mcp_tools_enabled and self.mcp_registry:
            mcp_tools = self._get_mcp_tools()
            tools.extend(mcp_tools)

        # Add status and environment tools
        if self._mcp_status_tool_registered:
            tools.append("get_mcp_server_status")
        if self._environment_tool_registered:
            tools.append("get_environment_variable")

        return tools

    def get_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions of available tools.

        Returns:
            Dictionary mapping tool names to descriptions
        """
        descriptions = {}

        # Add filesystem tool descriptions
        if self.filesystem_tools_enabled:
            descriptions.update(
                {
                    "read_file": "Read the contents of a file in the workspace",
                    "write_file": "Write content to a file in the workspace",
                    "list_directory": "List contents of a directory in the workspace",
                    "create_directory": "Create a new directory in the workspace",
                    "get_file_info": "Get information about a file in the workspace",
                    "search_files": "Search for files matching a pattern in the workspace",
                }
            )

        # Add MCP tool descriptions
        if self.mcp_tools_enabled and self.mcp_registry:
            mcp_descriptions = self._get_mcp_tool_descriptions()
            descriptions.update(mcp_descriptions)

        # Add status and environment tool descriptions
        if self._mcp_status_tool_registered:
            descriptions["get_mcp_server_status"] = (
                "Get the status of all MCP servers and their available tools"
            )
        if self._environment_tool_registered:
            descriptions["get_environment_variable"] = (
                "Get the value of an environment variable"
            )

        return descriptions

    def _get_mcp_tools(self) -> list[str]:
        """Get list of available MCP tool names with conflict resolution.

        Returns:
            List of MCP tool names, prefixed if there are conflicts with filesystem tools
        """
        if not self.mcp_registry:
            return []

        filesystem_tools = set()
        if self.filesystem_tools_enabled:
            filesystem_tools = {
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "get_file_info",
                "search_files",
            }

        mcp_tools = []
        all_tools = self.mcp_registry.get_all_tools()

        for _server_name, tools in all_tools.items():
            for tool in tools:
                tool_name = tool.name

                # Handle name conflicts by prefixing
                if tool_name in filesystem_tools:
                    tool_name = f"{self._mcp_tool_prefix}{tool.name}"

                mcp_tools.append(tool_name)

        return mcp_tools

    def _get_mcp_tool_descriptions(self) -> dict[str, str]:
        """Get descriptions for MCP tools with conflict resolution.

        Returns:
            Dictionary mapping MCP tool names to descriptions
        """
        if not self.mcp_registry:
            return {}

        filesystem_tools = set()
        if self.filesystem_tools_enabled:
            filesystem_tools = {
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "get_file_info",
                "search_files",
            }

        descriptions = {}
        all_tools = self.mcp_registry.get_all_tools()

        for server_name, tools in all_tools.items():
            for tool in tools:
                tool_name = tool.name

                # Handle name conflicts by prefixing
                if tool_name in filesystem_tools:
                    tool_name = f"{self._mcp_tool_prefix}{tool.name}"

                # Add server info to description for clarity
                description = f"{tool.description} (from {server_name})"
                descriptions[tool_name] = description

        return descriptions

    def _create_mcp_tool_function(
        self,
        agent,
        tool_name: str,
        original_name: str,
        description: str,
        input_schema: dict[str, Any],
        server_name: str,
    ) -> None:
        """Create a dynamic tool function for an MCP tool.

        Args:
            agent: The Pydantic AI agent instance
            tool_name: Final tool name (with conflict resolution)
            original_name: Original tool name from MCP server
            description: Tool description
            input_schema: Tool input schema
            server_name: Name of the MCP server
        """

        async def mcp_tool_wrapper(**kwargs) -> str:
            """Dynamic wrapper for MCP tool calls."""
            try:
                # Validate arguments against schema
                properties = input_schema.get("properties", {})
                required = input_schema.get("required", [])

                # Check required arguments
                for req_arg in required:
                    if req_arg not in kwargs:
                        return f"Error: Missing required argument '{req_arg}'"

                # Filter and validate arguments
                validated_args = {}
                for arg_name, arg_value in kwargs.items():
                    if arg_name in properties:
                        validated_args[arg_name] = arg_value
                    else:
                        logger.warning(
                            f"Unknown argument '{arg_name}' for tool '{tool_name}'"
                        )

                # Call the MCP tool
                result = await self._call_mcp_tool(
                    original_name, validated_args, server_name
                )
                return result

            except Exception as e:
                error_msg = f"Error calling MCP tool '{tool_name}': {e}"
                logger.error(error_msg)
                return error_msg

        # Register the tool with proper type hints and description
        agent.tool_plain(mcp_tool_wrapper, name=tool_name, description=description)

    # Filesystem Tool Implementation Methods
    async def _tool_read_file(self, file_path: str) -> str:
        """Internal implementation of read_file tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            # Handle both async and sync mocks/implementations
            if callable(self.mcp_file_server.read_file):
                content = self.mcp_file_server.read_file(file_path)
                # If it's a coroutine, await it
                if hasattr(content, "__await__"):
                    content = await content
            else:
                content = await self.mcp_file_server.read_file(file_path)
            return content

        except Exception as e:
            logger.warning(f"File read error for {file_path}: {e}")
            return f"Error reading file: {e}"

    async def _tool_write_file(self, file_path: str, content: str) -> str:
        """Internal implementation of write_file tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            # Handle both async and sync mocks/implementations
            if callable(self.mcp_file_server.write_file):
                success = self.mcp_file_server.write_file(file_path, content)
                # If it's a coroutine, await it
                if hasattr(success, "__await__"):
                    success = await success
            else:
                success = await self.mcp_file_server.write_file(file_path, content)

            if success:
                return "File written successfully"
            else:
                return "Error: Failed to write file"

        except Exception as e:
            logger.warning(f"File write error for {file_path}: {e}")
            return f"Error writing file: {e}"

    async def _tool_list_directory(self, dir_path: str = ".") -> str:
        """Internal implementation of list_directory tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            # Handle both async and sync mocks/implementations
            if callable(self.mcp_file_server.list_directory):
                entries = self.mcp_file_server.list_directory(dir_path)
                # If it's a coroutine, await it
                if hasattr(entries, "__await__"):
                    entries = await entries
            else:
                entries = await self.mcp_file_server.list_directory(dir_path)

            if not entries:
                return f"Directory '{dir_path}' is empty or does not exist"

            formatted_entries = []
            for entry in entries:
                entry_type = "📁" if entry.get("type") == "directory" else "📄"
                name = entry.get("name", "unknown")
                size = entry.get("size", "")
                size_str = f" ({size} bytes)" if size else ""
                formatted_entries.append(f"{entry_type} {name}{size_str}")

            return f"Contents of '{dir_path}':\n" + "\n".join(formatted_entries)

        except Exception as e:
            logger.warning(f"Directory list error for {dir_path}: {e}")
            return f"Error listing directory: {e}"

    async def _tool_create_directory(self, dir_path: str) -> str:
        """Internal implementation of create_directory tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            # Handle both async and sync mocks/implementations
            if callable(self.mcp_file_server.create_directory):
                success = self.mcp_file_server.create_directory(dir_path)
                # If it's a coroutine, await it
                if hasattr(success, "__await__"):
                    success = await success
            else:
                success = await self.mcp_file_server.create_directory(dir_path)

            if success:
                return f"Directory '{dir_path}' created successfully"
            else:
                return f"Error: Failed to create directory '{dir_path}'"

        except Exception as e:
            logger.warning(f"Directory creation error for {dir_path}: {e}")
            return f"Error creating directory: {e}"

    async def _tool_get_file_info(self, file_path: str) -> str:
        """Internal implementation of get_file_info tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            # Handle both async and sync mocks/implementations
            if callable(self.mcp_file_server.get_file_info):
                info = self.mcp_file_server.get_file_info(file_path)
                # If it's a coroutine, await it
                if hasattr(info, "__await__"):
                    info = await info
            else:
                info = await self.mcp_file_server.get_file_info(file_path)

            if not info:
                return f"File '{file_path}' not found or inaccessible"

            formatted_info = [f"File Information for '{file_path}':"]
            formatted_info.append("-" * 40)

            for key, value in info.items():
                formatted_info.append(f"{key.title()}: {value}")

            return "\n".join(formatted_info)

        except Exception as e:
            logger.warning(f"File info error for {file_path}: {e}")
            return f"Error getting file info: {e}"

    async def _tool_search_files(self, pattern: str, dir_path: str = ".") -> str:
        """Internal implementation of search_files tool."""
        try:
            if not self.mcp_file_server or not self.mcp_file_server.is_connected:
                return "Error: MCP file server not connected. Please connect first."

            # Handle both async and sync mocks/implementations
            if callable(self.mcp_file_server.search_files):
                files = self.mcp_file_server.search_files(pattern, dir_path)
                # If it's a coroutine, await it
                if hasattr(files, "__await__"):
                    files = await files
            else:
                files = await self.mcp_file_server.search_files(pattern, dir_path)

            if not files:
                return f"No files matching pattern '{pattern}' found in '{dir_path}'"

            return f"Files matching '{pattern}' in '{dir_path}':\n" + "\n".join(
                f"📄 {file}" for file in files
            )

        except Exception as e:
            logger.warning(f"File search error for pattern {pattern}: {e}")
            return f"Error searching files: {e}"

    # MCP Tool Implementation Methods
    async def _call_mcp_tool(
        self, tool_name: str, arguments: dict[str, Any], server_name: str | None = None
    ) -> str:
        """Call an MCP tool with the given arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_name: Optional server name for direct routing

        Returns:
            Tool result as string
        """
        try:
            if not self.mcp_registry:
                return "Error: MCP registry not available"

            # Handle both async and sync mocks/implementations
            if callable(self.mcp_registry.call_tool):
                result = self.mcp_registry.call_tool(tool_name, arguments, server_name)
                # If it's a coroutine, await it
                if hasattr(result, "__await__"):
                    result = await result
            else:
                result = await self.mcp_registry.call_tool(
                    tool_name, arguments, server_name
                )

            return (
                str(result)
                if result is not None
                else "Tool executed successfully (no output)"
            )

        except Exception as e:
            logger.error(f"Error calling MCP tool '{tool_name}': {e}")
            return f"Error: {e}"

    async def _tool_get_mcp_server_status(self) -> str:
        """Internal implementation of MCP server status tool."""
        try:
            if not self.mcp_registry:
                return "MCP Registry: Not initialized"

            status = self.mcp_registry.get_server_status()

            if not status:
                return "No MCP servers registered"

            formatted_status = ["MCP Server Status:"]
            formatted_status.append("=" * 50)

            for server_name, server_status in status.items():
                formatted_status.append(f"\nServer: {server_name}")
                formatted_status.append(
                    f"  Status: {server_status.get('status', 'Unknown')}"
                )
                formatted_status.append(
                    f"  Connected: {server_status.get('connected', False)}"
                )

                tools = server_status.get("tools", [])
                formatted_status.append(f"  Tools: {len(tools)} available")

                if tools:
                    for tool in tools[:5]:  # Show first 5 tools
                        formatted_status.append(f"    - {tool}")
                    if len(tools) > 5:
                        formatted_status.append(f"    ... and {len(tools) - 5} more")

            return "\n".join(formatted_status)

        except Exception as e:
            logger.error(f"Error getting MCP server status: {e}")
            return f"Error retrieving MCP server status: {e}"

    async def _tool_get_environment_variable(self, variable_name: str) -> str:
        """Internal implementation of environment variable tool."""
        try:
            import os

            value = os.environ.get(variable_name)

            if value is None:
                return f"Environment variable '{variable_name}' is not set"

            # Mask sensitive variables
            sensitive_vars = ["api_key", "password", "secret", "token", "key"]
            if any(sensitive in variable_name.lower() for sensitive in sensitive_vars):
                return f"Environment variable '{variable_name}' is set (value masked for security)"

            return f"Environment variable '{variable_name}' = '{value}'"

        except Exception as e:
            logger.error(f"Error getting environment variable '{variable_name}': {e}")
            return f"Error: {e}"
