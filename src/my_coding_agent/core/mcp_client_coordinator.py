"""
MCP Client Coordinator - Simplified MCP communication interface.

This module provides a focused, lightweight interface for communicating with
MCP (Model Context Protocol) servers, replacing the complex AIAgent architecture.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MCPCoordinatorConfig:
    """Configuration for MCP Client Coordinator."""

    server_url: str
    timeout: float = 30.0
    enable_streaming: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class MCPResponse:
    """Response from MCP server."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    code_blocks: list[dict[str, str]] = field(default_factory=list)


@dataclass
class StreamingMCPResponse:
    """Streaming response chunk from MCP server."""

    content: str
    is_complete: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    code_blocks: list[dict[str, str]] = field(default_factory=list)


class MCPClientCoordinator:
    """
    Simplified MCP Client Coordinator.

    Provides a clean, focused interface for communicating with MCP servers,
    replacing the complex AIAgent with a streamlined approach.
    """

    def __init__(self, config: MCPCoordinatorConfig) -> None:
        """Initialize the MCP Client Coordinator."""
        self.config = config
        self.is_connected = False
        self._session: aiohttp.ClientSession | None = None

        # Expose config properties for easy access
        self.server_url = config.server_url
        self.timeout = config.timeout
        self.enable_streaming = config.enable_streaming
        self.max_retries = config.max_retries

    async def connect(self) -> bool:
        """
        Connect to the MCP server.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            await self._establish_connection()
            self.is_connected = True
            logger.info(f"Successfully connected to MCP server at {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        await self._close_connection()
        self.is_connected = False
        logger.info("Disconnected from MCP server")

    async def cleanup(self) -> None:
        """Clean up resources and ensure proper session closure."""
        await self.disconnect()

    def __del__(self) -> None:
        """Destructor to ensure session cleanup."""
        if self._session and not self._session.closed:
            # Note: This is a fallback - proper cleanup should use disconnect() or cleanup()
            import warnings
            warnings.warn(
                "MCPClientCoordinator session not properly closed. Call disconnect() or cleanup().",
                ResourceWarning,
                stacklevel=2
            )

    async def send_message(self, message: str) -> MCPResponse:
        """
        Send a message to the MCP server.

        Args:
            message: The message to send

        Returns:
            MCPResponse: The response from the server

        Raises:
            RuntimeError: If not connected to server or max retries exceeded
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to MCP server")

        # Implement retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await self._send_mcp_message(message, streaming=False)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    logger.warning(f"Retry {attempt + 1} after error: {e}")

        raise RuntimeError(f"Max retries exceeded. Last error: {last_exception}")

    async def send_message_streaming(
        self, message: str
    ) -> AsyncIterator[StreamingMCPResponse]:
        """
        Send a message with streaming response.

        Args:
            message: The message to send

        Yields:
            StreamingMCPResponse: Streaming response chunks

        Raises:
            RuntimeError: If not connected to server
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to MCP server")

        async for response in self._send_mcp_message_streaming(message):
            yield response

    async def _establish_connection(self) -> None:
        """Establish connection to MCP server."""
        # Create aiohttp session with timeout
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)

        # Test connection with a simple health check
        try:
            async with self._session.get(f"{self.server_url}/health") as response:
                if response.status != 200:
                    raise Exception(f"Server returned status {response.status}")
        except Exception as e:
            await self._close_connection()
            raise Exception(f"Connection test failed: {e}") from e

    async def _close_connection(self) -> None:
        """Close connection to MCP server."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _send_mcp_message(
        self, message: str, streaming: bool = False
    ) -> MCPResponse:
        """
        Internal method to send message to MCP server.

        Args:
            message: Message to send
            streaming: Whether to use streaming (for internal use)

        Returns:
            MCPResponse: Server response
        """
        if not self._session:
            raise RuntimeError("No active session")

        payload = {
            "message": message,
            "streaming": streaming,
            "timestamp": asyncio.get_event_loop().time(),
        }

        try:
            async with self._session.post(
                f"{self.server_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Server error: {response.status}")

                data = await response.json()

                return MCPResponse(
                    content=data.get("content", ""),
                    metadata=data.get("metadata", {}),
                    tool_calls=data.get("tool_calls", []),
                    code_blocks=data.get("code_blocks", []),
                )

        except Exception as e:
            logger.error(f"Error sending MCP message: {e}")
            raise

    async def _send_mcp_message_streaming(
        self, message: str
    ) -> AsyncIterator[StreamingMCPResponse]:
        """
        Internal method to send streaming message to MCP server.

        Args:
            message: Message to send

        Yields:
            StreamingMCPResponse: Streaming response chunks
        """
        if not self._session:
            raise RuntimeError("No active session")

        payload = {
            "message": message,
            "streaming": True,
            "timestamp": asyncio.get_event_loop().time(),
        }

        try:
            async with self._session.post(
                f"{self.server_url}/chat/stream",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    raise Exception(f"Server error: {response.status}")

                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8").strip())
                            yield StreamingMCPResponse(
                                content=data.get("content", ""),
                                is_complete=data.get("is_complete", False),
                                metadata=data.get("metadata", {}),
                                tool_calls=data.get("tool_calls", []),
                                code_blocks=data.get("code_blocks", []),
                            )
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue

        except Exception as e:
            logger.error(f"Error in streaming MCP message: {e}")
            raise
