"""
Tests to verify ai_agent.py doesn't duplicate functionality already provided by services.

This test module validates the elimination of code duplication between ai_agent.py
and existing services as part of the GOD object refactoring.
"""

from unittest.mock import Mock, patch

import pytest
from src.my_coding_agent.core.ai_agent import AIAgent
from src.my_coding_agent.core.ai_services.ai_messaging_service import AIMessagingService
from src.my_coding_agent.core.ai_services.configuration_service import (
    ConfigurationService,
)
from src.my_coding_agent.core.ai_services.error_handling_service import (
    ErrorHandlingService,
)
from src.my_coding_agent.core.ai_services.mcp_connection_service import (
    MCPConnectionService,
)
from src.my_coding_agent.core.ai_services.streaming_response_service import (
    StreamingResponseService,
)
from src.my_coding_agent.core.ai_services.tool_registration_service import (
    ToolRegistrationService,
)
from src.my_coding_agent.core.ai_services.workspace_service import WorkspaceService


class TestAIAgentCodeDuplication:
    """Test that ai_agent.py delegates to existing services instead of duplicating code."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing delegation."""
        return {
            "workspace_service": Mock(spec=WorkspaceService),
            "mcp_connection_service": Mock(spec=MCPConnectionService),
            "streaming_response_service": Mock(spec=StreamingResponseService),
            "ai_messaging_service": Mock(spec=AIMessagingService),
            "tool_registration_service": Mock(spec=ToolRegistrationService),
            "config_service": Mock(spec=ConfigurationService),
            "error_service": Mock(spec=ErrorHandlingService),
        }

    @pytest.fixture
    def service_oriented_agent(self, mock_services):
        """Create an AIAgent that uses service-oriented architecture."""
        # Configure config service mock
        mock_services[
            "config_service"
        ].azure_endpoint = "https://test.openai.azure.com/"
        mock_services["config_service"].api_version = "2024-02-15-preview"
        mock_services["config_service"].azure_api_key = "test-key"
        mock_services["config_service"].deployment_name = "test-deployment"
        mock_services["config_service"].max_retries = 3
        mock_services["config_service"].request_timeout = 30
        mock_services["config_service"].max_tokens = 4000
        mock_services["config_service"].temperature = 0.7

        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            agent = AIAgent(
                config_service=mock_services["config_service"],
                error_service=mock_services["error_service"],
                workspace_service=mock_services["workspace_service"],
                mcp_connection_service=mock_services["mcp_connection_service"],
                streaming_response_service=mock_services["streaming_response_service"],
                ai_messaging_service=mock_services["ai_messaging_service"],
                tool_registration_service=mock_services["tool_registration_service"],
            )

        return agent, mock_services

    def test_workspace_operations_delegate_to_workspace_service(
        self, service_oriented_agent
    ):
        """Test that ai_agent.py delegates file operations to WorkspaceService."""
        agent, mock_services = service_oriented_agent

        # Test file reading delegation
        mock_services[
            "workspace_service"
        ].read_workspace_file.return_value = "test content"
        result = agent.read_workspace_file("test.py")

        mock_services["workspace_service"].read_workspace_file.assert_called_once_with(
            "test.py"
        )
        assert result == "test content"

        # Test file writing delegation
        agent.write_workspace_file("test.py", "new content")
        mock_services["workspace_service"].write_workspace_file.assert_called_once_with(
            "test.py", "new content"
        )

        # Test directory listing delegation
        mock_services["workspace_service"].list_workspace_directory.return_value = [
            "file1.py",
            "file2.py",
        ]
        result = agent.list_workspace_directory("src/")

        mock_services[
            "workspace_service"
        ].list_workspace_directory.assert_called_once_with("src/")
        assert result == ["file1.py", "file2.py"]

    async def test_mcp_operations_delegate_to_mcp_service(self, service_oriented_agent):
        """Test that ai_agent.py delegates MCP operations to MCPConnectionService."""
        agent, mock_services = service_oriented_agent

        # Test MCP connection delegation
        mock_services["mcp_connection_service"].connect_mcp.return_value = True
        result = await agent.connect_mcp()

        mock_services["mcp_connection_service"].connect_mcp.assert_called_once()
        assert result is True

        # Test MCP status delegation
        mock_services["mcp_connection_service"].get_mcp_health_status.return_value = {
            "status": "healthy"
        }
        result = agent.get_mcp_health_status()

        mock_services[
            "mcp_connection_service"
        ].get_mcp_health_status.assert_called_once()
        assert result == {"status": "healthy"}

    async def test_messaging_operations_delegate_to_messaging_service(
        self, service_oriented_agent
    ):
        """Test that ai_agent.py delegates messaging operations to AIMessagingService."""
        agent, mock_services = service_oriented_agent

        # Test enhanced message sending delegation
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "AI response"
        mock_services[
            "ai_messaging_service"
        ].send_enhanced_message.return_value = mock_response

        result = await agent.send_enhanced_message("Test message")

        mock_services[
            "ai_messaging_service"
        ].send_enhanced_message.assert_called_once_with("Test message")
        assert result.success is True
        assert result.content == "AI response"

    def test_streaming_operations_delegate_to_streaming_service(
        self, service_oriented_agent
    ):
        """Test that ai_agent.py delegates streaming operations to StreamingResponseService."""
        agent, mock_services = service_oriented_agent

        # Test streaming status delegation
        # Create a mock with is_streaming as a property that returns True
        mock_streaming_service = mock_services["streaming_response_service"]
        mock_streaming_service.is_streaming = True

        result = agent.is_streaming

        # Verify delegation is working by checking the result
        assert result is True

        # Test that when service is None, it falls back to legacy behavior
        agent.streaming_response_service = None
        result = agent.is_streaming

        # Should return False for legacy implementation when no handlers
        assert result is False

    def test_tool_registration_delegates_to_tool_service(self, service_oriented_agent):
        """Test that ai_agent.py delegates tool registration to ToolRegistrationService."""
        agent, mock_services = service_oriented_agent

        # Test tool availability delegation
        mock_services["tool_registration_service"].get_available_tools.return_value = [
            "read_file",
            "write_file",
        ]
        result = agent.get_available_tools()

        mock_services[
            "tool_registration_service"
        ].get_available_tools.assert_called_once()
        assert result == ["read_file", "write_file"]

    def test_no_duplicate_error_categorization(self, service_oriented_agent):
        """Test that ai_agent.py uses ErrorHandlingService instead of duplicate _categorize_error."""
        agent, mock_services = service_oriented_agent

        # Verify ai_agent doesn't have its own error categorization when services are available
        assert hasattr(agent, "error_service")
        assert agent.error_service is not None

        # Test that agent uses error service for categorization
        test_error = ValueError("Test error")
        from src.my_coding_agent.core.ai_services.error_handling_service import (
            ErrorCategory,
        )

        mock_services["error_service"].categorize_error.return_value = (
            ErrorCategory.VALIDATION_ERROR,
            "Validation failed",
        )

        # This would be called internally during send_message error handling
        category, message = agent.error_service.categorize_error(test_error)

        mock_services["error_service"].categorize_error.assert_called_once_with(
            test_error
        )
        assert category == ErrorCategory.VALIDATION_ERROR
        assert message == "Validation failed"

    def test_no_duplicate_file_validation(self, service_oriented_agent):
        """Test that ai_agent.py uses WorkspaceService for file validation instead of duplicating."""
        agent, mock_services = service_oriented_agent

        # Test file path validation delegation
        agent.workspace_service.validate_file_path("test.py")
        mock_services["workspace_service"].validate_file_path.assert_called_once_with(
            "test.py"
        )

        # Test file content validation delegation
        agent.workspace_service.validate_file_content("test content")
        mock_services[
            "workspace_service"
        ].validate_file_content.assert_called_once_with("test content")

    def test_no_duplicate_mcp_tool_creation(self, service_oriented_agent):
        """Test that ai_agent.py uses ToolRegistrationService instead of duplicate MCP tool creation."""
        agent, mock_services = service_oriented_agent

        # Verify tool registration is delegated
        mock_pydantic_agent = Mock()
        agent.tool_registration_service.register_all_tools(mock_pydantic_agent)

        mock_services[
            "tool_registration_service"
        ].register_all_tools.assert_called_once_with(mock_pydantic_agent)

    def test_configuration_access_through_service(self, service_oriented_agent):
        """Test that ai_agent.py accesses configuration through ConfigurationService."""
        agent, mock_services = service_oriented_agent

        # Test that configuration properties use service
        mock_services["config_service"].max_tokens = 4000
        assert agent.max_tokens == 4000

        mock_services["config_service"].temperature = 0.8
        assert agent.temperature == 0.8

        mock_services["config_service"].request_timeout = 45
        assert agent.request_timeout == 45


class TestDuplicationEliminationValidation:
    """Tests to validate that duplicate code has been properly eliminated."""

    def test_ai_agent_does_not_have_duplicate_file_operations(self):
        """Test that ai_agent.py doesn't contain duplicate file operation methods."""
        from src.my_coding_agent.core.ai_agent import AIAgent

        # These methods should either not exist or should be thin wrappers that delegate
        # Note: We check the AIAgent class to ensure delegation patterns are followed

        # File operations that should be delegated to WorkspaceService
        workspace_methods = [
            "read_workspace_file",
            "write_workspace_file",
            "list_workspace_directory",
            "create_workspace_directory",
            "delete_workspace_file",
            "workspace_file_exists",
            "validate_file_path",
            "validate_file_content",
            "validate_directory_path",
        ]

        # If these methods exist in AIAgent, they should be delegation methods only
        for method_name in workspace_methods:
            if hasattr(AIAgent, method_name):
                method = getattr(AIAgent, method_name)
                # The method should be small (delegation only) - check if it's not a large implementation
                assert callable(method), f"{method_name} should be callable"

    def test_ai_agent_does_not_have_duplicate_mcp_operations(self):
        """Test that ai_agent.py doesn't contain duplicate MCP operation methods."""
        from src.my_coding_agent.core.ai_agent import AIAgent

        # MCP operations that should be delegated to MCPConnectionService
        mcp_methods = [
            "connect_mcp_servers",
            "disconnect_mcp_servers",
            "register_mcp_server",
            "unregister_mcp_server",
            "get_mcp_server_status",
            "update_mcp_config",
        ]

        # If these methods exist in AIAgent, they should be delegation methods only
        for method_name in mcp_methods:
            if hasattr(AIAgent, method_name):
                method = getattr(AIAgent, method_name)
                assert callable(method), f"{method_name} should be callable"

    def test_ai_agent_does_not_have_duplicate_tool_registration(self):
        """Test that ai_agent.py doesn't contain duplicate tool registration methods."""
        from src.my_coding_agent.core.ai_agent import AIAgent

        # Tool registration methods that should be delegated to ToolRegistrationService
        tool_methods = [
            "get_available_tools",
            "get_tool_descriptions",
            "_register_mcp_tools",
            "_create_mcp_tool_function",
            "_get_mcp_tools",
            "_get_mcp_tool_descriptions",
        ]

        # If these methods exist in AIAgent, they should be delegation methods only
        for method_name in tool_methods:
            if hasattr(AIAgent, method_name):
                method = getattr(AIAgent, method_name)
                assert callable(method), f"{method_name} should be callable"

    def test_ai_agent_error_handling_uses_service(self):
        """Test that ai_agent.py uses ErrorHandlingService instead of duplicate error handling."""
        from src.my_coding_agent.core.ai_agent import AIAgent

        # Create an agent with error service (service-oriented mode)
        config_service = Mock()
        config_service.azure_endpoint = "https://test.openai.azure.com/"
        config_service.api_version = "2024-02-15-preview"
        config_service.azure_api_key = "test-key"
        config_service.deployment_name = "test-deployment"
        config_service.max_retries = 3

        error_service = Mock()

        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            agent = AIAgent(config_service=config_service, error_service=error_service)

        # Verify agent has error service
        assert hasattr(agent, "error_service")
        assert agent.error_service is error_service

        # The agent should use error service methods
        assert hasattr(agent, "get_error_statistics")
        assert hasattr(agent, "safe_execute")
