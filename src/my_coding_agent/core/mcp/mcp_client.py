"""
FastMCP client implementation for JSON-RPC protocol support.

This module provides a comprehensive MCP client implementation that wraps
the FastMCP library with additional features including support for multiple
transport protocols (stdio, HTTP, SSE, WebSocket) and OAuth 2.0 authentication.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from fastmcp import Client

from .error_handler import (
    MCPErrorHandler,
)
from .oauth2_auth import OAuth2AuthenticationError, OAuth2Authenticator, OAuth2Config

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
        self.oauth2_authenticator: OAuth2Authenticator | None = None
        self._connected = False  # Track connection state manually

        # Initialize error handler
        error_config = config.get("error_handling", {})
        self.error_handler = MCPErrorHandler(error_config)

        # Initialize OAuth 2.0 authenticator if configured
        if "oauth2" in self.config:
            self._initialize_oauth2_authenticator()

        # Auto-detect transport if not specified
        if "transport" not in self.config:
            self.config["transport"] = self._detect_transport_from_config()

        # Validate configuration
        self._validate_config()

        # Defer client creation until connection
        self._client_created = False

    def _initialize_oauth2_authenticator(self) -> None:
        """Initialize OAuth 2.0 authenticator from configuration."""
        try:
            oauth2_config = OAuth2Config.from_dict(self.config["oauth2"])
            self.oauth2_authenticator = OAuth2Authenticator(oauth2_config)
            logger.info(f"OAuth 2.0 authenticator initialized for server: {self.server_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OAuth 2.0 authenticator: {e}")
            raise ValueError(f"Invalid OAuth 2.0 configuration: {e}")

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

        # Validate that OAuth 2.0 is only used with HTTP-based transports
        if self.oauth2_authenticator and transport not in ["http", "sse", "websocket"]:
            raise ValueError("OAuth 2.0 authentication is only supported with HTTP-based transports")

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
        command = self.config.get("command", "python")
        args = self.config.get("args", [])

        # Handle npx commands specially
        if command == "npx" and args:
            # For npx commands, we need to use NpxStdioTransport
            from fastmcp.client.transports import NpxStdioTransport

            # Extract package name (skip -y flag if present)
            package_name = None
            package_args = []

            for i, arg in enumerate(args):
                if arg == "-y":
                    continue  # Skip the -y flag
                elif not package_name:
                    package_name = arg  # First non-flag argument is the package
                else:
                    package_args.append(arg)  # Remaining args go to the package

            if package_name:
                transport = NpxStdioTransport(
                    package=package_name,
                    args=package_args if package_args else None
                )
                self._client = Client(transport)
            else:
                raise ValueError("No package name found in npx command arguments")
        elif args:
            # Use the script path for FastMCP auto-detection
            self._client = Client(args[0])
        else:
            # Fallback to command if no args
            self._client = Client(command)

    def _create_http_client(self) -> None:
        """Create HTTP transport client."""
        url = self.config.get("url")
        headers = self.config.get("headers", {})

        # Add OAuth 2.0 authentication header if available
        if self.oauth2_authenticator and self.oauth2_authenticator.is_authenticated():
            auth_header = self.oauth2_authenticator.to_authorization_header()
            if auth_header:
                headers.update(auth_header)

        from fastmcp.client.transports import HttpTransport

        transport = HttpTransport(url=url, headers=headers)
        self._client = Client(transport=transport)

    def _create_sse_client(self) -> None:
        """Create Server-Sent Events transport client."""
        url = self.config.get("url")
        headers = self.config.get("headers", {})

        # Add OAuth 2.0 authentication header if available
        if self.oauth2_authenticator and self.oauth2_authenticator.is_authenticated():
            auth_header = self.oauth2_authenticator.to_authorization_header()
            if auth_header:
                headers.update(auth_header)

        from fastmcp.client.transports import SseTransport

        transport = SseTransport(url=url, headers=headers)
        self._client = Client(transport=transport)

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
        # Authenticate with OAuth 2.0 if configured
        if self.oauth2_authenticator and not self.oauth2_authenticator.is_authenticated():
            logger.info(f"Performing OAuth 2.0 authentication for server: {self.server_name}")
            await self.authenticate_oauth2()

        # Ensure we create the client in the current event loop context
        self._create_client()

        if not self._client:
            raise MCPConnectionError("Client not initialized")

        try:
            # Check if we're in a different event loop context
            try:
                current_loop = asyncio.get_running_loop()
                logger.debug(f"Connecting {self.server_name} in event loop: {current_loop}")
            except RuntimeError:
                logger.warning(f"No event loop running during {self.server_name} connection")

            # For FastMCP, we don't need to maintain persistent connections
            # The context manager handles connection lifecycle for each call
            self._connected = True  # Mark as connected
            logger.info(
                f"Connected to MCP server: {self.server_name} via {self.config['transport']}"
            )
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to MCP server {self.server_name}: {e}")
            raise MCPConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._client:
            return

        try:
            # Check if the client is still valid and the event loop is running
            try:
                current_loop = asyncio.get_running_loop()
                logger.debug(f"Disconnecting {self.server_name} in event loop: {current_loop}")
            except RuntimeError:
                logger.warning(f"No event loop running during {self.server_name} disconnection")
                # If no event loop, just mark as disconnected
                self._connected = False
                return

            # For FastMCP, we don't need to explicitly disconnect
            # The context manager handles this automatically
            self._connected = False  # Mark as disconnected
            logger.info(f"Disconnected from MCP server: {self.server_name}")
        except Exception as e:
            self._connected = False  # Mark as disconnected even on error
            logger.error(
                f"Failed to disconnect from MCP server {self.server_name}: {e}"
            )
            # Don't raise exception on disconnect failure

    async def reconnect(self) -> None:
        """Reconnect to the MCP server."""
        logger.info(f"Reconnecting to MCP server: {self.server_name}")

        # Disconnect if currently connected
        if self.is_connected():
            await self.disconnect()

        # Reset client creation flag to force recreation in current event loop
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
        return self._connected and self._client is not None

    async def ping(self) -> None:
        """Send ping to server to test connectivity."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        if not self.is_connected():
            raise RuntimeError("Client is not connected to server")

        try:
            # Check if we're in a valid event loop context
            try:
                current_loop = asyncio.get_running_loop()
                logger.debug(f"Pinging {self.server_name} in event loop: {current_loop}")
            except RuntimeError:
                raise MCPConnectionError("No event loop available for ping operation")

            await self._client.ping()
            logger.debug(f"Ping successful to server: {self.server_name}")
        except asyncio.TimeoutError as e:
            raise MCPTimeoutError(f"Ping timeout: {e}") from e
        except Exception as e:
            # Check if this is an event loop issue
            if "loop" in str(e).lower() or "event" in str(e).lower():
                logger.warning(f"Event loop issue during ping for {self.server_name}: {e}")
                self._connected = False  # Mark as disconnected
                raise MCPConnectionError(f"Event loop issue during ping: {e}") from e
            raise MCPProtocolError(f"Ping failed: {e}") from e

    async def list_tools(self) -> "list[MCPTool]":
        """List available tools from the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        try:
            # Use the client within its context manager
            async with self._client as client:
                result = await client.list_tools()

                # Convert result to MCPTool objects
                tools = []
                if hasattr(result, "tools"):
                    for tool_data in result.tools:
                        if hasattr(tool_data, "model_dump"):
                            tool_dict = tool_data.model_dump()
                        elif hasattr(tool_data, "__dict__"):
                            tool_dict = tool_data.__dict__
                        else:
                            tool_dict = dict(tool_data) if hasattr(tool_data, '__iter__') else {"name": str(tool_data)}

                        tools.append(MCPTool.from_mcp_result(tool_dict, self.server_name or ""))
                elif isinstance(result, list):
                    for tool_data in result:
                        if hasattr(tool_data, "model_dump"):
                            tool_dict = tool_data.model_dump()
                        elif hasattr(tool_data, "__dict__"):
                            tool_dict = tool_data.__dict__
                        else:
                            tool_dict = dict(tool_data) if hasattr(tool_data, '__iter__') else {"name": str(tool_data)}

                        tools.append(MCPTool.from_mcp_result(tool_dict, self.server_name or ""))

                return tools

        except asyncio.TimeoutError as e:
            self._record_error(e, "list_tools")
            raise MCPTimeoutError(f"List tools timeout: {e}") from e
        except Exception as e:
            self._record_error(e, "list_tools")
            # Check if this is a connection issue
            if "not connected" in str(e).lower() or "context manager" in str(e).lower():
                self._connected = False  # Mark as disconnected
                raise MCPConnectionError(f"List tools failed: {e}") from e
            raise MCPProtocolError(f"List tools failed: {e}") from e

    def _record_error(self, error: Exception, operation: str) -> None:
        """Record error in error handler metrics."""
        server_name = self.server_name or "unknown"
        context = self.error_handler.create_error_context(
            error=error,
            server_name=server_name,
            operation=operation
        )
        self.error_handler.metrics.record_error(context)

    async def call_tool(
        self, tool_name: str, arguments: "dict[str, Any]"
    ) -> "list[dict[str, Any]]":
        """Call a tool on the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        # For FastMCP clients, we need to use the context manager for each call
        try:
            # Use the client within its context manager
            async with self._client as client:
                result = await client.call_tool(tool_name, arguments)

                # Handle different result formats and convert to dict format
                if hasattr(result, "content"):
                    # Convert content list to dict format
                    content_list = []
                    for item in result.content:
                        if hasattr(item, "__dict__"):
                            content_list.append(item.__dict__)
                        elif hasattr(item, "model_dump"):
                            content_list.append(item.model_dump())
                        elif isinstance(item, dict):
                            content_list.append(item)
                        else:
                            content_list.append({"text": str(item)})
                    return content_list
                elif hasattr(result, "model_dump"):
                    # Handle Pydantic models
                    result_dict = result.model_dump()
                    content = result_dict.get("content")
                    if content and isinstance(content, list):
                        return [{"text": str(item)} for item in content]
                    return [result_dict]
                elif isinstance(result, dict):
                    # Handle dict results
                    content = result.get("content")
                    if content and isinstance(content, list):
                        return [{"text": str(item)} for item in content]
                    return [result]
                elif isinstance(result, list):
                    # Handle list results
                    return [{"text": str(item)} if not isinstance(item, dict) else item for item in result]
                else:
                    # Handle other types
                    return [{"text": str(result)}]

        except asyncio.TimeoutError as e:
            self._record_error(e, f"call_tool({tool_name})")
            raise MCPTimeoutError(f"Tool call timeout: {e}") from e
        except Exception as e:
            self._record_error(e, f"call_tool({tool_name})")
            # Check if this is a connection issue
            if "not connected" in str(e).lower() or "context manager" in str(e).lower():
                self._connected = False  # Mark as disconnected
                raise MCPConnectionError(f"Tool call failed: {e}") from e
            raise MCPProtocolError(f"Tool call failed: {e}") from e

    async def list_resources(self) -> "list[MCPResource]":
        """List available resources from the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        try:
            # Use the client within its context manager
            async with self._client as client:
                result = await client.list_resources()

                # Convert result to MCPResource objects
                resources = []
                if hasattr(result, "resources"):
                    for resource_data in result.resources:
                        if hasattr(resource_data, "model_dump"):
                            resource_dict = resource_data.model_dump()
                        elif hasattr(resource_data, "__dict__"):
                            resource_dict = resource_data.__dict__
                        else:
                            resource_dict = dict(resource_data) if hasattr(resource_data, '__iter__') else {"uri": str(resource_data)}

                        resources.append(MCPResource.from_mcp_result(resource_dict, self.server_name or ""))

                return resources

        except asyncio.TimeoutError as e:
            self._record_error(e, "list_resources")
            raise MCPTimeoutError(f"List resources timeout: {e}") from e
        except Exception as e:
            self._record_error(e, "list_resources")
            # Check if this is a connection issue
            if "not connected" in str(e).lower() or "context manager" in str(e).lower():
                self._connected = False  # Mark as disconnected
                raise MCPConnectionError(f"List resources failed: {e}") from e
            raise MCPProtocolError(f"List resources failed: {e}") from e

    async def read_resource(self, uri: str) -> "list[dict[str, Any]]":
        """Read a resource from the MCP server."""
        if not self._client:
            raise RuntimeError("Client is not initialized")

        try:
            # Use the client within its context manager
            async with self._client as client:
                result = await client.read_resource(uri)

                # Handle different result formats and convert to dict format
                if hasattr(result, "contents"):
                    # Convert contents list to dict format
                    content_list = []
                    for item in result.contents:
                        if hasattr(item, "__dict__"):
                            content_list.append(item.__dict__)
                        elif hasattr(item, "model_dump"):
                            content_list.append(item.model_dump())
                        elif isinstance(item, dict):
                            content_list.append(item)
                        else:
                            content_list.append({"text": str(item)})
                    return content_list
                elif hasattr(result, "model_dump"):
                    # Handle Pydantic models
                    result_dict = result.model_dump()
                    contents = result_dict.get("contents")
                    if contents and isinstance(contents, list):
                        return [{"text": str(item)} for item in contents]
                    return [result_dict]
                elif isinstance(result, dict):
                    # Handle dict results
                    contents = result.get("contents")
                    if contents and isinstance(contents, list):
                        return [{"text": str(item)} for item in contents]
                    return [result]
                elif isinstance(result, list):
                    # Handle list results
                    return [{"text": str(item)} if not isinstance(item, dict) else item for item in result]
                else:
                    # Handle other types
                    return [{"text": str(result)}]

        except asyncio.TimeoutError as e:
            self._record_error(e, f"read_resource({uri})")
            raise MCPTimeoutError(f"Read resource timeout: {e}") from e
        except Exception as e:
            self._record_error(e, f"read_resource({uri})")
            # Check if this is a connection issue
            if "not connected" in str(e).lower() or "context manager" in str(e).lower():
                self._connected = False  # Mark as disconnected
                raise MCPConnectionError(f"Read resource failed: {e}") from e
            raise MCPProtocolError(f"Read resource failed: {e}") from e

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

    async def authenticate_oauth2(self, flow_type: str = "client_credentials") -> None:
        """
        Authenticate using OAuth 2.0.

        Args:
            flow_type: OAuth 2.0 flow type ("client_credentials" or "authorization_code")

        Raises:
            MCPConnectionError: If OAuth 2.0 authentication fails
        """
        if not self.oauth2_authenticator:
            raise MCPConnectionError("OAuth 2.0 not configured for this client")

        try:
            if flow_type == "client_credentials":
                await self.oauth2_authenticator.client_credentials_flow()
            elif flow_type == "authorization_code":
                # Note: This requires external authorization code flow handling
                raise ValueError("Authorization code flow requires external handling")
            else:
                raise ValueError(f"Unsupported OAuth 2.0 flow type: {flow_type}")

            logger.info(f"OAuth 2.0 authentication successful for server: {self.server_name}")

        except OAuth2AuthenticationError as e:
            logger.error(f"OAuth 2.0 authentication failed for server {self.server_name}: {e}")
            raise MCPConnectionError(f"OAuth 2.0 authentication failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during OAuth 2.0 authentication: {e}")
            raise MCPConnectionError(f"OAuth 2.0 authentication failed: {e}") from e

    async def get_oauth2_authorization_url(self) -> str:
        """
        Get OAuth 2.0 authorization URL for authorization code flow.

        Returns:
            Authorization URL

        Raises:
            MCPConnectionError: If OAuth 2.0 not configured
        """
        if not self.oauth2_authenticator:
            raise MCPConnectionError("OAuth 2.0 not configured for this client")

        try:
            return self.oauth2_authenticator.generate_authorization_url()
        except Exception as e:
            logger.error(f"Failed to generate OAuth 2.0 authorization URL: {e}")
            raise MCPConnectionError(f"Failed to generate authorization URL: {e}") from e

    async def exchange_oauth2_code(self, authorization_code: str, state: str) -> None:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from OAuth provider
            state: State parameter for validation

        Raises:
            MCPConnectionError: If code exchange fails
        """
        if not self.oauth2_authenticator:
            raise MCPConnectionError("OAuth 2.0 not configured for this client")

        try:
            await self.oauth2_authenticator.exchange_code_for_token(authorization_code, state)
            logger.info(f"OAuth 2.0 code exchange successful for server: {self.server_name}")

        except OAuth2AuthenticationError as e:
            logger.error(f"OAuth 2.0 code exchange failed for server {self.server_name}: {e}")
            raise MCPConnectionError(f"OAuth 2.0 code exchange failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during OAuth 2.0 code exchange: {e}")
            raise MCPConnectionError(f"OAuth 2.0 code exchange failed: {e}") from e

    def is_oauth2_authenticated(self) -> bool:
        """
        Check if OAuth 2.0 authentication is active.

        Returns:
            True if authenticated with valid OAuth 2.0 token
        """
        return self.oauth2_authenticator is not None and self.oauth2_authenticator.is_authenticated()

    def get_oauth2_token_info(self) -> Optional["dict[str, Any]"]:
        """
        Get OAuth 2.0 token information.

        Returns:
            Token information dictionary or None if not authenticated
        """
        if not self.oauth2_authenticator:
            return None

        return self.oauth2_authenticator.get_token_info()

    async def list_tools_with_retry(self, max_attempts: int | None = None) -> "list[MCPTool]":
        """List available tools with retry logic."""
        server_name = self.server_name or "unknown"
        return await self.error_handler.execute_with_retry(
            operation=self.list_tools,
            server_name=server_name,
            operation_name="list_tools",
            max_attempts=max_attempts
        )

    async def list_tools_with_fallback(self) -> "list[MCPTool]":
        """List available tools with fallback to empty list on failure."""
        try:
            return await self.list_tools()
        except Exception as error:
            server_name = self.server_name or "unknown"
            context = self.error_handler.create_error_context(
                error=error,
                server_name=server_name,
                operation="list_tools"
            )
            self.error_handler.metrics.record_error(context)
            logger.warning(f"Failed to list tools from {server_name}, using fallback: {error}")
            return []

    def get_error_report(self) -> "dict[str, Any]":
        """Get comprehensive error report."""
        return self.error_handler.get_error_report()
