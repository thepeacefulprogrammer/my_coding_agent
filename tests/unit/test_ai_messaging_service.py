"""Tests for the AI Messaging Service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.my_coding_agent.core.ai_services.ai_messaging_service import AIMessagingService


class TestAIMessagingService:
    """Test cases for AIMessagingService."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = MagicMock()
        config.deployment_name = "test-deployment"
        config.azure_endpoint = "https://test.openai.azure.com/"
        config.azure_api_key = "test-key"
        config.api_version = "2024-02-15-preview"
        config.request_timeout = 30
        config.max_retries = 3
        return config

    @pytest.fixture
    def mock_mcp_service(self):
        """Mock MCP connection service."""
        mock_service = MagicMock()
        mock_service.is_connected.return_value = True
        mock_service.connect = AsyncMock()
        mock_service.list_directory = AsyncMock(return_value=["file1.py", "file2.py"])
        mock_service.write_file = AsyncMock(return_value=True)
        return mock_service

    @pytest.fixture
    def mock_workspace_service(self):
        """Mock workspace service."""
        mock_service = MagicMock()
        mock_service.is_configured.return_value = True
        mock_service.read_workspace_file.return_value = "test file content"
        return mock_service

    @pytest.fixture
    def messaging_service(self, mock_config, mock_mcp_service, mock_workspace_service):
        """Create AIMessagingService instance for testing."""
        with (
            patch("src.my_coding_agent.core.ai_services.core_ai_service.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_services.core_ai_service.Agent"),
        ):
            service = AIMessagingService(
                config=mock_config,
                mcp_connection_service=mock_mcp_service,
                workspace_service=mock_workspace_service,
            )
            return service

    def test_initialization_success(
        self, mock_config, mock_mcp_service, mock_workspace_service
    ):
        """Test successful initialization of AIMessagingService."""
        with (
            patch("src.my_coding_agent.core.ai_services.core_ai_service.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_services.core_ai_service.Agent"),
        ):
            service = AIMessagingService(
                config=mock_config,
                mcp_connection_service=mock_mcp_service,
                workspace_service=mock_workspace_service,
            )

            assert service._mcp_connection_service == mock_mcp_service
            assert service._workspace_service == mock_workspace_service
            assert service.is_configured

    def test_initialization_without_optional_services(self, mock_config):
        """Test initialization without optional services."""
        with (
            patch("src.my_coding_agent.core.ai_services.core_ai_service.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_services.core_ai_service.Agent"),
        ):
            service = AIMessagingService(config=mock_config)

            assert service._mcp_connection_service is None
            assert service._workspace_service is None
            assert service.is_configured

    @pytest.mark.asyncio
    async def test_send_message_with_tools_success(self, messaging_service):
        """Test successful send_message_with_tools."""
        # Mock the agent response
        mock_response = MagicMock()
        mock_response.data = "AI response content"
        messaging_service._agent.run = AsyncMock(return_value=mock_response)

        result = await messaging_service.send_message_with_tools("test message")

        assert result.success
        assert result.content == "AI response content"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_send_message_with_tools_mcp_connection(self, messaging_service):
        """Test send_message_with_tools with MCP connection."""
        # Setup MCP service to be disconnected initially
        messaging_service._mcp_connection_service.is_connected.return_value = False

        mock_response = MagicMock()
        mock_response.data = "AI response with tools"
        messaging_service._agent.run = AsyncMock(return_value=mock_response)

        result = await messaging_service.send_message_with_tools(
            "test message", enable_filesystem=True
        )

        # Verify MCP connection was attempted
        messaging_service._mcp_connection_service.connect.assert_called_once()
        assert result.success
        assert result.content == "AI response with tools"

    @pytest.mark.asyncio
    async def test_send_message_with_tools_error(self, messaging_service):
        """Test send_message_with_tools with error."""
        messaging_service._agent.run = AsyncMock(side_effect=Exception("Test error"))

        result = await messaging_service.send_message_with_tools("test message")

        assert not result.success
        assert result.error_type == "unknown"
        assert "An unexpected error occurred" in result.error

    @pytest.mark.asyncio
    async def test_analyze_project_files_success(self, messaging_service):
        """Test successful project analysis."""
        mock_response = MagicMock()
        mock_response.data = "Project analysis results"
        messaging_service._agent.run = AsyncMock(return_value=mock_response)

        result = await messaging_service.analyze_project_files()

        assert result.success
        assert result.content == "Project analysis results"
        messaging_service._mcp_connection_service.list_directory.assert_called_once_with(
            "."
        )

    @pytest.mark.asyncio
    async def test_analyze_project_files_no_mcp_service(self, mock_config):
        """Test project analysis without MCP service."""
        with (
            patch("src.my_coding_agent.core.ai_services.core_ai_service.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_services.core_ai_service.Agent"),
        ):
            service = AIMessagingService(config=mock_config)

            result = await service.analyze_project_files()

            assert not result.success
            assert "Filesystem tools not available" in result.content

    @pytest.mark.asyncio
    async def test_generate_and_save_code_success(self, messaging_service):
        """Test successful code generation and saving."""
        result = await messaging_service.generate_and_save_code(
            "Generate a function", "test.py", "def test(): pass"
        )

        assert result.success
        assert "Code generated and saved to test.py" in result.content
        messaging_service._mcp_connection_service.write_file.assert_called_once_with(
            "test.py", "def test(): pass"
        )

    @pytest.mark.asyncio
    async def test_generate_and_save_code_failure(self, messaging_service):
        """Test code generation with save failure."""
        messaging_service._mcp_connection_service.write_file.return_value = False

        result = await messaging_service.generate_and_save_code(
            "Generate a function", "test.py", "def test(): pass"
        )

        assert not result.success
        assert "Failed to save code to test.py" in result.content

    @pytest.mark.asyncio
    async def test_send_message_with_file_context_success(self, messaging_service):
        """Test successful message with file context."""
        mock_response = MagicMock()
        mock_response.data = "Response with file context"
        messaging_service._agent.run = AsyncMock(return_value=mock_response)

        result = await messaging_service.send_message_with_file_context(
            "test message", "test.py"
        )

        assert result.success
        assert result.content == "Response with file context"
        messaging_service._workspace_service.read_workspace_file.assert_called_once_with(
            "test.py"
        )

    @pytest.mark.asyncio
    async def test_send_message_with_file_context_no_workspace_service(
        self, mock_config, mock_mcp_service
    ):
        """Test message with file context without workspace service."""
        with (
            patch("src.my_coding_agent.core.ai_services.core_ai_service.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_services.core_ai_service.Agent"),
        ):
            service = AIMessagingService(
                config=mock_config, mcp_connection_service=mock_mcp_service
            )

            result = await service.send_message_with_file_context(
                "test message", "test.py"
            )

            assert not result.success
            assert result.error_type == "service_unavailable"
            assert "Workspace service not available" in result.content

    @pytest.mark.asyncio
    async def test_send_enhanced_message_with_file_detection(self, messaging_service):
        """Test enhanced message with file detection."""
        mock_response = MagicMock()
        mock_response.data = "Response with detected file"
        messaging_service._agent.run = AsyncMock(return_value=mock_response)

        result = await messaging_service.send_enhanced_message("read test.py file")

        assert result.success
        messaging_service._workspace_service.read_workspace_file.assert_called_once_with(
            "test.py"
        )

    @pytest.mark.asyncio
    async def test_send_enhanced_message_fallback(self, messaging_service):
        """Test enhanced message fallback to regular message."""
        mock_response = MagicMock()
        mock_response.data = "Regular response"
        messaging_service._agent.run = AsyncMock(return_value=mock_response)

        result = await messaging_service.send_enhanced_message("regular message")

        assert result.success
        assert result.content == "Regular response"

    @pytest.mark.asyncio
    async def test_send_enhanced_message_file_read_failure(self, messaging_service):
        """Test enhanced message with file read failure fallback."""
        messaging_service._workspace_service.read_workspace_file.side_effect = (
            Exception("File not found")
        )

        mock_response = MagicMock()
        mock_response.data = "Fallback response"
        messaging_service._agent.run = AsyncMock(return_value=mock_response)

        result = await messaging_service.send_enhanced_message("read test.py file")

        assert result.success
        assert result.content == "Fallback response"

    def test_categorize_error_file_not_found(self, messaging_service):
        """Test error categorization for FileNotFoundError."""
        error_type, error_msg = messaging_service._categorize_error(
            FileNotFoundError("File not found")
        )

        assert error_type == "file_not_found"
        assert error_msg == "Requested file was not found."

    def test_categorize_error_permission_error(self, messaging_service):
        """Test error categorization for PermissionError."""
        error_type, error_msg = messaging_service._categorize_error(
            PermissionError("Permission denied")
        )

        assert error_type == "permission_error"
        assert "Permission denied" in error_msg

    def test_categorize_error_connection_error(self, messaging_service):
        """Test error categorization for ConnectionError."""
        error_type, error_msg = messaging_service._categorize_error(
            ConnectionError("Connection failed")
        )

        assert error_type == "connection_error"
        assert "Network connection failed" in error_msg

    def test_categorize_error_timeout_error(self, messaging_service):
        """Test error categorization for TimeoutError."""
        import asyncio

        error_type, error_msg = messaging_service._categorize_error(
            asyncio.TimeoutError("Timeout")
        )

        assert error_type == "timeout_error"
        assert "Request timed out" in error_msg

    def test_categorize_error_token_limit(self, messaging_service):
        """Test error categorization for token limit error."""
        error = Exception("Token limit exceeded")
        error_type, error_msg = messaging_service._categorize_error(error)

        assert error_type == "token_limit_error"
        assert "Token limit exceeded" in error_msg

    def test_categorize_error_streaming_interrupted(self, messaging_service):
        """Test error categorization for streaming interruption."""
        error = Exception("Stream was interrupted")
        error_type, error_msg = messaging_service._categorize_error(error)

        assert error_type == "stream_interrupted"
        assert "Stream was interrupted" in error_msg

    def test_categorize_error_validation_error(self, messaging_service):
        """Test error categorization for validation errors."""
        error_type, error_msg = messaging_service._categorize_error(
            ValueError("Invalid value")
        )

        assert error_type == "validation_error"
        assert "Invalid input provided" in error_msg

    def test_categorize_error_unknown(self, messaging_service):
        """Test error categorization for unknown errors."""
        error = RuntimeError("Unknown error")
        error_type, error_msg = messaging_service._categorize_error(error)

        assert error_type == "unknown"
        assert "An unexpected error occurred" in error_msg

    def test_get_health_status_full_services(self, messaging_service):
        """Test health status with all services available."""
        status = messaging_service.get_health_status()

        assert status["service"] == "AIMessagingService"
        assert status["mcp_connection_available"] is True
        assert status["workspace_service_available"] is True
        assert status["mcp_connected"] is True
        assert status["workspace_configured"] is True

    def test_get_health_status_no_services(self, mock_config):
        """Test health status without optional services."""
        with (
            patch("src.my_coding_agent.core.ai_services.core_ai_service.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_services.core_ai_service.Agent"),
        ):
            service = AIMessagingService(config=mock_config)

            status = service.get_health_status()

            assert status["service"] == "AIMessagingService"
            assert status["mcp_connection_available"] is False
            assert status["workspace_service_available"] is False
