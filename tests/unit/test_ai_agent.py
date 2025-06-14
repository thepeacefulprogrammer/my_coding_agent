"""Unit tests for AI Agent functionality."""

from __future__ import annotations

import asyncio
import logging
import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic_ai.models.openai import OpenAIModel

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig, AIResponse


class TestAIAgentConfig:
    """Test the AI Agent configuration class."""

    def test_config_from_env_vars(self):
        """Test creating config from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ENDPOINT": "https://test.openai.azure.com/",
                "API_KEY": "test-key",
                "MODEL": "test-deployment",
                "API_VERSION": "2024-02-15-preview",
                "AI_MAX_TOKENS": "1000",
                "AI_TEMPERATURE": "0.5",
                "AI_REQUEST_TIMEOUT": "20",
            },
        ):
            config = AIAgentConfig.from_env()

            assert config.azure_endpoint == "https://test.openai.azure.com/"
            assert config.azure_api_key == "test-key"
            assert config.deployment_name == "test-deployment"
            assert config.api_version == "2024-02-15-preview"
            assert config.max_tokens == 1000
            assert config.temperature == 0.5
            assert config.request_timeout == 20

    def test_config_with_defaults(self):
        """Test config with default values when env vars are missing."""
        with patch.dict(
            os.environ,
            {
                "ENDPOINT": "https://test.openai.azure.com/",
                "API_KEY": "test-key",
                "MODEL": "test-deployment",
            },
            clear=True,
        ):
            config = AIAgentConfig.from_env()

            assert config.api_version == "2024-02-15-preview"
            assert config.max_tokens == 2000
            assert config.temperature == 0.7
            assert config.request_timeout == 30

    def test_config_missing_required_env(self):
        """Test that missing required environment variables raise appropriate errors."""
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="ENDPOINT"),
        ):
            AIAgentConfig.from_env()


class TestAIResponse:
    """Test the AI response model."""

    def test_ai_response_creation(self):
        """Test creating an AI response."""
        response = AIResponse(
            content="Test response", success=True, error=None, tokens_used=100
        )

        assert response.content == "Test response"
        assert response.success is True
        assert response.error is None
        assert response.tokens_used == 100

    def test_ai_response_with_error(self):
        """Test creating an AI response with error."""
        response = AIResponse(
            content="", success=False, error="API Error occurred", tokens_used=0
        )

        assert response.content == ""
        assert response.success is False
        assert response.error == "API Error occurred"
        assert response.tokens_used == 0


class TestAIAgent:
    """Test the AI Agent service class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test-key",
            deployment_name="test-deployment",
            api_version="2024-02-15-preview",
            max_tokens=1000,
            temperature=0.7,
            request_timeout=30,
        )

    @pytest.fixture
    def ai_agent(self, mock_config):
        """Create an AI Agent instance for testing."""
        return AIAgent(mock_config)

    def test_ai_agent_initialization(self, mock_config):
        """Test AI Agent initialization."""
        agent = AIAgent(mock_config)

        assert agent.config == mock_config
        assert agent._model is not None
        assert agent._agent is not None

    def test_model_configuration(self, ai_agent):
        """Test that the OpenAI model is configured correctly."""
        model = ai_agent._model

        assert isinstance(model, OpenAIModel)
        assert model is not None

    @pytest.mark.asyncio
    async def test_send_message_with_empty_message(self, ai_agent):
        """Test sending an empty message."""
        response = await ai_agent.send_message("")

        assert response.success is False
        assert response.content == ""
        assert response.error == "Message cannot be empty"
        assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_with_whitespace_only(self, ai_agent):
        """Test sending a message with only whitespace."""
        response = await ai_agent.send_message("   \n\t   ")

        assert response.success is False
        assert response.content == ""
        assert response.error == "Message cannot be empty"
        assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_api_error(self, ai_agent):
        """Test handling API errors during message sending."""
        with patch.object(
            ai_agent._agent,
            "run",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert "API Error" in response.error
            assert response.tokens_used == 0

    def test_system_prompt_configuration(self, ai_agent):
        """Test that the system prompt is properly configured."""
        assert ai_agent._agent is not None

    def test_agent_properties(self, ai_agent):
        """Test agent properties and getters."""
        assert ai_agent.is_configured is True
        assert ai_agent.model_info is not None
        assert "openai" in ai_agent.model_info.lower()

    # New enhanced error handling tests
    @pytest.mark.asyncio
    async def test_send_message_timeout_error(self, ai_agent):
        """Test handling timeout errors."""
        with patch.object(
            ai_agent._agent,
            "run",
            new_callable=AsyncMock,
            side_effect=asyncio.TimeoutError(),
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert (
                "Request timed out. The service may be experiencing high load. Please try again."
                in response.error
            )
            assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_http_error(self, ai_agent):
        """Test handling HTTP errors from Azure OpenAI."""
        import httpx

        http_error = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=httpx.Request("POST", "https://test.com"),
            response=httpx.Response(401),
        )

        with patch.object(
            ai_agent._agent, "run", new_callable=AsyncMock, side_effect=http_error
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert "Authentication failed" in response.error
            assert response.error_type == "authentication_error"
            assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_connection_error(self, ai_agent):
        """Test handling connection errors."""
        import httpx

        connection_error = httpx.ConnectError("Connection failed")

        with patch.object(
            ai_agent._agent, "run", new_callable=AsyncMock, side_effect=connection_error
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert "Connection failed" in response.error
            assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_authentication_error(self, ai_agent):
        """Test handling authentication errors."""
        auth_error = Exception("Authentication failed - invalid API key")

        with patch.object(
            ai_agent._agent, "run", new_callable=AsyncMock, side_effect=auth_error
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert "Authentication failed" in response.error
            assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_rate_limit_error(self, ai_agent):
        """Test handling rate limit errors."""
        rate_limit_error = Exception("Rate limit exceeded")

        with patch.object(
            ai_agent._agent, "run", new_callable=AsyncMock, side_effect=rate_limit_error
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert "Rate limit exceeded" in response.error
            assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_model_retry_exceeded(self, ai_agent):
        """Test handling model retry exceeded errors."""
        from pydantic_ai.exceptions import UnexpectedModelBehavior

        retry_error = UnexpectedModelBehavior("Tool exceeded max retries")

        with patch.object(
            ai_agent._agent, "run", new_callable=AsyncMock, side_effect=retry_error
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert "Tool exceeded max retries" in response.error
            assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_send_message_usage_limit_exceeded(self, ai_agent):
        """Test handling usage limit exceeded errors."""
        from pydantic_ai.exceptions import UsageLimitExceeded

        usage_error = UsageLimitExceeded("Exceeded the request_limit of 3")

        with patch.object(
            ai_agent._agent, "run", new_callable=AsyncMock, side_effect=usage_error
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert response.content == ""
            assert "Exceeded the request_limit" in response.error
            assert response.tokens_used == 0

    @pytest.mark.asyncio
    async def test_logging_on_successful_message(self, ai_agent, caplog):
        """Test that successful messages are properly logged."""
        from unittest.mock import Mock

        # Create proper mock objects
        mock_usage = Mock()
        mock_usage.total_tokens = 150

        mock_result = Mock()
        mock_result.data = "Test response"
        mock_result.usage.return_value = mock_usage

        with (
            patch.object(
                ai_agent._agent, "run", new_callable=AsyncMock, return_value=mock_result
            ),
            caplog.at_level(logging.INFO),
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is True
            assert "Hello, AI!" in caplog.text

    @pytest.mark.asyncio
    async def test_logging_on_error(self, ai_agent, caplog):
        """Test that errors are properly logged."""

        with (
            patch.object(
                ai_agent._agent,
                "run",
                new_callable=AsyncMock,
                side_effect=Exception("Test error"),
            ),
            caplog.at_level(logging.ERROR),
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert "Test error" in caplog.text

    def test_model_creation_error_handling(self, mock_config):
        """Test error handling during model creation."""
        with (
            patch(
                "my_coding_agent.core.ai_agent.OpenAIModel",
                side_effect=Exception("Model creation failed"),
            ),
            pytest.raises(Exception, match="Model creation failed"),
        ):
            AIAgent(mock_config)

    def test_agent_creation_error_handling(self, mock_config):
        """Test error handling during agent creation."""
        with (
            patch(
                "my_coding_agent.core.ai_agent.Agent",
                side_effect=Exception("Agent creation failed"),
            ),
            pytest.raises(Exception, match="Agent creation failed"),
        ):
            AIAgent(mock_config)

    def test_get_health_status(self, ai_agent):
        """Test health status reporting."""
        status = ai_agent.get_health_status()

        assert "configured" in status
        assert "model_name" in status
        assert "endpoint" in status
        assert "max_retries" in status
        assert "timeout" in status
        assert status["configured"] is True
        assert status["model_name"] == "test-deployment"

    @pytest.mark.asyncio
    async def test_retry_mechanism_with_retryable_error(self, ai_agent):
        """Test retry mechanism with retryable errors."""
        import httpx

        server_error = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=httpx.Request("POST", "https://test.com"),
            response=httpx.Response(500),
        )

        with (
            patch.object(
                ai_agent._agent, "run", new_callable=AsyncMock, side_effect=server_error
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert "Server error occurred. Please try again later." in response.error
            assert mock_sleep.call_count >= 1  # Should have retried

    @pytest.mark.asyncio
    async def test_no_retry_for_non_retryable_error(self, ai_agent):
        """Test that non-retryable errors don't trigger retries."""
        auth_error = Exception("Authentication failed - invalid API key")

        with (
            patch.object(
                ai_agent._agent, "run", new_callable=AsyncMock, side_effect=auth_error
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is False
            assert "Authentication failed" in response.error
            assert mock_sleep.call_count == 0  # Should not have retried

    @pytest.mark.asyncio
    async def test_successful_retry_after_transient_error(self, ai_agent):
        """Test successful retry after transient error."""
        import httpx

        mock_result = Mock()
        mock_result.data = "Hello! How can I help you today?"
        mock_usage = Mock()
        mock_usage.total_tokens = 50
        mock_result.usage.return_value = mock_usage

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Use a retryable server error instead of generic Exception
                raise httpx.HTTPStatusError(
                    "503 Service Unavailable",
                    request=httpx.Request("POST", "https://test.com"),
                    response=httpx.Response(503),
                )
            return mock_result

        with (
            patch.object(
                ai_agent._agent, "run", new_callable=AsyncMock, side_effect=side_effect
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert response.success is True
            assert "Hello!" in response.content
            assert call_count == 2  # First call failed, second succeeded

    @pytest.mark.asyncio
    async def test_error_categorization(self, ai_agent):
        """Test that different error types are categorized correctly."""
        import httpx

        test_cases = [
            # HTTP 429 error - properly detected as rate_limit_error
            (
                httpx.HTTPStatusError(
                    "429 Too Many Requests",
                    request=httpx.Request("POST", "https://test.com"),
                    response=httpx.Response(429),
                ),
                "rate_limit_error",
            ),
            # Generic exceptions fall back to "unknown"
            (Exception("Network connection error"), "unknown"),
            (Exception("Invalid API key"), "unknown"),
            (Exception("Some random error"), "unknown"),
        ]

        for exception, expected_type in test_cases:
            error_type, _ = ai_agent._categorize_error(exception)
            assert error_type == expected_type

    def test_config_with_max_retries(self):
        """Test configuration includes max_retries setting."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_API_KEY": "test-key",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test-deployment",
                "AI_MAX_RETRIES": "5",
            },
        ):
            config = AIAgentConfig.from_env()
            assert config.max_retries == 5

    @pytest.mark.asyncio
    async def test_enhanced_response_fields(self, ai_agent):
        """Test that responses include enhanced fields."""
        from unittest.mock import Mock

        mock_usage = Mock()
        mock_usage.total_tokens = 75

        mock_result = Mock()
        mock_result.data = "Test response"
        mock_result.usage.return_value = mock_usage

        with patch.object(
            ai_agent._agent, "run", new_callable=AsyncMock, return_value=mock_result
        ):
            response = await ai_agent.send_message("Hello, AI!")

            assert hasattr(response, "error_type")
            assert hasattr(response, "retry_count")
            assert response.error_type is None  # No error
            assert response.retry_count == 0  # No retries needed


@pytest.mark.integration
class TestAIAgentIntegration:
    """Integration tests for AI Agent (require actual Azure OpenAI setup)."""

    @pytest.mark.skipif(
        not all(
            [
                os.getenv("AZURE_OPENAI_ENDPOINT"),
                os.getenv("AZURE_OPENAI_API_KEY"),
                os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            ]
        ),
        reason="Azure OpenAI credentials not available",
    )
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test with real Azure OpenAI API (requires credentials)."""
        config = AIAgentConfig.from_env()
        agent = AIAgent(config)

        response = await agent.send_message(
            "Hello! Please respond with exactly 'Integration test successful'"
        )

        assert response.success is True
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0
        assert response.error is None
