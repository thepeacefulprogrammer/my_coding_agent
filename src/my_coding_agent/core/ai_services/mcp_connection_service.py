"""MCP Connection Service for managing MCP server connections."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from ..mcp import MCPClient, MCPServerRegistry

if TYPE_CHECKING:
    from typing import Any as SignalHandler

    from .tool_registration_service import ToolRegistrationService

logger = logging.getLogger(__name__)


class MCPConnectionService:
    """Service for managing MCP server connections and lifecycle."""

    def __init__(
        self,
        signal_handler: SignalHandler | None = None,  # noqa: ANN401
        tool_registration_service: ToolRegistrationService | None = None,
    ) -> None:
        """
        Initialize the MCP Connection Service.

        Args:
            signal_handler: Object that can emit signals for UI updates (e.g., MainWindow)
            tool_registration_service: ToolRegistrationService for tool cache updates after connections
        """
        self.signal_handler = signal_handler
        self.tool_registration_service = tool_registration_service
        self.mcp_registry: MCPServerRegistry | None = None
        self._mcp_servers_need_connection = False
        self._mcp_tools_registered = False
        self.mcp_file_server = None

        # Initialize logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def initialize_mcp_registry(self, auto_discover: bool = False) -> None:
        """
        Initialize MCP registry and optionally auto-discover servers.

        Args:
            auto_discover: Whether to auto-discover MCP servers from configuration
        """
        try:
            self.mcp_registry = MCPServerRegistry()

            if auto_discover:
                self._auto_discover_mcp_servers()

            logger.info("MCP server registry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP registry: {e}")
            self.mcp_registry = None

    def _auto_discover_mcp_servers(self) -> None:
        """Automatically discover and register MCP servers from configuration using enhanced logic."""
        if not self.mcp_registry:
            return

        try:
            # Use enhanced auto-discovery from AIAgent - more sophisticated than simple mcp.json
            from ..mcp import load_default_mcp_config

            mcp_config = load_default_mcp_config()
            servers = mcp_config.get_all_servers()
            logger.info(
                f"Found {len(servers)} MCP servers in configuration: {list(servers.keys())}"
            )

            for server_name, server_config in servers.items():
                try:
                    # Convert MCPServerConfig to dict format expected by MCPClient
                    client_config = server_config.to_dict()
                    client = MCPClient(client_config)
                    self.mcp_registry.register_server(client)
                    logger.info(f"Auto-discovered MCP server: {server_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to register auto-discovered server {server_name}: {e}"
                    )

            # After registering all servers, mark them for lazy connection
            if servers:
                logger.info(
                    f"Auto-discovered {len(servers)} MCP servers, will connect on first use"
                )
                self._mcp_servers_need_connection = True

        except Exception as e:
            logger.warning(f"Failed to auto-discover MCP servers: {e}")
            # Fallback to simple mcp.json discovery if enhanced method fails
            self._auto_discover_mcp_servers_fallback()

    def _auto_discover_mcp_servers_fallback(self) -> None:
        """Fallback auto-discovery method using simple mcp.json file."""
        try:
            # Try to load from mcp.json (original simple method)
            import json
            from pathlib import Path

            mcp_config_path = Path("mcp.json")
            if mcp_config_path.exists():
                with open(mcp_config_path) as f:
                    config = json.load(f)

                # Register servers from configuration
                if "mcpServers" in config:
                    for server_name, server_config in config["mcpServers"].items():
                        try:
                            client = MCPClient(
                                server_name=server_name,
                                command=server_config.get("command"),
                                args=server_config.get("args", []),
                                env=server_config.get("env", {}),
                            )
                            if self.mcp_registry:
                                self.mcp_registry.register_server(client)
                                logger.info(
                                    f"Auto-discovered MCP server (fallback): {server_name}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to auto-discover server {server_name}: {e}"
                            )
        except Exception as e:
            logger.error(f"Failed to auto-discover MCP servers (fallback): {e}")

    async def connect_mcp_servers(self) -> dict[str, bool]:
        """
        Connect to all registered MCP servers with advanced features.
        Includes tool cache updates and integration with ToolRegistrationService.

        Returns:
            dict[str, bool]: Dictionary mapping server names to connection success status
        """
        if not self.mcp_registry:
            logger.warning("MCP registry not initialized")
            return {}

        logger.info("Connecting to MCP servers...")

        # Get current event loop info for debugging (enhanced from AIAgent)
        try:
            current_loop = asyncio.get_running_loop()
            logger.info(f"Connecting MCP servers in event loop: {current_loop}")
        except RuntimeError:
            logger.warning("No event loop running during MCP connection")

        # Connect to all servers using registry's method
        connection_results = await self.mcp_registry.connect_all_servers()

        successful_connections = sum(
            1 for success in connection_results.values() if success
        )
        total_servers = len(connection_results)

        logger.info(
            f"MCP server connections: {successful_connections}/{total_servers} successful"
        )

        if successful_connections > 0:
            # Update tools cache from connected servers (enhanced from AIAgent)
            logger.info("Updating MCP tools cache from connected servers...")
            await self.mcp_registry.update_tools_cache()

            # Get tool count for logging
            all_tools = self.mcp_registry.get_all_tools()
            total_tools = sum(len(tools) for tools in all_tools.values())
            logger.info(
                f"MCP tools cache updated: {total_tools} tools discovered from {successful_connections} servers"
            )

            # Re-register MCP tools with the agent after successful connections (if service available)
            if self.tool_registration_service and hasattr(
                self.tool_registration_service, "register_all_tools"
            ):
                logger.info(
                    "Re-registering MCP tools after successful server connections..."
                )
                # Note: This will be called by the AIAgent with the agent parameter
                # The service itself doesn't have access to the agent
                self._mcp_tools_registered = True
            else:
                logger.debug(
                    "Tool registration service not available for MCP tool updates"
                )
        else:
            logger.warning("No MCP servers connected successfully")

        return connection_results

    async def connect_mcp_servers_async(self) -> None:
        """
        Connect to all registered MCP servers asynchronously (AIAgent compatibility method).
        This is a wrapper around connect_mcp_servers for AIAgent compatibility.
        """
        try:
            await self.connect_mcp_servers()
        except Exception as e:
            logger.error(f"Error connecting to MCP servers: {e}")
            # Don't raise the exception to avoid breaking initialization

    async def disconnect_mcp_servers(self) -> None:
        """Disconnect from all MCP servers."""
        if not self.mcp_registry:
            return

        clients = self.mcp_registry.get_all_servers()
        for client in clients:
            await client.disconnect()

    def register_mcp_server(self, client: MCPClient) -> None:
        """
        Register an MCP server client.

        Args:
            client: The MCP client to register
        """
        if not self.mcp_registry:
            self.mcp_registry = MCPServerRegistry()

        self.mcp_registry.register_server(client)
        logger.info(f"Registered MCP server: {client.server_name}")

        # Emit signal if available
        if self.signal_handler and hasattr(
            self.signal_handler, "mcp_server_registered"
        ):
            self.signal_handler.mcp_server_registered.emit(client.server_name)

    def unregister_mcp_server(self, server_name: str) -> bool:
        """
        Unregister an MCP server.

        Args:
            server_name: Name of the server to unregister

        Returns:
            bool: True if server was unregistered successfully
        """
        if not self.mcp_registry:
            return False

        result = self.mcp_registry.unregister_server(server_name)
        if result:
            logger.info(f"Unregistered MCP server: {server_name}")
            # Emit signal if available
            if self.signal_handler and hasattr(
                self.signal_handler, "mcp_server_unregistered"
            ):
                self.signal_handler.mcp_server_unregistered.emit(server_name)

        return result

    async def get_mcp_server_status(self) -> dict[str, Any]:
        """
        Get the status of all MCP servers.

        Returns:
            dict[str, Any]: Dictionary containing server status information
        """
        if not self.mcp_registry:
            return {
                "servers": {},
                "total_servers": 0,
                "connected_servers": 0,
                "available_tools": 0,
            }

        servers = {}
        total_servers = 0
        connected_servers = 0
        available_tools = 0

        for client in self.mcp_registry.get_all_servers():
            total_servers += 1
            is_connected = client.is_connected
            if is_connected:
                connected_servers += 1

            server_tools = []
            tool_count = 0
            if is_connected and hasattr(client, "list_tools"):
                try:
                    tools_result = client.list_tools()
                    if asyncio.iscoroutine(tools_result):
                        server_tools = await tools_result or []
                    else:
                        server_tools = tools_result or []
                    tool_count = len(server_tools)
                    available_tools += tool_count
                except Exception as e:
                    logger.warning(f"Failed to get tools for {client.server_name}: {e}")

            servers[client.server_name] = {
                "connected": is_connected,
                "tools": server_tools,
                "tool_count": tool_count,
                "server_info": getattr(client, "server_info", {}),
            }

        return {
            "servers": servers,
            "total_servers": total_servers,
            "connected_servers": connected_servers,
            "available_tools": available_tools,
        }

    async def ensure_mcp_servers_connected(self) -> bool:
        """
        Ensure all MCP servers are connected.

        Returns:
            bool: True if all servers are connected successfully
        """
        if not self.mcp_registry:
            return False

        try:
            connection_results = await self.connect_mcp_servers()
            all_connected = all(connection_results.values())

            if not all_connected:
                failed_servers = [
                    name
                    for name, connected in connection_results.items()
                    if not connected
                ]
                logger.warning(f"Failed to connect to servers: {failed_servers}")

            return all_connected
        except Exception as e:
            logger.error(f"Error ensuring MCP servers connected: {e}")
            return False

    @property
    def has_mcp_servers(self) -> bool:
        """Check if any MCP servers are registered."""
        return (
            self.mcp_registry is not None
            and len(self.mcp_registry.get_all_servers()) > 0
        )

    @property
    def connected_server_count(self) -> int:
        """Get the number of connected MCP servers."""
        if not self.mcp_registry:
            return 0

        return sum(
            1 for client in self.mcp_registry.get_all_servers() if client.is_connected
        )

    def get_mcp_health_status(self) -> dict[str, Any]:
        """
        Get comprehensive MCP health status (enhanced from AIAgent).

        Returns:
            dict[str, Any]: Comprehensive health status including connection details
        """
        if not self.mcp_registry:
            return {
                "status": "not_configured",
                "message": "MCP registry not initialized",
                "servers": {},
                "total_servers": 0,
                "connected_servers": 0,
                "available_tools": 0,
                "health_score": 0.0,
            }

        try:
            servers = {}
            total_servers = 0
            connected_servers = 0
            available_tools = 0
            health_issues = []

            for client in self.mcp_registry.get_all_servers():
                total_servers += 1
                is_connected = client.is_connected

                if is_connected:
                    connected_servers += 1
                else:
                    health_issues.append(
                        f"Server '{client.server_name}' is disconnected"
                    )

                # Get server tools
                server_tools = []
                tool_count = 0
                if is_connected and hasattr(client, "list_tools"):
                    try:
                        tools_result = client.list_tools()
                        if asyncio.iscoroutine(tools_result):
                            # Cannot await in sync method, use cached tools
                            cached_tools = getattr(client, "_cached_tools", [])
                            server_tools = cached_tools
                        else:
                            server_tools = tools_result or []
                        tool_count = len(server_tools)
                        available_tools += tool_count
                    except Exception as e:
                        health_issues.append(
                            f"Failed to get tools for {client.server_name}: {e}"
                        )

                servers[client.server_name] = {
                    "connected": is_connected,
                    "tools": server_tools,
                    "tool_count": tool_count,
                    "server_info": getattr(client, "server_info", {}),
                    "last_error": getattr(client, "last_error", None),
                }

            # Calculate health score
            health_score = (
                (connected_servers / total_servers) if total_servers > 0 else 0.0
            )

            # Determine overall status
            if total_servers == 0:
                status = "no_servers"
                message = "No MCP servers configured"
            elif connected_servers == 0:
                status = "all_disconnected"
                message = "All MCP servers are disconnected"
            elif connected_servers == total_servers:
                status = "healthy"
                message = "All MCP servers are connected and operational"
            else:
                status = "partial"
                message = f"{connected_servers}/{total_servers} servers connected"

            return {
                "status": status,
                "message": message,
                "servers": servers,
                "total_servers": total_servers,
                "connected_servers": connected_servers,
                "available_tools": available_tools,
                "health_score": health_score,
                "health_issues": health_issues,
                "registry_initialized": True,
            }

        except Exception as e:
            logger.error(f"Error getting MCP health status: {e}")
            return {
                "status": "error",
                "message": f"Error retrieving health status: {e}",
                "servers": {},
                "total_servers": 0,
                "connected_servers": 0,
                "available_tools": 0,
                "health_score": 0.0,
                "health_issues": [str(e)],
                "registry_initialized": self.mcp_registry is not None,
            }

    # def update_mcp_config(self, new_config: MCPFileConfig) -> None:
    #     """
    #     Update MCP configuration dynamically (from AIAgent).
    #
    #     Args:
    #         new_config: New MCP file configuration
    #     """
    #     try:
    #         self.mcp_file_server = new_config
    #         logger.info("MCP configuration updated successfully")
    #
    #         # Emit signal if available
    #         if self.signal_handler and hasattr(
    #             self.signal_handler, "mcp_config_updated"
    #         ):
    #             self.signal_handler.mcp_config_updated.emit()
    #
    #     except Exception as e:
    #         logger.error(f"Failed to update MCP configuration: {e}")

    async def connect_mcp(self) -> bool:
        """
        Connect to MCP servers (from AIAgent).

        Returns:
            bool: True if connection was successful
        """
        try:
            if not self.mcp_registry:
                logger.warning("MCP registry not initialized")
                return False

            connection_results = await self.connect_mcp_servers()
            success = any(connection_results.values())

            if success:
                logger.info("MCP connection established successfully")
            else:
                logger.warning("Failed to establish MCP connections")

            return success

        except Exception as e:
            logger.error(f"Error connecting to MCP: {e}")
            return False

    async def disconnect_mcp(self) -> None:
        """
        Disconnect from MCP servers (from AIAgent).
        """
        try:
            await self.disconnect_mcp_servers()
            logger.info("MCP disconnection completed")
        except Exception as e:
            logger.error(f"Error disconnecting from MCP: {e}")

    @asynccontextmanager
    async def mcp_context(self) -> AsyncGenerator[None, None]:
        """
        Async context manager for MCP operations (from AIAgent).
        Ensures MCP servers are connected during the context.
        """
        connected = await self.connect_mcp()
        try:
            if connected:
                yield
            else:
                logger.warning("MCP context entered but no servers connected")
                yield
        finally:
            # Optionally disconnect here, but usually we keep connections alive
            pass

    def _ensure_mcp_connected(self) -> None:
        """
        Ensure MCP servers are connected (sync version from AIAgent).
        This is a synchronous check - for async connection use ensure_mcp_servers_connected.
        """
        if not self.mcp_registry:
            logger.warning("MCP registry not initialized")
            return

        # Check if any servers need connection
        if self._mcp_servers_need_connection:
            logger.info(
                "MCP servers need connection - will connect on next async operation"
            )

    async def _ensure_mcp_servers_connected(self) -> bool:
        """
        Ensure all MCP servers are connected (async version from AIAgent).

        Returns:
            bool: True if all servers are connected successfully
        """
        if not self.mcp_registry:
            logger.warning("MCP registry not initialized")
            return False

        try:
            # Check if we need to connect
            if self._mcp_servers_need_connection:
                logger.info("Connecting MCP servers as needed...")
                connection_results = await self.connect_mcp_servers()
                self._mcp_servers_need_connection = False
                return any(connection_results.values())

            # Check if all servers are still connected
            all_connected = True
            for client in self.mcp_registry.get_all_servers():
                if not client.is_connected:
                    all_connected = False
                    break

            if not all_connected:
                logger.info("Some MCP servers disconnected, reconnecting...")
                connection_results = await self.connect_mcp_servers()
                return any(connection_results.values())

            return True

        except Exception as e:
            logger.error(f"Error ensuring MCP servers connected: {e}")
            return False

    async def connect_mcp_servers_on_startup(self) -> None:
        """
        Connect to MCP servers on startup (from AIAgent).
        This method is called during initialization to establish connections.
        """
        try:
            if self._mcp_servers_need_connection:
                logger.info("Connecting to MCP servers on startup...")
                await self.connect_mcp_servers()
                self._mcp_servers_need_connection = False
            else:
                logger.debug("No MCP servers need connection on startup")
        except Exception as e:
            logger.error(f"Error connecting MCP servers on startup: {e}")

    # Additional utility methods for compatibility
    def needs_connection(self) -> bool:
        """Check if MCP servers need connection."""
        return self._mcp_servers_need_connection

    def is_tools_registered(self) -> bool:
        """Check if MCP tools have been registered."""
        return self._mcp_tools_registered

    def set_tools_registered(self, registered: bool) -> None:
        """Set the MCP tools registration status."""
        self._mcp_tools_registered = registered
