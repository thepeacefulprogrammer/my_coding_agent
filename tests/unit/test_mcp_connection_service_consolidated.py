"""Comprehensive tests for consolidated MCPConnectionService."""

import json
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from my_coding_agent.core.ai_services.mcp_connection_service import MCPConnectionService
from my_coding_agent.core.mcp import MCPClient, MCPServerRegistry
from my_coding_agent.core.mcp_file_server import MCPFileConfig


class TestMCPConnectionServiceInitialization:
    """Test MCPConnectionService initialization and basic setup."""

    def test_initialization_default(self):
        """Test default initialization."""
        service = MCPConnectionService()

        assert service.signal_handler is None
        assert service.tool_registration_service is None
        assert service.mcp_registry is None
        assert service._mcp_servers_need_connection is False
        assert service._mcp_tools_registered is False
        assert service.mcp_file_server is None

    def test_initialization_with_handlers(self):
        """Test initialization with signal handler and tool registration service."""
        signal_handler = Mock()
        tool_service = Mock()

        service = MCPConnectionService(
            signal_handler=signal_handler, tool_registration_service=tool_service
        )

        assert service.signal_handler is signal_handler
        assert service.tool_registration_service is tool_service

    def test_logging_setup(self):
        """Test that logging is properly configured."""
        with patch("logging.basicConfig") as mock_config:
            MCPConnectionService()
            mock_config.assert_called_once()


class TestMCPRegistryInitialization:
    """Test MCP registry initialization and auto-discovery."""

    def test_initialize_mcp_registry_basic(self):
        """Test basic MCP registry initialization."""
        service = MCPConnectionService()

        with patch(
            "my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
        ) as mock_registry:
            service.initialize_mcp_registry(auto_discover=False)

            mock_registry.assert_called_once()
            assert service.mcp_registry is not None

    def test_initialize_mcp_registry_with_auto_discover(self):
        """Test MCP registry initialization with auto-discovery."""
        service = MCPConnectionService()

        with (
            patch(
                "my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
            ) as mock_registry,
            patch.object(service, "_auto_discover_mcp_servers") as mock_discover,
        ):
            service.initialize_mcp_registry(auto_discover=True)

            mock_registry.assert_called_once()
            mock_discover.assert_called_once()

    def test_initialize_mcp_registry_error_handling(self):
        """Test error handling during registry initialization."""
        service = MCPConnectionService()

        with patch(
            "my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry",
            side_effect=Exception("Registry error"),
        ):
            service.initialize_mcp_registry()

            assert service.mcp_registry is None


class TestEnhancedAutoDiscovery:
    """Test enhanced auto-discovery functionality."""

    def test_auto_discover_enhanced_method(self):
        """Test enhanced auto-discovery using load_default_mcp_config."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock the enhanced config loading
        mock_config = Mock()
        mock_servers = {
            "server1": Mock(
                to_dict=Mock(return_value={"server_name": "server1", "command": "cmd1"})
            ),
            "server2": Mock(
                to_dict=Mock(return_value={"server_name": "server2", "command": "cmd2"})
            ),
        }
        mock_config.get_all_servers.return_value = mock_servers

        # Patch the import from the mcp module where it's actually imported from
        with (
            patch(
                "my_coding_agent.core.mcp.load_default_mcp_config",
                return_value=mock_config,
            ),
            patch(
                "my_coding_agent.core.ai_services.mcp_connection_service.MCPClient"
            ) as mock_client,
        ):
            service._auto_discover_mcp_servers()

            # Should create clients for both servers
            assert mock_client.call_count == 2
            assert service.mcp_registry.register_server.call_count == 2
            assert service._mcp_servers_need_connection is True

    def test_auto_discover_fallback_to_simple_method(self):
        """Test fallback to simple mcp.json discovery when enhanced method fails."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock enhanced method failure and successful fallback
        with (
            patch(
                "my_coding_agent.core.mcp.load_default_mcp_config",
                side_effect=Exception("Enhanced discovery failed"),
            ),
            patch.object(
                service, "_auto_discover_mcp_servers_fallback"
            ) as mock_fallback,
        ):
            service._auto_discover_mcp_servers()
            mock_fallback.assert_called_once()

    def test_auto_discover_fallback_method(self):
        """Test fallback auto-discovery using mcp.json."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock mcp.json file
        mock_config = {
            "mcpServers": {
                "test_server": {
                    "command": "test_command",
                    "args": ["arg1", "arg2"],
                    "env": {"VAR": "value"},
                }
            }
        }

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=json.dumps(mock_config))),
            patch(
                "my_coding_agent.core.ai_services.mcp_connection_service.MCPClient"
            ) as mock_client,
        ):
            service._auto_discover_mcp_servers_fallback()

            mock_client.assert_called_once_with(
                server_name="test_server",
                command="test_command",
                args=["arg1", "arg2"],
                env={"VAR": "value"},
            )

    def test_auto_discover_no_config_file(self):
        """Test auto-discovery when no config file exists."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        with patch("pathlib.Path.exists", return_value=False):
            # Should not raise exception
            service._auto_discover_mcp_servers_fallback()


class TestAdvancedConnectionLogic:
    """Test advanced connection logic with tool cache integration."""

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_advanced(self):
        """Test advanced connection logic with tool cache updates."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)
        service.tool_registration_service = Mock()
        service.tool_registration_service.register_all_tools = Mock()

        # Mock successful connections
        mock_connection_results = {"server1": True, "server2": True}
        service.mcp_registry.connect_all_servers = AsyncMock(
            return_value=mock_connection_results
        )
        service.mcp_registry.update_tools_cache = AsyncMock()
        service.mcp_registry.get_all_tools = Mock(
            return_value={"server1": ["tool1"], "server2": ["tool2"]}
        )

        with patch("asyncio.get_running_loop"):
            result = await service.connect_mcp_servers()

            assert result == mock_connection_results
            service.mcp_registry.connect_all_servers.assert_called_once()
            service.mcp_registry.update_tools_cache.assert_called_once()
            assert service._mcp_tools_registered is True

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_no_registry(self):
        """Test connection when no registry is initialized."""
        service = MCPConnectionService()

        result = await service.connect_mcp_servers()

        assert result == {}

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_partial_success(self):
        """Test connection with partial success."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock partial success
        mock_connection_results = {"server1": True, "server2": False}
        service.mcp_registry.connect_all_servers = AsyncMock(
            return_value=mock_connection_results
        )
        service.mcp_registry.update_tools_cache = AsyncMock()
        service.mcp_registry.get_all_tools = Mock(return_value={"server1": ["tool1"]})

        result = await service.connect_mcp_servers()

        assert result == mock_connection_results
        service.mcp_registry.update_tools_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_async_wrapper(self):
        """Test async wrapper method for AIAgent compatibility."""
        service = MCPConnectionService()

        with patch.object(
            service, "connect_mcp_servers", new_callable=AsyncMock
        ) as mock_connect:
            await service.connect_mcp_servers_async()
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_async_error_handling(self):
        """Test error handling in async wrapper."""
        service = MCPConnectionService()

        with patch.object(
            service,
            "connect_mcp_servers",
            new_callable=AsyncMock,
            side_effect=Exception("Connection error"),
        ):
            # Should not raise exception
            await service.connect_mcp_servers_async()


class TestHealthMonitoring:
    """Test comprehensive health monitoring functionality."""

    def test_get_mcp_health_status_no_registry(self):
        """Test health status when no registry is initialized."""
        service = MCPConnectionService()

        status = service.get_mcp_health_status()

        assert status["status"] == "not_configured"
        assert status["total_servers"] == 0
        assert status["connected_servers"] == 0
        assert status["health_score"] == 0.0

    def test_get_mcp_health_status_no_servers(self):
        """Test health status with no servers configured."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)
        service.mcp_registry.get_all_servers.return_value = []

        status = service.get_mcp_health_status()

        assert status["status"] == "no_servers"
        assert status["total_servers"] == 0
        assert status["health_score"] == 0.0

    def test_get_mcp_health_status_all_connected(self):
        """Test health status with all servers connected."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock connected clients
        mock_client1 = Mock()
        mock_client1.server_name = "server1"
        mock_client1.is_connected = True
        mock_client1.list_tools.return_value = ["tool1", "tool2"]

        mock_client2 = Mock()
        mock_client2.server_name = "server2"
        mock_client2.is_connected = True
        mock_client2.list_tools.return_value = ["tool3"]

        service.mcp_registry.get_all_servers.return_value = [mock_client1, mock_client2]

        status = service.get_mcp_health_status()

        assert status["status"] == "healthy"
        assert status["total_servers"] == 2
        assert status["connected_servers"] == 2
        assert status["available_tools"] == 3
        assert status["health_score"] == 1.0
        assert len(status["health_issues"]) == 0

    def test_get_mcp_health_status_partial_connection(self):
        """Test health status with partial server connections."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock mixed connection states
        mock_client1 = Mock()
        mock_client1.server_name = "server1"
        mock_client1.is_connected = True
        mock_client1.list_tools.return_value = ["tool1"]

        mock_client2 = Mock()
        mock_client2.server_name = "server2"
        mock_client2.is_connected = False

        service.mcp_registry.get_all_servers.return_value = [mock_client1, mock_client2]

        status = service.get_mcp_health_status()

        assert status["status"] == "partial"
        assert status["total_servers"] == 2
        assert status["connected_servers"] == 1
        assert status["health_score"] == 0.5
        assert len(status["health_issues"]) == 1
        assert "server2" in status["health_issues"][0]

    def test_get_mcp_health_status_error_handling(self):
        """Test health status error handling."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)
        service.mcp_registry.get_all_servers.side_effect = Exception("Registry error")

        status = service.get_mcp_health_status()

        assert status["status"] == "error"
        assert "Registry error" in status["message"]


class TestConfigurationManagement:
    """Test configuration management functionality."""

    def test_update_mcp_config(self):
        """Test MCP configuration update."""
        service = MCPConnectionService()
        new_config = Mock(spec=MCPFileConfig)

        service.update_mcp_config(new_config)

        assert service.mcp_file_server is new_config

    def test_update_mcp_config_with_signal(self):
        """Test MCP configuration update with signal emission."""
        service = MCPConnectionService()
        signal_handler = Mock()
        signal_handler.mcp_config_updated = Mock()
        service.signal_handler = signal_handler

        new_config = Mock(spec=MCPFileConfig)

        service.update_mcp_config(new_config)

        signal_handler.mcp_config_updated.emit.assert_called_once()

    def test_update_mcp_config_error_handling(self):
        """Test configuration update error handling."""
        service = MCPConnectionService()

        with patch.object(
            service,
            "mcp_file_server",
            new_callable=PropertyMock,
            side_effect=Exception("Config error"),
        ):
            # Should not raise exception
            service.update_mcp_config(Mock())


class TestContextManagement:
    """Test async context management functionality."""

    @pytest.mark.asyncio
    async def test_connect_mcp(self):
        """Test connect_mcp method."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(
            spec=MCPServerRegistry
        )  # Add registry for this test

        with patch.object(
            service,
            "connect_mcp_servers",
            new_callable=AsyncMock,
            return_value={"server1": True},
        ) as mock_connect:
            result = await service.connect_mcp()

            assert result is True
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_no_registry(self):
        """Test connect_mcp with no registry."""
        service = MCPConnectionService()

        result = await service.connect_mcp()

        assert result is False

    @pytest.mark.asyncio
    async def test_connect_mcp_no_connections(self):
        """Test connect_mcp with no successful connections."""
        service = MCPConnectionService()

        with patch.object(
            service,
            "connect_mcp_servers",
            new_callable=AsyncMock,
            return_value={"server1": False},
        ):
            result = await service.connect_mcp()

            assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_mcp(self):
        """Test disconnect_mcp method."""
        service = MCPConnectionService()

        with patch.object(
            service, "disconnect_mcp_servers", new_callable=AsyncMock
        ) as mock_disconnect:
            await service.disconnect_mcp()
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_context_manager(self):
        """Test MCP async context manager."""
        service = MCPConnectionService()

        with patch.object(
            service, "connect_mcp", new_callable=AsyncMock, return_value=True
        ):
            async with service.mcp_context():
                pass  # Context should work without issues

    @pytest.mark.asyncio
    async def test_mcp_context_manager_no_connection(self):
        """Test MCP context manager when connection fails."""
        service = MCPConnectionService()

        with patch.object(
            service, "connect_mcp", new_callable=AsyncMock, return_value=False
        ):
            async with service.mcp_context():
                pass  # Should still work even without connection


class TestConnectionUtilities:
    """Test connection utility methods."""

    def test_ensure_mcp_connected_sync(self):
        """Test synchronous MCP connection check."""
        service = MCPConnectionService()
        service._mcp_servers_need_connection = True

        # Should not raise exception
        service._ensure_mcp_connected()

    def test_ensure_mcp_connected_no_registry(self):
        """Test sync connection check with no registry."""
        service = MCPConnectionService()

        # Should not raise exception
        service._ensure_mcp_connected()

    @pytest.mark.asyncio
    async def test_ensure_mcp_servers_connected_needs_connection(self):
        """Test async connection ensuring when connection is needed."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(
            spec=MCPServerRegistry
        )  # Add registry for this test
        service._mcp_servers_need_connection = True

        with patch.object(
            service,
            "connect_mcp_servers",
            new_callable=AsyncMock,
            return_value={"server1": True},
        ) as mock_connect:
            result = await service._ensure_mcp_servers_connected()

            assert result is True
            assert service._mcp_servers_need_connection is False
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_mcp_servers_connected_check_existing(self):
        """Test async connection ensuring with existing connections."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock connected client
        mock_client = Mock()
        mock_client.is_connected = True
        service.mcp_registry.get_all_servers.return_value = [mock_client]

        result = await service._ensure_mcp_servers_connected()

        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_mcp_servers_connected_reconnect_needed(self):
        """Test async connection ensuring when reconnection is needed."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)

        # Mock disconnected client
        mock_client = Mock()
        mock_client.is_connected = False
        service.mcp_registry.get_all_servers.return_value = [mock_client]

        with patch.object(
            service,
            "connect_mcp_servers",
            new_callable=AsyncMock,
            return_value={"server1": True},
        ) as mock_connect:
            result = await service._ensure_mcp_servers_connected()

            assert result is True
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_on_startup(self):
        """Test startup connection method."""
        service = MCPConnectionService()
        service._mcp_servers_need_connection = True

        with patch.object(
            service, "connect_mcp_servers", new_callable=AsyncMock
        ) as mock_connect:
            await service.connect_mcp_servers_on_startup()

            assert service._mcp_servers_need_connection is False
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_mcp_servers_on_startup_not_needed(self):
        """Test startup connection when not needed."""
        service = MCPConnectionService()
        service._mcp_servers_need_connection = False

        with patch.object(
            service, "connect_mcp_servers", new_callable=AsyncMock
        ) as mock_connect:
            await service.connect_mcp_servers_on_startup()

            mock_connect.assert_not_called()


class TestUtilityMethods:
    """Test utility methods for compatibility and state management."""

    def test_needs_connection(self):
        """Test needs_connection utility method."""
        service = MCPConnectionService()

        assert service.needs_connection() is False

        service._mcp_servers_need_connection = True
        assert service.needs_connection() is True

    def test_is_tools_registered(self):
        """Test is_tools_registered utility method."""
        service = MCPConnectionService()

        assert service.is_tools_registered() is False

        service._mcp_tools_registered = True
        assert service.is_tools_registered() is True

    def test_set_tools_registered(self):
        """Test set_tools_registered utility method."""
        service = MCPConnectionService()

        service.set_tools_registered(True)
        assert service._mcp_tools_registered is True

        service.set_tools_registered(False)
        assert service._mcp_tools_registered is False


class TestServerRegistration:
    """Test server registration and unregistration functionality."""

    def test_register_mcp_server(self):
        """Test MCP server registration."""
        service = MCPConnectionService()
        client = Mock(spec=MCPClient)
        client.server_name = "test_server"

        with patch(
            "my_coding_agent.core.ai_services.mcp_connection_service.MCPServerRegistry"
        ) as mock_registry_class:
            mock_registry = Mock()
            mock_registry_class.return_value = mock_registry

            service.register_mcp_server(client)

            assert service.mcp_registry is mock_registry
            mock_registry.register_server.assert_called_once_with(client)

    def test_register_mcp_server_with_signal(self):
        """Test server registration with signal emission."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)
        signal_handler = Mock()
        signal_handler.mcp_server_registered = Mock()
        service.signal_handler = signal_handler

        client = Mock(spec=MCPClient)
        client.server_name = "test_server"

        service.register_mcp_server(client)

        signal_handler.mcp_server_registered.emit.assert_called_once_with("test_server")

    def test_unregister_mcp_server(self):
        """Test MCP server unregistration."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)
        service.mcp_registry.unregister_server.return_value = True

        result = service.unregister_mcp_server("test_server")

        assert result is True
        service.mcp_registry.unregister_server.assert_called_once_with("test_server")

    def test_unregister_mcp_server_with_signal(self):
        """Test server unregistration with signal emission."""
        service = MCPConnectionService()
        service.mcp_registry = Mock(spec=MCPServerRegistry)
        service.mcp_registry.unregister_server.return_value = True
        signal_handler = Mock()
        signal_handler.mcp_server_unregistered = Mock()
        service.signal_handler = signal_handler

        result = service.unregister_mcp_server("test_server")

        assert result is True
        signal_handler.mcp_server_unregistered.emit.assert_called_once_with(
            "test_server"
        )

    def test_unregister_mcp_server_no_registry(self):
        """Test server unregistration with no registry."""
        service = MCPConnectionService()

        result = service.unregister_mcp_server("test_server")

        assert result is False


# Utility functions for tests
def mock_open_json(data):
    """Create a mock for opening JSON files."""
    from unittest.mock import mock_open

    return mock_open(read_data=json.dumps(data))


# Property mock for configuration testing
class PropertyMock:
    def __init__(self, side_effect=None):
        self.side_effect = side_effect

    def __set__(self, obj, value):
        if self.side_effect:
            raise self.side_effect
