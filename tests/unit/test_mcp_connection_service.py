"""Tests for MCP Connection Service."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from src.my_coding_agent.core.ai_services.mcp_connection_service import (
    MCPConnectionService,
)
from src.my_coding_agent.core.mcp import MCPClient


class TestMCPConnectionService:
    """Test suite for MCPConnectionService."""

    @pytest.fixture
    def service(self):
        """Create MCPConnectionService for testing."""
        return MCPConnectionService()

    @pytest.fixture
    def service_with_signal_handler(self):
        """Create MCPConnectionService with signal handler for testing."""
        signal_handler = Mock()
        signal_handler.mcp_server_registered = Mock()
        signal_handler.mcp_server_unregistered = Mock()
        return MCPConnectionService(signal_handler=signal_handler)

    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mock MCP client."""
        client = Mock(spec=MCPClient)
        client.server_name = "test_server"
        client.is_connected = False
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.list_tools = Mock(return_value=[{"name": "test_tool"}])
        client.server_info = {"version": "1.0.0"}
        return client

    def test_init(self):
        """Test MCPConnectionService initialization."""
        service = MCPConnectionService()
        assert service.signal_handler is None
        assert service.mcp_registry is None
        assert service._mcp_servers_need_connection is False

    def test_init_with_signal_handler(self):
        """Test MCPConnectionService initialization with signal handler."""
        signal_handler = Mock()
        service = MCPConnectionService(signal_handler=signal_handler)
        assert service.signal_handler is signal_handler

    @patch(
        "src.my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
    )
    def test_initialize_mcp_registry_basic(self, mock_registry_class, service):
        """Test basic MCP registry initialization."""
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry

        service.initialize_mcp_registry()

        mock_registry_class.assert_called_once()
        assert service.mcp_registry is mock_registry

    @patch(
        "src.my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
    )
    def test_initialize_mcp_registry_with_auto_discover(
        self, mock_registry_class, service
    ):
        """Test MCP registry initialization with auto-discovery."""
        mock_registry = Mock()
        mock_registry.get_all_servers.return_value = [Mock()]  # Non-empty server list
        mock_registry_class.return_value = mock_registry

        with patch.object(service, "_auto_discover_mcp_servers") as mock_auto_discover:
            # Mock that auto_discover finds servers and sets the flag
            def side_effect():
                service._mcp_servers_need_connection = True

            mock_auto_discover.side_effect = side_effect

            service.initialize_mcp_registry(auto_discover=True)

            mock_auto_discover.assert_called_once()
            assert service._mcp_servers_need_connection is True

    @patch(
        "src.my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
    )
    def test_initialize_mcp_registry_error_handling(self, mock_registry_class, service):
        """Test MCP registry initialization error handling."""
        mock_registry_class.side_effect = Exception("Test error")

        # Should not raise exception
        service.initialize_mcp_registry()
        assert service.mcp_registry is None

    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    @patch("json.load")
    @patch("src.my_coding_agent.core.ai_services.mcp_connection_service.MCPClient")
    def test_auto_discover_mcp_servers_success(
        self, mock_client_class, mock_json_load, mock_exists, mock_open, service
    ):
        """Test successful auto-discovery of MCP servers."""
        # Setup mocks
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "mcpServers": {
                "test_server": {
                    "command": "test_command",
                    "args": ["arg1", "arg2"],
                    "env": {"VAR": "value"},
                }
            }
        }
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_registry = Mock()
        service.mcp_registry = mock_registry

        service._auto_discover_mcp_servers()

        # The MCPClient is now called with a config dict instead of individual parameters
        mock_client_class.assert_called_once_with(
            {
                "server_name": "test_server",
                "transport": "stdio",
                "keep_alive": True,
                "command": "test_command",
                "args": ["arg1", "arg2"],
                "env": {"VAR": "value"},
            }
        )
        mock_registry.register_server.assert_called_once_with(mock_client)

    @patch("pathlib.Path.exists")
    def test_auto_discover_mcp_servers_no_config(self, mock_exists, service):
        """Test auto-discovery when no config file exists."""
        mock_exists.return_value = False
        mock_registry = Mock()
        service.mcp_registry = mock_registry

        service._auto_discover_mcp_servers()

        # Should not call registry methods
        mock_registry.register_server.assert_not_called()

    def test_auto_discover_mcp_servers_no_registry(self, service):
        """Test auto-discovery when no registry is initialized."""
        service.mcp_registry = None

        # Should not raise exception
        service._auto_discover_mcp_servers()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_success(self, service, mock_mcp_client):
        """Test successful connection to MCP servers."""
        mock_registry = Mock()
        mock_registry.connect_all_servers = AsyncMock(
            return_value={"test_server": True}
        )
        mock_registry.update_tools_cache = AsyncMock()
        mock_registry.get_all_tools.return_value = {"test_server": ["tool1", "tool2"]}
        service.mcp_registry = mock_registry

        result = await service.connect_mcp_servers()

        assert result == {"test_server": True}
        mock_registry.connect_all_servers.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_already_connected(
        self, service, mock_mcp_client
    ):
        """Test connection when server is already connected."""
        mock_registry = Mock()
        mock_registry.connect_all_servers = AsyncMock(
            return_value={"test_server": True}
        )
        mock_registry.update_tools_cache = AsyncMock()
        mock_registry.get_all_tools.return_value = {"test_server": ["tool1"]}
        service.mcp_registry = mock_registry

        result = await service.connect_mcp_servers()

        assert result == {"test_server": True}
        mock_registry.connect_all_servers.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_failure(self, service, mock_mcp_client):
        """Test connection failure handling."""
        mock_registry = Mock()
        mock_registry.connect_all_servers = AsyncMock(
            return_value={"test_server": False}
        )
        service.mcp_registry = mock_registry

        result = await service.connect_mcp_servers()

        assert result == {"test_server": False}
        mock_registry.connect_all_servers.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_no_registry(self, service):
        """Test connection when no registry is initialized."""
        service.mcp_registry = None

        result = await service.connect_mcp_servers()

        assert result == {}

    @pytest.mark.asyncio
    async def test_disconnect_mcp_servers(self, service, mock_mcp_client):
        """Test disconnecting from MCP servers."""
        mock_registry = Mock()
        mock_registry.get_all_servers.return_value = [mock_mcp_client]
        service.mcp_registry = mock_registry

        await service.disconnect_mcp_servers()

        mock_mcp_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_mcp_servers_no_registry(self, service):
        """Test disconnection when no registry is initialized."""
        service.mcp_registry = None

        # Should not raise exception
        await service.disconnect_mcp_servers()

    @patch(
        "src.my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
    )
    def test_register_mcp_server(
        self, mock_registry_class, service_with_signal_handler, mock_mcp_client
    ):
        """Test registering an MCP server."""
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry

        service_with_signal_handler.register_mcp_server(mock_mcp_client)

        mock_registry_class.assert_called_once()
        mock_registry.register_server.assert_called_once_with(mock_mcp_client)
        service_with_signal_handler.signal_handler.mcp_server_registered.emit.assert_called_once_with(
            "test_server"
        )

    def test_register_mcp_server_no_signal_handler(self, service, mock_mcp_client):
        """Test registering an MCP server without signal handler."""
        with patch(
            "src.my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
        ) as mock_registry_class:
            mock_registry = Mock()
            mock_registry_class.return_value = mock_registry

            service.register_mcp_server(mock_mcp_client)

            mock_registry.register_server.assert_called_once_with(mock_mcp_client)

    def test_unregister_mcp_server_success(self, service_with_signal_handler):
        """Test successful unregistering of an MCP server."""
        mock_registry = Mock()
        mock_registry.unregister_server.return_value = True
        service_with_signal_handler.mcp_registry = mock_registry

        result = service_with_signal_handler.unregister_mcp_server("test_server")

        assert result is True
        mock_registry.unregister_server.assert_called_once_with("test_server")
        service_with_signal_handler.signal_handler.mcp_server_unregistered.emit.assert_called_once_with(
            "test_server"
        )

    def test_unregister_mcp_server_failure(self, service):
        """Test unsuccessful unregistering of an MCP server."""
        mock_registry = Mock()
        mock_registry.unregister_server.return_value = False
        service.mcp_registry = mock_registry

        result = service.unregister_mcp_server("test_server")

        assert result is False

    def test_unregister_mcp_server_no_registry(self, service):
        """Test unregistering when no registry is initialized."""
        service.mcp_registry = None

        result = service.unregister_mcp_server("test_server")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_mcp_server_status_no_registry(self, service):
        """Test getting server status when no registry is initialized."""
        service.mcp_registry = None

        result = await service.get_mcp_server_status()

        expected = {
            "servers": {},
            "total_servers": 0,
            "connected_servers": 0,
            "available_tools": 0,
        }
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_mcp_server_status_with_servers(self, service, mock_mcp_client):
        """Test getting server status with connected servers."""
        mock_mcp_client.is_connected = True
        mock_registry = Mock()
        mock_registry.get_all_servers.return_value = [mock_mcp_client]
        service.mcp_registry = mock_registry

        result = await service.get_mcp_server_status()

        expected = {
            "servers": {
                "test_server": {
                    "connected": True,
                    "tools": [{"name": "test_tool"}],
                    "tool_count": 1,
                    "server_info": {"version": "1.0.0"},
                }
            },
            "total_servers": 1,
            "connected_servers": 1,
            "available_tools": 1,
        }
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_mcp_server_status_async_tools(self, service):
        """Test getting server status with async list_tools method."""
        mock_client = Mock()
        mock_client.server_name = "async_server"
        mock_client.is_connected = True
        mock_client.list_tools = AsyncMock(return_value=[{"name": "async_tool"}])
        mock_client.server_info = {}

        mock_registry = Mock()
        mock_registry.get_all_servers.return_value = [mock_client]
        service.mcp_registry = mock_registry

        result = await service.get_mcp_server_status()

        assert result["servers"]["async_server"]["tool_count"] == 1
        assert result["available_tools"] == 1

    @pytest.mark.asyncio
    async def test_ensure_mcp_servers_connected_success(self, service):
        """Test ensuring MCP servers are connected successfully."""
        # Mock the registry so the service doesn't return False early
        mock_registry = Mock()
        service.mcp_registry = mock_registry

        with patch.object(
            service,
            "connect_mcp_servers",
            new_callable=AsyncMock,
            return_value={"server1": True, "server2": True},
        ):
            result = await service.ensure_mcp_servers_connected()
            assert result is True

    @pytest.mark.asyncio
    async def test_ensure_mcp_servers_connected_partial_failure(self, service):
        """Test ensuring MCP servers are connected with partial failure."""
        # Mock the registry so the service doesn't return False early
        mock_registry = Mock()
        service.mcp_registry = mock_registry

        with patch.object(
            service,
            "connect_mcp_servers",
            new_callable=AsyncMock,
            return_value={"server1": True, "server2": False},
        ):
            result = await service.ensure_mcp_servers_connected()
            assert result is False

    @pytest.mark.asyncio
    async def test_ensure_mcp_servers_connected_no_registry(self, service):
        """Test ensuring MCP servers are connected when no registry exists."""
        service.mcp_registry = None
        result = await service.ensure_mcp_servers_connected()
        assert result is False

    def test_has_mcp_servers_true(self, service):
        """Test has_mcp_servers property when servers exist."""
        mock_registry = Mock()
        mock_registry.get_all_servers.return_value = [Mock()]
        service.mcp_registry = mock_registry

        assert service.has_mcp_servers is True

    def test_has_mcp_servers_false_no_servers(self, service):
        """Test has_mcp_servers property when no servers exist."""
        mock_registry = Mock()
        mock_registry.get_all_servers.return_value = []
        service.mcp_registry = mock_registry

        assert service.has_mcp_servers is False

    def test_has_mcp_servers_false_no_registry(self, service):
        """Test has_mcp_servers property when no registry exists."""
        service.mcp_registry = None
        assert service.has_mcp_servers is False

    def test_connected_server_count(self, service):
        """Test connected_server_count property."""
        mock_client1 = Mock()
        mock_client1.is_connected = True
        mock_client2 = Mock()
        mock_client2.is_connected = False

        mock_registry = Mock()
        mock_registry.get_all_servers.return_value = [mock_client1, mock_client2]
        service.mcp_registry = mock_registry

        assert service.connected_server_count == 1

    def test_connected_server_count_no_registry(self, service):
        """Test connected_server_count property when no registry exists."""
        service.mcp_registry = None
        assert service.connected_server_count == 0
