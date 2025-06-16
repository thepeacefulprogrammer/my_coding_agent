"""
FastMCP client implementation for JSON-RPC protocol support.

This module provides a comprehensive MCP client implementation that wraps
the FastMCP library with additional features including support for multiple
transport protocols (stdio, HTTP, SSE, WebSocket).
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from fastmcp import Client

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP-related errors."""

    pass


class MCPConnectionError(MCPError):
    """Exception raised when connection operations fail."""

    pass


class MCPProtocolError(MCPError):
    """Exception raised when JSON-RPC protocol errors occur."""

    pass


class MCPTimeoutError(MCPError):
    """Exception raised when operations timeout."""

    pass


@dataclass
class MCPTool:
    """Represents an MCP tool with its metadata."""

    name: str
    description: str
    input_schema: "dict[str, Any]"
    server: str = ""

    @classmethod
    def from_mcp_result(
        cls, tool_data: "dict[str, Any]", server: str = ""
    ) -> "MCPTool":
        """Create MCPTool from MCP protocol result."""
        return cls(
            name=tool_data["name"],
            description=tool_data.get("description", ""),
            input_schema=tool_data.get("inputSchema", {}),
            server=server,
        )


@dataclass
class MCPResource:
    """Represents an MCP resource with its metadata."""

    uri: str
    name: str
    description: str = ""
    mime_type: str = ""
    server: str = ""

    @classmethod
    def from_mcp_result(
        cls, resource_data: "dict[str, Any]", server: str = ""
    ) -> "MCPResource":
        """Create MCPResource from MCP protocol result."""
        return cls(
            uri=resource_data["uri"],
            name=resource_data.get("name", ""),
            description=resource_data.get("description", ""),
            mime_type=resource_data.get("mimeType", ""),
            server=server,
        )


class MCPClient:
    """FastMCP client wrapper with enhanced transport protocol support."""

    def __init__(self, config: "dict[str, Any]"):
        """Initialize MCP client with configuration."""
        self.config = config.copy()
        self.server_name = config.get("server_name")
        self._request_id = 0
        self._client: Client | None = None

        # Auto-detect transport if not specified
        if "transport" not in self.config:
            self.config["transport"] = self._detect_transport_from_config()

        # Validate configuration
        self._validate_config()

        # Defer client creation until connection
        self._client_created = False

    def _detect_transport_from_config(self) -> str:
        """Auto-detect transport type from configuration."""
        if "url" in self.config:
            url = self.config["url"].lower()
            if url.startswith("ws://") or url.startswith("wss://"):
                return "websocket"
            elif "/sse" in url:
                return "sse"
            else:
                return "http"
        elif "command" in self.config:
            return "stdio"
        else:
            return "stdio"  # Default fallback

    def _validate_config(self) -> None:
        """Validate the configuration dictionary."""
        if not self.server_name:
            raise ValueError("server_name is required in configuration")

        transport = self.config.get("transport", "stdio")

        if transport not in ["stdio", "http", "sse", "websocket"]:
            raise ValueError(f"Unsupported transport type: {transport}")

        # Validate transport-specific requirements
        if transport == "stdio":
            if not self.config.get("command"):
                raise ValueError("command is required for stdio transport")
        elif transport in ["http", "sse", "websocket"] and not self.config.get("url"):
            raise ValueError(f"url is required for {transport} transport")

    def _create_client(self) -> None:
        """Create FastMCP client based on configuration and transport type."""
        if self._client_created:
            return

        transport_type = self.config.get("transport", "stdio")

        try:
            if transport_type == "stdio":
                self._create_stdio_client()
            elif transport_type == "http":
                self._create_http_client()
            elif transport_type == "sse":
                self._create_sse_client()
            elif transport_type == "websocket":
                self._create_websocket_client()

            self._client_created = True
        except Exception as e:
            logger.warning(f"Failed to create client: {e}")
            self._client = None

    def _create_stdio_client(self) -> None:
        """Create stdio transport client."""
        args = self.config.get("args", [])

        if args:
            # Use the script path for FastMCP auto-detection
            self._client = Client(args[0])
        else:
            # Fallback to command if no args
            command = self.config.get("command", "python")
            self._client = Client(command)

    def _create_http_client(self) -> None:
        """Create HTTP transport client."""
        from fastmcp.client.transports import StreamableHttpTransport

        url = self.config["url"]
        headers = self.config.get("headers", {})
        timeout = self.config.get("timeout")

        if headers or timeout:
            # Create explicit transport with custom settings
            transport_kwargs = {"url": url}
            if headers:
                transport_kwargs["headers"] = headers
            if timeout:
                transport_kwargs["timeout"] = timeout

            transport = StreamableHttpTransport(**transport_kwargs)
            self._client = Client(transport)
        else:
            # Use simple URL for auto-detection
            self._client = Client(url)

    def _create_sse_client(self) -> None:
        """Create SSE transport client."""
        from fastmcp.client.transports import SSETransport

        url = self.config["url"]
        headers = self.config.get("headers", {})
        timeout = self.config.get("timeout")

        if headers or timeout:
            # Create explicit transport with custom settings
            transport_kwargs = {"url": url}
            if headers:
                transport_kwargs["headers"] = headers
            if timeout:
                transport_kwargs["timeout"] = timeout

            transport = SSETransport(**transport_kwargs)
            self._client = Client(transport)
        else:
            # Use simple URL for auto-detection
            self._client = Client(url)

    def _create_websocket_client(self) -> None:
        """Create WebSocket transport client."""
        # Note: FastMCP may not have native WebSocket support yet
        # This is a placeholder for future WebSocket transport implementation
        try:
            # WebSocket transport not available in current FastMCP version
            # Fallback to HTTP transport
            logger.warning(
                "WebSocket transport not yet supported, falling back to HTTP"
            )
            self.config["transport"] = "http"
            self._create_http_client()
        except Exception as e:
            logger.error(f"Failed to create WebSocket client: {e}")
            self._client = None

    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        self._create_client()

        if not self._client:
            raise MCPConnectionError("Client not initialized")

        try:
            await self._client.__aenter__()
            logger.info(
                f"Connected to MCP server: {self.server_name} via {self.config['transport']}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.server_name}: {e}")
            raise MCPConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._client:
            return

        try:
            await self._client.__aexit__(None, None, None)
            logger.info(f"Disconnected from MCP server: {self.server_name}")
        except Exception as e:
            logger.error(
                f"Failed to disconnect from MCP server {self.server_name}: {e}"
            )
            raise MCPConnectionError(f"Disconnection failed: {e}") from e

    async def reconnect(self) -> None:
        """Reconnect to the MCP server."""
        logger.info(f"Reconnecting to MCP server: {self.server_name}")

        # Disconnect if currently connected
        if self.is_connected():
            await self.disconnect()

        # Reset client creation flag to force recreation
        self._client_created = False
        self._client = None

        # Reconnect
        await self.connect()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        try:
            await self.disconnect()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        if not self._client:
            return False

        if hasattr(self._client, "is_connected"):
            return self._client.is_connected()

        return False

    async def ping(self) -> None:
        """Send ping to server to test connectivity."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        if not self.is_connected():
            raise RuntimeError("Client is not connected to server")

        try:
            await self._client.ping()
            logger.debug(f"Ping successful to server: {self.server_name}")
        except asyncio.TimeoutError as e:
            raise MCPTimeoutError(f"Ping timeout: {e}") from e
        except Exception as e:
            raise MCPProtocolError(f"Ping failed: {e}") from e

    async def list_tools(self) -> "list[MCPTool]":
        """List available tools from the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        if not self.is_connected():
            raise RuntimeError("Client is not connected to server")

        try:
            tools = await self._client.list_tools()
            return [
                MCPTool.from_mcp_result(tool.__dict__, self.server_name or "")
                for tool in tools
            ]
        except asyncio.TimeoutError as e:
            raise MCPTimeoutError(f"List tools timeout: {e}") from e
        except Exception as e:
            raise MCPProtocolError(f"Failed to list tools: {e}") from e

    async def call_tool(
        self, tool_name: str, arguments: "dict[str, Any]"
    ) -> "list[dict[str, Any]]":
        """Call a tool on the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        if not self.is_connected():
            raise RuntimeError("Client is not connected to server")

        try:
            result = await self._client.call_tool(tool_name, arguments)

            # Handle different result formats
            if hasattr(result, "content"):
                return result.content
            elif isinstance(result, list):
                return result
            else:
                return [{"type": "text", "text": str(result)}]

        except asyncio.TimeoutError as e:
            raise MCPTimeoutError(f"Tool call timeout: {e}") from e
        except Exception as e:
            raise MCPProtocolError(f"Tool call failed: {e}") from e

    async def list_resources(self) -> "list[MCPResource]":
        """List available resources from the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        if not self.is_connected():
            raise RuntimeError("Client is not connected to server")

        try:
            resources = await self._client.list_resources()
            return [
                MCPResource.from_mcp_result(resource.__dict__, self.server_name or "")
                for resource in resources
            ]
        except asyncio.TimeoutError as e:
            raise MCPTimeoutError(f"List resources timeout: {e}") from e
        except Exception as e:
            raise MCPProtocolError(f"Failed to list resources: {e}") from e

    async def read_resource(self, uri: str) -> "list[dict[str, Any]]":
        """Read a resource from the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        if not self.is_connected():
            raise RuntimeError("Client is not connected to server")

        try:
            result = await self._client.read_resource(uri)

            # Handle different result formats
            if hasattr(result, "contents"):
                return result.contents
            elif isinstance(result, list):
                return result
            else:
                return [{"type": "text", "text": str(result)}]

        except asyncio.TimeoutError as e:
            raise MCPTimeoutError(f"Read resource timeout: {e}") from e
        except Exception as e:
            raise MCPProtocolError(f"Failed to read resource: {e}") from e

    def _create_request(
        self, method: str, params: "dict[str, Any] | None" = None
    ) -> "dict[str, Any]":
        """Create a JSON-RPC request."""
        self._request_id += 1
        request = {"jsonrpc": "2.0", "id": self._request_id, "method": method}
        if params:
            request["params"] = params
        return request

    def get_server_info(self) -> "dict[str, Any]":
        """Get server information and configuration."""
        return {
            "server_name": self.server_name,
            "transport": self.config.get("transport"),
            "connected": self.is_connected(),
            "config": {
                k: v for k, v in self.config.items() if k not in ["headers", "env"]
            },
        }
