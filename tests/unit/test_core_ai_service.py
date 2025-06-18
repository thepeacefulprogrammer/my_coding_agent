"""Tests for CoreAIService focused AI functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from my_coding_agent.core.ai_services import AIResponse, CoreAIService


class TestCoreAIService:
    """Test cases for CoreAIService."""

    @pytest.fixture
    def mock_config(self):
        """Mock AI configuration."""
        config = MagicMock()
        config.deployment_name = "test-model"
        config.azure_endpoint = "https://test.openai.azure.com/"
        config.azure_api_key = "test-key"
        config.api_version = "2023-12-01-preview"
        config.request_timeout = 30.0
        config.max_retries = 3
        return config

    @pytest.fixture
    def mock_agent_response(self):
        """Mock agent response."""
        response = MagicMock()
        response.data = "Test AI response"
        response.usage = {"total_tokens": 150}
        return response

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    def test_initialization_success(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test successful service initialization."""
        mock_model = MagicMock()
        mock_agent = MagicMock()
        mock_model_class.return_value = mock_model
        mock_agent_class.return_value = mock_agent

        service = CoreAIService(mock_config)

        assert service.config == mock_config
        assert service._model == mock_model
        assert service._agent == mock_agent
        assert service.is_configured is True

        # Verify model creation with correct parameters
        mock_model_class.assert_called_once_with(
            model_name="test-model",
            base_url="https://test.openai.azure.com/openai/deployments/test-model",
            api_key="test-key",
            openai_client_kwargs={
                "api_version": "2023-12-01-preview",
                "timeout": 30.0,
                "max_retries": 3,
            },
        )

        # Verify agent creation
        mock_agent_class.assert_called_once_with(
            model=mock_model,
            system_prompt=mock_agent_class.call_args[1]["system_prompt"],
        )
        # Verify the system prompt contains expected content
        system_prompt = mock_agent_class.call_args[1]["system_prompt"]
        assert "AI coding assistant" in system_prompt

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    def test_initialization_model_failure(self, mock_model_class, mock_config):
        """Test initialization with model creation failure."""
        mock_model_class.side_effect = Exception("Model creation failed")

        with pytest.raises(Exception, match="Model creation failed"):
            CoreAIService(mock_config)

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    def test_initialization_agent_failure(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test initialization with agent creation failure."""
        mock_model_class.return_value = MagicMock()
        mock_agent_class.side_effect = Exception("Agent creation failed")

        with pytest.raises(Exception, match="Agent creation failed"):
            CoreAIService(mock_config)

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_send_message_success(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test successful message sending."""
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.data = "Test AI response"
        mock_response.usage = {"total_tokens": 150}
        mock_agent.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is True
        assert response.content == "Test AI response"
        assert response.tokens_used == 150
        assert response.error is None

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_send_message_empty_input(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test sending empty message."""
        mock_model_class.return_value = MagicMock()
        mock_agent_class.return_value = MagicMock()

        service = CoreAIService(mock_config)

        # Test empty string
        response = await service.send_message("")
        assert response.success is False
        assert response.error == "Message cannot be empty"

        # Test whitespace only
        response = await service.send_message("   ")
        assert response.success is False
        assert response.error == "Message cannot be empty"

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_send_message_authentication_error(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test authentication error handling."""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("401 Unauthorized")
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is False
        assert response.error_type == "AuthenticationError"
        assert response.error == "Authentication failed. Please check your API key."

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_send_message_rate_limit_error(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test rate limit error handling."""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("429 Rate limit exceeded")
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is False
        assert response.error_type == "RateLimitError"
        assert response.error == "Rate limit exceeded. Please try again later."

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_send_message_timeout_error(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test timeout error handling."""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = asyncio.TimeoutError("Request timeout")
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is False
        assert response.error_type == "TimeoutError"
        assert response.error == "Request timed out. Please try again."

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_send_message_connection_error(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test connection error handling."""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Connection failed")
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is False
        assert response.error_type == "ConnectionError"
        assert response.error == "Network connection error."

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_retry_logic_success_after_failure(
        self, mock_agent_class, mock_model_class, mock_config, mock_agent_response
    ):
        """Test retry logic succeeding after initial failure."""
        mock_agent = AsyncMock()
        # First call fails, second succeeds
        mock_agent.run.side_effect = [
            Exception("Temporary failure"),
            mock_agent_response,
        ]
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is True
        assert response.content == "Test AI response"
        assert mock_agent.run.call_count == 2

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_retry_logic_non_retryable_error(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test retry logic not retrying for authentication errors."""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("401 Unauthorized")
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is False
        assert response.error_type == "AuthenticationError"
        # Should not retry for auth errors
        assert mock_agent.run.call_count == 1

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    async def test_retry_logic_max_retries_exceeded(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test retry logic when max retries exceeded."""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Temporary failure")
        mock_agent_class.return_value = mock_agent
        mock_model_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        response = await service.send_message("Test message")

        assert response.success is False
        # Should try max_retries + 1 times (3 + 1 = 4)
        assert mock_agent.run.call_count == 4

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    def test_model_info_configured(
        self, mock_agent_class, mock_model_class, mock_config
    ):
        """Test model info when configured."""
        mock_model_class.return_value = MagicMock()
        mock_agent_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        assert service.model_info == "Azure OpenAI - test-model"

    @patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel")
    @patch("my_coding_agent.core.ai_services.core_ai_service.Agent")
    def test_get_health_status(self, mock_agent_class, mock_model_class, mock_config):
        """Test health status retrieval."""
        mock_model_class.return_value = MagicMock()
        mock_agent_class.return_value = MagicMock()

        service = CoreAIService(mock_config)
        health = service.get_health_status()

        expected = {
            "service": "CoreAIService",
            "configured": True,
            "model": "Azure OpenAI - test-model",
            "endpoint": "https://test.openai.azure.com/",
            "deployment": "test-model",
            "api_version": "2023-12-01-preview",
        }
        assert health == expected

    def test_categorize_error_types(self):
        """Test error categorization logic."""
        config = MagicMock()
        config.max_retries = 3

        with (
            patch("my_coding_agent.core.ai_services.core_ai_service.OpenAIModel"),
            patch("my_coding_agent.core.ai_services.core_ai_service.Agent"),
        ):
            service = CoreAIService(config)

        # Test authentication error
        auth_error = Exception("401 Unauthorized access")
        error_type, message = service._categorize_error(auth_error)
        assert error_type == "AuthenticationError"
        assert message == "Authentication failed. Please check your API key."

        # Test rate limit error
        rate_error = Exception("429 Too Many Requests")
        error_type, message = service._categorize_error(rate_error)
        assert error_type == "RateLimitError"
        assert message == "Rate limit exceeded. Please try again later."


class TestAIResponse:
    """Test cases for AIResponse model."""

    def test_ai_response_success(self):
        """Test successful AIResponse creation."""
        response = AIResponse(content="Test response", success=True, tokens_used=100)

        assert response.content == "Test response"
        assert response.success is True
        assert response.error is None
        assert response.tokens_used == 100

    def test_ai_response_error(self):
        """Test error AIResponse creation."""
        response = AIResponse(
            content="",
            success=False,
            error="Something went wrong",
            error_type="TestError",
        )

        assert response.content == ""
        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.error_type == "TestError"

    def test_ai_response_defaults(self):
        """Test AIResponse with minimal required fields."""
        response = AIResponse(content="Test", success=True)

        assert response.content == "Test"
        assert response.success is True
        assert response.error is None
        assert response.error_type is None
        assert response.tokens_used == 0
        assert response.retry_count == 0
