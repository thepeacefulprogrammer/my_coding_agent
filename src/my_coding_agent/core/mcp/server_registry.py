"""
MCP server registry for tracking connected servers and available tools.

This module provides a centralized registry for managing multiple MCP servers,
tracking their connection status, and providing unified access to tools
and resources across all connected servers.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .mcp_client import MCPClient, MCPError, MCPResource, MCPTool

logger = logging.getLogger(__name__)


@dataclass
class ServerStatus:
    """Status information for an MCP server."""

    name: str
    connected: bool = False
    last_ping: datetime | None = None
    last_error: str | None = None
    connection_attempts: int = 0
    tools_count: int = 0
    resources_count: int = 0
    transport_type: str = "unknown"


@dataclass
class ToolRegistry:
    """Registry entry for a tool with server information."""

    tool: MCPTool
    server_name: str
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ResourceRegistry:
    """Registry entry for a resource with server information."""

    resource: MCPResource
    server_name: str
    last_updated: datetime = field(default_factory=datetime.now)


class MCPServerRegistry:
    """
    Registry for managing multiple MCP servers and their tools/resources.

    This class provides a centralized way to:
    - Register and manage multiple MCP clients
    - Track server connection status
    - Cache and provide access to tools across all servers
    - Handle server failures and reconnection
    - Provide unified tool/resource discovery
    """

    def __init__(self):
        """Initialize the server registry."""
        self._servers: dict[str, MCPClient] = {}
        self._server_status: dict[str, ServerStatus] = {}
        self._tools_cache: dict[str, ToolRegistry] = {}  # tool_name -> ToolRegistry
        self._resources_cache: dict[
            str, ResourceRegistry
        ] = {}  # uri -> ResourceRegistry
        self._tools_by_server: dict[str, list[MCPTool]] = {}
        self._resources_by_server: dict[str, list[MCPResource]] = {}
        self._health_check_interval: float = 60.0  # seconds
        self._health_check_task: asyncio.Task | None = None
        self._cache_update_interval: float = 300.0  # 5 minutes
        self._last_cache_update: datetime | None = None

    def register_server(self, client: MCPClient) -> None:
        """
        Register an MCP client with the registry.

        Args:
            client: MCPClient instance to register
        """
        server_name = client.server_name

        if not server_name:
            raise ValueError("Client must have a valid server_name")

        if server_name in self._servers:
            logger.warning(f"Server {server_name} is already registered, replacing")

        self._servers[server_name] = client
        self._server_status[server_name] = ServerStatus(
            name=server_name,
            connected=client.is_connected(),
            transport_type=client.config.get("transport", "unknown"),
        )

        logger.info(f"Registered MCP server: {server_name}")

    def unregister_server(self, server_name: str) -> bool:
        """
        Unregister an MCP server from the registry.

        Args:
            server_name: Name of the server to unregister

        Returns:
            True if server was unregistered, False if not found
        """
        if server_name not in self._servers:
            return False

        # Clean up server data
        del self._servers[server_name]
        del self._server_status[server_name]

        # Remove server's tools and resources from cache
        self._tools_by_server.pop(server_name, None)
        self._resources_by_server.pop(server_name, None)

        # Remove from unified caches
        tools_to_remove = [
            name
            for name, registry in self._tools_cache.items()
            if registry.server_name == server_name
        ]
        for tool_name in tools_to_remove:
            del self._tools_cache[tool_name]

        resources_to_remove = [
            uri
            for uri, registry in self._resources_cache.items()
            if registry.server_name == server_name
        ]
        for resource_uri in resources_to_remove:
            del self._resources_cache[resource_uri]

        logger.info(f"Unregistered MCP server: {server_name}")
        return True

    def get_server(self, server_name: str) -> MCPClient | None:
        """
        Get a registered MCP client by name.

        Args:
            server_name: Name of the server

        Returns:
            MCPClient instance if found, None otherwise
        """
        return self._servers.get(server_name)

    def get_all_servers(self) -> list[MCPClient]:
        """
        Get all registered MCP clients.

        Returns:
            List of all registered MCPClient instances
        """
        return list(self._servers.values())

    def get_server_names(self) -> list[str]:
        """
        Get names of all registered servers.

        Returns:
            List of server names
        """
        return list(self._servers.keys())

    def get_server_status(self, server_name: str) -> ServerStatus | None:
        """
        Get status information for a server.

        Args:
            server_name: Name of the server

        Returns:
            ServerStatus if found, None otherwise
        """
        return self._server_status.get(server_name)

    def get_all_server_statuses(self) -> dict[str, ServerStatus]:
        """
        Get status information for all servers.

        Returns:
            Dictionary mapping server names to their status
        """
        return self._server_status.copy()

    async def connect_all_servers(self) -> dict[str, bool]:
        """
        Connect to all registered servers.

        Returns:
            Dictionary mapping server names to connection success status
        """
        results = {}

        for server_name, client in self._servers.items():
            try:
                logger.info(f"Connecting to MCP server: {server_name}")
                await client.connect()
                results[server_name] = True

                # Update status
                status = self._server_status[server_name]
                status.connected = True
                status.last_error = None
                status.connection_attempts += 1

                logger.info(f"Connected to server: {server_name}")
            except Exception as e:
                results[server_name] = False

                # Update status
                status = self._server_status[server_name]
                status.connected = False
                status.last_error = str(e)
                status.connection_attempts += 1

                logger.error(f"Failed to connect to server {server_name}: {e}")

        return results

    async def disconnect_all_servers(self) -> None:
        """Disconnect from all servers."""
        for server_name, client in self._servers.items():
            try:
                await client.disconnect()
                self._server_status[server_name].connected = False
                logger.info(f"Disconnected from server: {server_name}")
            except Exception as e:
                self._server_status[server_name].connected = False
                logger.error(f"Error disconnecting from server {server_name}: {e}")

    async def update_tools_cache(self) -> None:
        """Update the tools cache from all connected servers."""
        logger.debug("Updating tools cache from all servers")

        for server_name, client in self._servers.items():
            if not client.is_connected():
                logger.debug(
                    f"Skipping tools update for disconnected server: {server_name}"
                )
                continue

            try:
                tools = await client.list_tools()
                self._tools_by_server[server_name] = tools

                # Update unified cache
                for tool in tools:
                    tool_key = f"{server_name}:{tool.name}"
                    self._tools_cache[tool_key] = ToolRegistry(
                        tool=tool, server_name=server_name, last_updated=datetime.now()
                    )

                # Update server status
                self._server_status[server_name].tools_count = len(tools)
                logger.debug(f"Updated {len(tools)} tools for server: {server_name}")

            except Exception as e:
                logger.error(f"Failed to update tools for server {server_name}: {e}")
                self._server_status[server_name].last_error = str(e)

        self._last_cache_update = datetime.now()

    async def update_resources_cache(self) -> None:
        """Update the resources cache from all connected servers."""
        logger.debug("Updating resources cache from all servers")

        for server_name, client in self._servers.items():
            if not client.is_connected():
                logger.debug(
                    f"Skipping resources update for disconnected server: {server_name}"
                )
                continue

            try:
                resources = await client.list_resources()
                self._resources_by_server[server_name] = resources

                # Update unified cache
                for resource in resources:
                    self._resources_cache[resource.uri] = ResourceRegistry(
                        resource=resource,
                        server_name=server_name,
                        last_updated=datetime.now(),
                    )

                # Update server status
                self._server_status[server_name].resources_count = len(resources)
                logger.debug(
                    f"Updated {len(resources)} resources for server: {server_name}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to update resources for server {server_name}: {e}"
                )
                self._server_status[server_name].last_error = str(e)

    def get_all_tools(self) -> dict[str, list[MCPTool]]:
        """
        Get all cached tools organized by server.

        Returns:
            Dictionary mapping server names to their tools
        """
        return self._tools_by_server.copy()

    def get_tools_for_server(self, server_name: str) -> list[MCPTool]:
        """
        Get all tools for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            List of tools for the server, empty list if server not found
        """
        return self._tools_by_server.get(server_name, [])

    def get_tool(
        self, tool_name: str, server_name: str | None = None
    ) -> ToolRegistry | None:
        """
        Get a tool by name, optionally from a specific server.

        Args:
            tool_name: Name of the tool
            server_name: Optional server name to search in

        Returns:
            ToolRegistry if found, None otherwise
        """
        if server_name:
            tool_key = f"{server_name}:{tool_name}"
            return self._tools_cache.get(tool_key)

        # Search across all servers
        for _tool_key, registry in self._tools_cache.items():
            if registry.tool.name == tool_name:
                return registry

        return None

    def search_tools(self, query: str) -> list[ToolRegistry]:
        """
        Search for tools by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching ToolRegistry entries
        """
        query_lower = query.lower()
        results = []

        for registry in self._tools_cache.values():
            tool = registry.tool
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
            ):
                results.append(registry)

        return results

    def get_all_resources(self) -> dict[str, list[MCPResource]]:
        """
        Get all cached resources organized by server.

        Returns:
            Dictionary mapping server names to their resources
        """
        return self._resources_by_server.copy()

    def get_resources_for_server(self, server_name: str) -> list[MCPResource]:
        """
        Get all resources for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            List of resources for the server, empty list if server not found
        """
        return self._resources_by_server.get(server_name, [])

    def get_resource(self, uri: str) -> ResourceRegistry | None:
        """
        Get a resource by URI.

        Args:
            uri: URI of the resource

        Returns:
            ResourceRegistry if found, None otherwise
        """
        return self._resources_cache.get(uri)

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], server_name: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Call a tool across servers with improved error handling.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            server_name: Optional specific server to call the tool on

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            MCPError: If tool execution fails
        """
        tool_registry = self.get_tool(tool_name, server_name)

        if not tool_registry:
            available_tools = [
                registry.tool.name for registry in self._tools_cache.values()
            ]
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )

        server = self.get_server(tool_registry.server_name)
        if not server:
            raise MCPError(f"Server '{tool_registry.server_name}' not available")

        # Check connection and attempt reconnection if needed
        if not server.is_connected():
            logger.warning(f"Server '{tool_registry.server_name}' is not connected, attempting reconnection...")
            try:
                await server.reconnect()
            except Exception as e:
                logger.error(f"Failed to reconnect to server '{tool_registry.server_name}': {e}")
                raise MCPError(f"Server '{tool_registry.server_name}' is not connected and reconnection failed: {e}")

        # Execute the tool call with error handling
        try:
            return await server.call_tool(tool_name, arguments)
        except Exception as e:
            # Check if this is an event loop issue
            error_msg = str(e)
            if "loop" in error_msg.lower() or "event" in error_msg.lower():
                logger.warning(f"Event loop issue calling tool {tool_name} on server {tool_registry.server_name}: {e}")
                # Mark server as disconnected and attempt reconnection
                server._connected = False
                try:
                    logger.info(f"Attempting to reconnect server {tool_registry.server_name} due to event loop issue")
                    await server.reconnect()
                    # Retry the tool call once after reconnection
                    return await server.call_tool(tool_name, arguments)
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect and retry tool call: {reconnect_error}")
                    raise MCPError(f"Tool call failed due to event loop issue and reconnection failed: {reconnect_error}")
            else:
                # Re-raise other errors
                raise

    async def read_resource(self, uri: str) -> list[dict[str, Any]]:
        """
        Read a resource from the appropriate server.

        Args:
            uri: URI of the resource

        Returns:
            Resource content

        Raises:
            ValueError: If resource not found
            MCPError: If resource reading fails
        """
        resource_registry = self.get_resource(uri)

        if not resource_registry:
            available_resources = list(self._resources_cache.keys())
            raise ValueError(
                f"Resource '{uri}' not found. Available resources: {available_resources}"
            )

        server = self.get_server(resource_registry.server_name)
        if not server:
            raise MCPError(f"Server '{resource_registry.server_name}' not available")

        if not server.is_connected():
            raise MCPError(f"Server '{resource_registry.server_name}' is not connected")

        return await server.read_resource(uri)

    async def health_check(self) -> dict[str, bool]:
        """
        Perform health check on all servers.

        Returns:
            Dictionary mapping server names to health status
        """
        results = {}

        for server_name, client in self._servers.items():
            try:
                if client.is_connected():
                    await client.ping()
                    results[server_name] = True
                    self._server_status[server_name].last_ping = datetime.now()
                    self._server_status[server_name].last_error = None
                else:
                    results[server_name] = False
            except Exception as e:
                results[server_name] = False
                status = self._server_status[server_name]
                status.last_error = str(e)
                status.connected = False
                logger.warning(f"Health check failed for server {server_name}: {e}")

        return results

    def start_health_monitoring(self) -> None:
        """Start periodic health monitoring of servers."""
        if self._health_check_task is not None:
            logger.warning("Health monitoring already started")
            return

        async def health_monitor():
            while True:
                try:
                    await self.health_check()

                    # Update caches periodically
                    if (
                        self._last_cache_update is None
                        or datetime.now() - self._last_cache_update
                        > timedelta(seconds=self._cache_update_interval)
                    ):
                        await self.update_tools_cache()
                        await self.update_resources_cache()

                    await asyncio.sleep(self._health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in health monitoring: {e}")
                    await asyncio.sleep(self._health_check_interval)

        self._health_check_task = asyncio.create_task(health_monitor())
        logger.info("Started health monitoring")

    def stop_health_monitoring(self) -> None:
        """Stop periodic health monitoring."""
        if self._health_check_task is not None:
            self._health_check_task.cancel()
            self._health_check_task = None
            logger.info("Stopped health monitoring")

    def get_registry_stats(self) -> dict[str, Any]:
        """
        Get statistics about the registry.

        Returns:
            Dictionary containing registry statistics
        """
        connected_servers = sum(
            1 for status in self._server_status.values() if status.connected
        )
        total_tools = sum(len(tools) for tools in self._tools_by_server.values())
        total_resources = sum(
            len(resources) for resources in self._resources_by_server.values()
        )

        return {
            "total_servers": len(self._servers),
            "connected_servers": connected_servers,
            "total_tools": total_tools,
            "total_resources": total_resources,
            "last_cache_update": self._last_cache_update,
            "health_monitoring_active": self._health_check_task is not None,
        }
