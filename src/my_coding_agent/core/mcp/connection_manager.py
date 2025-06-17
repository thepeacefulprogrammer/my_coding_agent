"""
Connection lifecycle management for MCP clients.

This module provides comprehensive connection lifecycle management including:
- Automatic reconnection with exponential backoff
- Connection state monitoring and recovery
- Health checking and status monitoring
- Graceful handling of transient network issues
- Connection pooling and event emission
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .mcp_client import MCPClient, MCPConnectionError, MCPTimeoutError

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for tracking connection performance and health."""

    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    last_connection_time: datetime | None = None
    uptime: timedelta = field(default_factory=lambda: timedelta(0))
    reconnection_count: int = 0
    last_error: str | None = None
    status: str = "disconnected"  # disconnected, connecting, connected, degraded


@dataclass
class ConnectionEvent:
    """Event data for connection state changes."""

    client: MCPClient | None
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """
    Manages connection lifecycle for multiple MCP clients.

    Provides automatic reconnection, health monitoring, and graceful degradation
    for MCP client connections.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize connection manager.

        Args:
            config: Configuration dictionary with optional settings
        """
        self._clients: dict[str, list[MCPClient]] = {}  # server_name -> [clients]
        self._client_metrics: dict[MCPClient, ConnectionMetrics] = {}
        self._event_listeners: dict[str, list[Callable]] = {}
        self._monitoring_task: asyncio.Task | None = None
        self._reconnection_tasks: dict[MCPClient, asyncio.Task] = {}
        self._monitoring_running = False

        # Configuration with defaults
        config = config or {}
        self._monitoring_interval: float = config.get("monitoring_interval", 30.0)
        self._max_reconnection_attempts: int = config.get(
            "max_reconnection_attempts", 5
        )
        self._reconnection_backoff_base: float = config.get(
            "reconnection_backoff_base", 2.0
        )
        self._health_check_timeout: float = config.get("health_check_timeout", 10.0)
        self._transient_error_threshold: int = config.get(
            "transient_error_threshold", 3
        )

        logger.info("Connection manager initialized")

    def configure(self, config: dict[str, Any]) -> None:
        """
        Update configuration settings.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        if "monitoring_interval" in config:
            interval = config["monitoring_interval"]
            if interval <= 0:
                raise ValueError("monitoring_interval must be positive")
            self._monitoring_interval = interval

        if "max_reconnection_attempts" in config:
            attempts = config["max_reconnection_attempts"]
            if attempts < 0:
                raise ValueError("max_reconnection_attempts must be non-negative")
            self._max_reconnection_attempts = attempts

        if "reconnection_backoff_base" in config:
            backoff = config["reconnection_backoff_base"]
            if backoff <= 1.0:
                raise ValueError("reconnection_backoff_base must be greater than 1.0")
            self._reconnection_backoff_base = backoff

    def add_client(self, client: MCPClient) -> None:
        """
        Add a client to be managed by the connection manager.

        Args:
            client: MCP client to add
        """
        server_name = client.server_name or "unknown"

        if server_name not in self._clients:
            self._clients[server_name] = []

        if client not in self._clients[server_name]:
            self._clients[server_name].append(client)
            self._client_metrics[client] = ConnectionMetrics()

            logger.info(f"Added client for server: {server_name}")
            self.emit_event(
                "connection_state_changed",
                {
                    "client": client,
                    "event_type": "client_added",
                    "server_name": server_name,
                },
            )

    def remove_client(self, client: MCPClient) -> bool:
        """
        Remove a client from the connection manager.

        Args:
            client: MCP client to remove

        Returns:
            True if client was removed, False if not found
        """
        server_name = client.server_name or "unknown"

        if server_name in self._clients and client in self._clients[server_name]:
            self._clients[server_name].remove(client)

            # Clean up empty server entries
            if not self._clients[server_name]:
                del self._clients[server_name]

            # Cancel any ongoing reconnection tasks
            if client in self._reconnection_tasks:
                self._reconnection_tasks[client].cancel()
                del self._reconnection_tasks[client]

            # Clean up metrics
            if client in self._client_metrics:
                del self._client_metrics[client]

            logger.info(f"Removed client for server: {server_name}")
            self.emit_event(
                "connection_state_changed",
                {
                    "client": client,
                    "event_type": "client_removed",
                    "server_name": server_name,
                },
            )
            return True

        return False

    def get_clients_for_server(self, server_name: str) -> list[MCPClient]:
        """
        Get all clients for a specific server.

        Args:
            server_name: Server name to get clients for

        Returns:
            List of clients for the server
        """
        return self._clients.get(server_name, []).copy()

    def get_client_status(self, client: MCPClient) -> dict[str, Any]:
        """
        Get status information for a client.

        Args:
            client: Client to get status for

        Returns:
            Status dictionary
        """
        metrics = self._client_metrics.get(client, ConnectionMetrics())

        return {
            "status": metrics.status,
            "connected": client.is_connected()
            if hasattr(client, "is_connected")
            else False,
            "connection_attempts": metrics.connection_attempts,
            "successful_connections": metrics.successful_connections,
            "failed_connections": metrics.failed_connections,
            "last_connection_time": metrics.last_connection_time,
            "uptime": metrics.uptime,
            "reconnection_count": metrics.reconnection_count,
            "last_error": metrics.last_error,
        }

    def get_connection_metrics(self, client: MCPClient) -> dict[str, Any]:
        """
        Get connection metrics for a client.

        Args:
            client: Client to get metrics for

        Returns:
            Metrics dictionary
        """
        metrics = self._client_metrics.get(client, ConnectionMetrics())

        return {
            "connection_attempts": metrics.connection_attempts,
            "successful_connections": metrics.successful_connections,
            "failed_connections": metrics.failed_connections,
            "last_connection_time": metrics.last_connection_time,
            "uptime": metrics.uptime,
            "reconnection_count": metrics.reconnection_count,
        }

    async def start_monitoring(self) -> None:
        """Start connection monitoring task."""
        if self._monitoring_task is not None:
            logger.warning("Monitoring is already running")
            return

        self._monitoring_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started connection monitoring")

    async def stop_monitoring(self) -> None:
        """Stop connection monitoring task."""
        if self._monitoring_task is None:
            return

        self._monitoring_running = False
        self._monitoring_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await self._monitoring_task

        self._monitoring_task = None
        logger.info("Stopped connection monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring_running:
            try:
                # Check health of all clients
                tasks = []
                for clients in self._clients.values():
                    for client in clients:
                        tasks.append(
                            asyncio.create_task(self._check_client_health(client))
                        )

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Wait for next monitoring cycle
                await asyncio.sleep(self._monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self._monitoring_interval)

    async def _check_client_health(self, client: MCPClient) -> bool:
        """
        Check health of a specific client.

        Args:
            client: Client to check

        Returns:
            True if healthy, False otherwise
        """
        try:
            # First check if client reports being connected
            if not client.is_connected():
                logger.debug(f"Client {client.server_name} reports disconnected")
                await self._handle_connection_failure(client)
                return False

            # Perform ping health check with timeout
            try:
                await asyncio.wait_for(
                    client.ping(), timeout=self._health_check_timeout
                )
                logger.debug(f"Health check passed for {client.server_name}")

                # Update metrics on successful health check
                metrics = self._client_metrics.get(client, ConnectionMetrics())
                metrics.status = "connected"

                return True

            except asyncio.TimeoutError:
                logger.warning(f"Health check timeout for {client.server_name}")
                await self._handle_connection_failure(client)
                return False

        except MCPTimeoutError:
            logger.warning(f"Transient timeout for {client.server_name}")
            # For transient timeouts, don't immediately trigger reconnection
            return False

        except Exception as e:
            logger.error(f"Health check failed for {client.server_name}: {e}")
            await self._handle_connection_failure(client)
            return False

    async def _handle_connection_failure(self, client: MCPClient) -> None:
        """
        Handle connection failure for a client.

        Args:
            client: Client that failed
        """
        logger.info(f"Handling connection failure for {client.server_name}")

        # Update metrics
        metrics = self._client_metrics.get(client, ConnectionMetrics())
        metrics.status = "connecting"

        # Emit connection failure event
        self.emit_event(
            "connection_state_changed",
            {
                "client": client,
                "event_type": "connection_failed",
                "server_name": client.server_name,
            },
        )

        # Start reconnection task if not already running
        if (
            client not in self._reconnection_tasks
            or self._reconnection_tasks[client].done()
        ):
            self._reconnection_tasks[client] = asyncio.create_task(
                self._attempt_reconnection(client, self._max_reconnection_attempts)
            )

    async def _attempt_reconnection(self, client: MCPClient, max_attempts: int) -> None:
        """
        Attempt to reconnect a client with exponential backoff.

        Args:
            client: Client to reconnect
            max_attempts: Maximum number of reconnection attempts

        Raises:
            MCPConnectionError: If all reconnection attempts fail
        """
        metrics = self._client_metrics.get(client, ConnectionMetrics())

        for attempt in range(max_attempts):
            try:
                logger.info(
                    f"Reconnection attempt {attempt + 1} for {client.server_name}"
                )

                # Update metrics
                metrics.connection_attempts += 1

                # Attempt connection
                await client.connect()

                # Success!
                metrics.successful_connections += 1
                metrics.last_connection_time = datetime.now()
                metrics.status = "connected"
                metrics.reconnection_count += 1

                logger.info(f"Successfully reconnected to {client.server_name}")

                # Emit successful reconnection event
                self.emit_event(
                    "connection_state_changed",
                    {
                        "client": client,
                        "event_type": "reconnected",
                        "server_name": client.server_name,
                        "attempts": attempt + 1,
                    },
                )

                return

            except Exception as e:
                metrics.failed_connections += 1
                metrics.last_error = str(e)

                if attempt < max_attempts - 1:
                    # Calculate exponential backoff delay
                    delay = self._reconnection_backoff_base**attempt
                    logger.info(
                        f"Reconnection failed for {client.server_name}, "
                        f"retrying in {delay} seconds: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    # All attempts failed
                    logger.error(
                        f"All reconnection attempts failed for {client.server_name}: {e}"
                    )
                    metrics.status = "degraded"

                    # Emit degraded event
                    self.emit_event(
                        "connection_state_changed",
                        {
                            "client": client,
                            "event_type": "degraded",
                            "server_name": client.server_name,
                            "total_attempts": max_attempts,
                            "error": str(e),
                        },
                    )

                    raise MCPConnectionError(
                        f"Failed to reconnect after {max_attempts} attempts: {e}"
                    ) from e

    async def health_check(self, client: MCPClient) -> bool:
        """
        Perform a one-time health check on a client.

        Args:
            client: Client to check

        Returns:
            True if healthy, False otherwise
        """
        return await self._check_client_health(client)

    async def shutdown(self) -> None:
        """Shutdown the connection manager and cleanup all resources."""
        logger.info("Shutting down connection manager")

        # Stop monitoring
        await self.stop_monitoring()

        # Cancel all reconnection tasks
        for task in self._reconnection_tasks.values():
            task.cancel()

        if self._reconnection_tasks:
            await asyncio.gather(
                *self._reconnection_tasks.values(), return_exceptions=True
            )

        # Disconnect all clients
        disconnect_tasks = []
        for clients in self._clients.values():
            for client in clients:
                if hasattr(client, "disconnect"):
                    disconnect_tasks.append(asyncio.create_task(client.disconnect()))

        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        # Clear all data
        self._clients.clear()
        self._client_metrics.clear()
        self._reconnection_tasks.clear()

        logger.info("Connection manager shutdown complete")

    def add_event_listener(self, event_type: str, handler: Callable) -> None:
        """
        Add an event listener for connection state changes.

        Args:
            event_type: Type of event to listen for
            handler: Callback function to handle events
        """
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []

        self._event_listeners[event_type].append(handler)

    def remove_event_listener(self, event_type: str, handler: Callable) -> bool:
        """
        Remove an event listener.

        Args:
            event_type: Type of event
            handler: Handler to remove

        Returns:
            True if handler was removed, False if not found
        """
        if (
            event_type in self._event_listeners
            and handler in self._event_listeners[event_type]
        ):
            self._event_listeners[event_type].remove(handler)
            return True
        return False

    def emit_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event_type: Type of event to emit
            event_data: Event data dictionary
        """
        if event_type not in self._event_listeners:
            return

        ConnectionEvent(
            client=event_data.get("client"),
            event_type=event_data.get("event_type", event_type),
            details=event_data,
        )

        for handler in self._event_listeners[event_type]:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def get_all_clients(self) -> list[MCPClient]:
        """
        Get all managed clients.

        Returns:
            List of all clients
        """
        clients = []
        for client_list in self._clients.values():
            clients.extend(client_list)
        return clients

    def get_statistics(self) -> dict[str, Any]:
        """
        Get connection manager statistics.

        Returns:
            Statistics dictionary
        """
        total_clients = len(self.get_all_clients())
        connected_clients = sum(
            1 for client in self.get_all_clients() if client.is_connected()
        )

        total_attempts = sum(
            metrics.connection_attempts for metrics in self._client_metrics.values()
        )

        total_successes = sum(
            metrics.successful_connections for metrics in self._client_metrics.values()
        )

        return {
            "total_clients": total_clients,
            "connected_clients": connected_clients,
            "disconnected_clients": total_clients - connected_clients,
            "total_connection_attempts": total_attempts,
            "total_successful_connections": total_successes,
            "success_rate": total_successes / max(total_attempts, 1),
            "monitoring_running": self._monitoring_running,
            "active_reconnection_tasks": len(
                [task for task in self._reconnection_tasks.values() if not task.done()]
            ),
        }
