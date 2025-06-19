"""
Unit tests for MCPClientCoordinator - the simplified MCP client interface.

This coordinator replaces the complex AIAgent with a focused MCP communication layer.
"""

from unittest.mock import AsyncMock, patch

import pytest
from src.my_coding_agent.core.mcp_client_coordinator import (
    MCPClientCoordinator,
    MCPCoordinatorConfig,
    MCPResponse,
    StreamingMCPResponse,
)


class TestMCPClientCoordinator:
    """Test suite for MCPClientCoordinator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = MCPCoordinatorConfig(
            server_url="http://localhost:8080",
            timeout=30.0,
            enable_streaming=True,
            max_retries=3,
        )
        self.coordinator = MCPClientCoordinator(self.config)

    def test_coordinator_initialization(self):
        """Test MCPClientCoordinator initializes correctly."""
        assert self.coordinator.config == self.config
        assert self.coordinator.server_url == "http://localhost:8080"
        assert self.coordinator.timeout == 30.0
        assert self.coordinator.enable_streaming is True
        assert self.coordinator.max_retries == 3
        assert self.coordinator.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_to_mcp_server(self):
        """Test successful connection to MCP server."""
        with patch.object(
            self.coordinator, "_establish_connection", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.return_value = True

            result = await self.coordinator.connect()

            assert result is True
            assert self.coordinator.is_connected is True
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_to_mcp_server_failure(self):
        """Test connection failure handling."""
        with patch.object(
            self.coordinator, "_establish_connection", new_callable=AsyncMock
        ) as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            result = await self.coordinator.connect()

            assert result is False
            assert self.coordinator.is_connected is False

    @pytest.mark.asyncio
    async def test_send_message_basic(self):
        """Test sending a basic message through MCP."""
        # Mock connection
        self.coordinator.is_connected = True

        expected_response = MCPResponse(
            content="Hello! How can I help you?",
            metadata={"tokens_used": 15, "model": "gpt-4"},
            tool_calls=[],
            code_blocks=[],
        )

        with patch.object(
            self.coordinator, "_send_mcp_message", new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = expected_response

            response = await self.coordinator.send_message("Hello")

            assert response == expected_response
            assert response.content == "Hello! How can I help you?"
            assert response.metadata["tokens_used"] == 15
            mock_send.assert_called_once_with("Hello", streaming=False)

    @pytest.mark.asyncio
    async def test_send_message_with_streaming(self):
        """Test sending message with streaming enabled."""
        self.coordinator.is_connected = True

        # Mock streaming response
        async def mock_stream():
            yield StreamingMCPResponse(content="Hello", is_complete=False)
            yield StreamingMCPResponse(content=" there!", is_complete=False)
            yield StreamingMCPResponse(
                content="", is_complete=True, metadata={"tokens": 10}
            )

        with patch.object(
            self.coordinator, "_send_mcp_message_streaming"
        ) as mock_stream_send:
            mock_stream_send.return_value = mock_stream()

            responses = []
            async for response in self.coordinator.send_message_streaming("Hello"):
                responses.append(response)

            assert len(responses) == 3
            assert responses[0].content == "Hello"
            assert responses[1].content == " there!"
            assert responses[2].is_complete is True
            mock_stream_send.assert_called_once_with("Hello")

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self):
        """Test sending message when not connected."""
        self.coordinator.is_connected = False

        with pytest.raises(RuntimeError, match="Not connected to MCP server"):
            await self.coordinator.send_message("Hello")

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from MCP server."""
        self.coordinator.is_connected = True

        with patch.object(
            self.coordinator, "_close_connection", new_callable=AsyncMock
        ) as mock_close:
            await self.coordinator.disconnect()

            assert self.coordinator.is_connected is False
            mock_close.assert_called_once()

    def test_coordinator_config_validation(self):
        """Test MCPCoordinatorConfig validation."""
        # Valid config
        config = MCPCoordinatorConfig(server_url="http://localhost:8080", timeout=30.0)
        assert config.server_url == "http://localhost:8080"
        assert config.timeout == 30.0
        assert config.enable_streaming is True  # default
        assert config.max_retries == 3  # default

    def test_mcp_response_structure(self):
        """Test MCPResponse data structure."""
        response = MCPResponse(
            content="Test response",
            metadata={"model": "gpt-4"},
            tool_calls=[{"name": "test_tool", "args": {}}],
            code_blocks=[{"language": "python", "code": "print('hello')"}],
        )

        assert response.content == "Test response"
        assert response.metadata["model"] == "gpt-4"
        assert len(response.tool_calls) == 1
        assert len(response.code_blocks) == 1

    def test_streaming_mcp_response_structure(self):
        """Test StreamingMCPResponse data structure."""
        response = StreamingMCPResponse(
            content="Partial response", is_complete=False, metadata={"partial": True}
        )

        assert response.content == "Partial response"
        assert response.is_complete is False
        assert response.metadata["partial"] is True

    @pytest.mark.asyncio
    async def test_error_handling_with_retries(self):
        """Test error handling with retry logic."""
        self.coordinator.is_connected = True

        with patch.object(
            self.coordinator, "_send_mcp_message", new_callable=AsyncMock
        ) as mock_send:
            # First two calls fail, third succeeds
            mock_send.side_effect = [
                Exception("Temporary error"),
                Exception("Another temp error"),
                MCPResponse(
                    content="Success!", metadata={}, tool_calls=[], code_blocks=[]
                ),
            ]

            response = await self.coordinator.send_message("Hello")

            assert response.content == "Success!"
            assert mock_send.call_count == 3

    @pytest.mark.asyncio
    async def test_error_handling_max_retries_exceeded(self):
        """Test error handling when max retries exceeded."""
        self.coordinator.is_connected = True

        with patch.object(
            self.coordinator, "_send_mcp_message", new_callable=AsyncMock
        ) as mock_send:
            mock_send.side_effect = Exception("Persistent error")

            with pytest.raises(RuntimeError, match="Max retries exceeded"):
                await self.coordinator.send_message("Hello")

            assert mock_send.call_count == 3  # max_retries
