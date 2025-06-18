"""Unit tests for AI Agent integration with foundation services."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.ai_services.configuration_service import ConfigurationService
from my_coding_agent.core.ai_services.error_handling_service import (
    ErrorCategory,
    ErrorHandlingService,
    RetryableError,
)


class TestAIAgentFoundationServices:
    """Test AI Agent integration with foundation services."""

    @pytest.fixture
    def mock_config_service(self):
        """Create a mock ConfigurationService."""
        config_service = Mock(spec=ConfigurationService)
        config_service.azure_endpoint = "https://test.openai.azure.com/"
        config_service.azure_api_key = "test-key"
        config_service.deployment_name = "test-deployment"
        config_service.api_version = "2024-02-15-preview"
        config_service.max_tokens = 2000
        config_service.temperature = 0.7
        config_service.request_timeout = 30
        config_service.max_retries = 3
        # Remove get_all_settings call - we'll define the interface as we implement
        return config_service

    @pytest.fixture
    def mock_error_service(self):
        """Create a mock ErrorHandlingService."""
        error_service = Mock(spec=ErrorHandlingService)
        error_service.categorize_error.return_value = (
            ErrorCategory.UNKNOWN,
            "An unexpected error occurred",
        )
        error_service.is_retryable_error.return_value = False
        error_service.calculate_backoff_time.return_value = 1.0
        error_service.execute_with_retry = AsyncMock()
        error_service.safe_execute.return_value = (None, None)
        error_service.get_error_statistics.return_value = {
            "total_errors": 0,
            "total_retries": 0,
            "error_categories": {},
            "retryable_errors": 0,
            "non_retryable_errors": 0,
        }
        return error_service

    def test_ai_agent_uses_configuration_service(self, mock_config_service):
        """Test that AIAgent uses ConfigurationService instead of AIAgentConfig."""
        # Create AIAgent with configuration service
        agent = AIAgent(config_service=mock_config_service)

        # Verify that the agent uses configuration service
        assert agent.config_service == mock_config_service
        assert agent.config_service.azure_endpoint == "https://test.openai.azure.com/"
        assert agent.config_service.azure_api_key == "test-key"
        assert agent.config_service.deployment_name == "test-deployment"

    def test_ai_agent_uses_error_handling_service(
        self, mock_config_service, mock_error_service
    ):
        """Test that AIAgent uses ErrorHandlingService for error management."""
        # Create AIAgent with both services
        agent = AIAgent(
            config_service=mock_config_service, error_service=mock_error_service
        )

        # Verify that the agent uses error handling service
        assert agent.error_service == mock_error_service

    @pytest.mark.asyncio
    async def test_ai_agent_error_handling_integration(
        self, mock_config_service, mock_error_service
    ):
        """Test that AIAgent uses ErrorHandlingService for error categorization."""

        # Configure mock to return specific error categorization
        mock_error_service.categorize_error.return_value = (
            ErrorCategory.TIMEOUT_ERROR,
            "Request timed out. The service may be experiencing high load. Please try again.",
        )
        mock_error_service.is_retryable_error.return_value = (
            False  # Non-retryable for single call test
        )

        # Create agent
        agent = AIAgent(
            config_service=mock_config_service, error_service=mock_error_service
        )

        # Mock agent._agent.run to raise TimeoutError
        with patch.object(
            agent._agent,
            "run",
            new_callable=AsyncMock,
            side_effect=asyncio.TimeoutError(),
        ):
            response = await agent.send_message("Hello, AI!")

            # Verify error handling service was called
            mock_error_service.categorize_error.assert_called_once()
            mock_error_service.is_retryable_error.assert_called_once_with(
                ErrorCategory.TIMEOUT_ERROR
            )

            # Verify response contains proper error info
            assert response.success is False
            assert response.error_type == "timeout_error"  # ErrorCategory.name.lower()
            assert "Request timed out" in response.error

    @pytest.mark.asyncio
    async def test_ai_agent_retry_with_error_service(
        self, mock_config_service, mock_error_service
    ):
        """Test that AIAgent uses ErrorHandlingService for retry logic."""

        # Configure mock for retryable error
        mock_error_service.categorize_error.return_value = (
            ErrorCategory.CONNECTION_ERROR,
            "Network connection failed. Please check your internet connection.",
        )
        mock_error_service.is_retryable_error.return_value = True
        mock_error_service.calculate_backoff_time.return_value = (
            0.1  # Fast retry for test
        )

        # Mock execute_with_retry to simulate retry behavior
        mock_error_service.execute_with_retry.side_effect = RetryableError(
            "Max retries exceeded", ConnectionError("Network error"), 3
        )

        # Create agent
        agent = AIAgent(
            config_service=mock_config_service, error_service=mock_error_service
        )

        # Send message (should trigger retry logic)
        response = await agent.send_message("Hello, AI!")

        # Verify retry mechanism was invoked
        assert response.success is False
        assert response.error_type == "connection_error"  # ErrorCategory.name.lower()
        assert response.retry_count > 0

    def test_ai_agent_configuration_service_properties(self, mock_config_service):
        """Test that AIAgent properly exposes configuration through service."""
        agent = AIAgent(config_service=mock_config_service)

        # Test configuration access through service
        assert agent.max_tokens == mock_config_service.max_tokens
        assert agent.temperature == mock_config_service.temperature
        assert agent.request_timeout == mock_config_service.request_timeout

    def test_ai_agent_error_statistics_tracking(
        self, mock_config_service, mock_error_service
    ):
        """Test that AIAgent can access error statistics from ErrorHandlingService."""
        agent = AIAgent(
            config_service=mock_config_service, error_service=mock_error_service
        )

        # Get error statistics
        stats = agent.get_error_statistics()

        # Verify statistics are retrieved from error service
        mock_error_service.get_error_statistics.assert_called_once()
        assert "total_errors" in stats
        assert "total_retries" in stats
        assert "error_categories" in stats

    @pytest.mark.asyncio
    async def test_ai_agent_safe_execution_with_error_service(
        self, mock_config_service, mock_error_service
    ):
        """Test that AIAgent uses ErrorHandlingService for safe execution."""

        # Configure mock to return safe execution result
        mock_error_service.safe_execute.return_value = (
            "Success result",
            None,  # No error
        )

        agent = AIAgent(
            config_service=mock_config_service, error_service=mock_error_service
        )

        # Test safe execution of a function
        def test_function():
            return "Success result"

        result, error_info = agent.safe_execute(test_function)

        # Verify safe execution was used
        mock_error_service.safe_execute.assert_called_once()
        assert result == "Success result"
        assert error_info is None

    def test_ai_agent_backwards_compatibility(self):
        """Test that AIAgent still works with legacy AIAgentConfig for backwards compatibility."""
        # Create legacy config
        legacy_config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test-key",
            deployment_name="test-deployment",
        )

        # Should work with legacy config (backwards compatibility)
        agent = AIAgent(legacy_config)

        assert agent.config == legacy_config
        assert hasattr(agent, "_model")
        assert hasattr(agent, "_agent")

    def test_ai_agent_service_dependency_injection(
        self, mock_config_service, mock_error_service
    ):
        """Test that services are properly injected as dependencies."""
        agent = AIAgent(
            config_service=mock_config_service, error_service=mock_error_service
        )

        # Verify both services are injected
        assert agent.config_service is mock_config_service
        assert agent.error_service is mock_error_service

        # Verify services are properly stored
        assert agent.config_service is mock_config_service
        assert agent.error_service is mock_error_service

    @pytest.mark.asyncio
    async def test_ai_agent_error_service_categorization_accuracy(
        self, mock_config_service, mock_error_service
    ):
        """Test that different error types are properly categorized by ErrorHandlingService."""

        test_cases = [
            (ConnectionError("Network failed"), ErrorCategory.CONNECTION_ERROR),
            (asyncio.TimeoutError(), ErrorCategory.TIMEOUT_ERROR),
            (ValueError("Invalid input"), ErrorCategory.VALIDATION_ERROR),
            (FileNotFoundError("File missing"), ErrorCategory.FILE_NOT_FOUND),
        ]

        agent = AIAgent(
            config_service=mock_config_service, error_service=mock_error_service
        )

        for exception, expected_category in test_cases:
            # Configure mock for this test case
            mock_error_service.categorize_error.return_value = (
                expected_category,
                f"Error: {str(exception)}",
            )

            # Mock agent run to raise the exception
            with patch.object(
                agent._agent, "run", new_callable=AsyncMock, side_effect=exception
            ):
                response = await agent.send_message("Test message")

                # Verify proper categorization
                assert response.success is False
                assert (
                    response.error_type == expected_category.name.lower()
                )  # ErrorCategory.name.lower()

            # Reset mock for next iteration
            mock_error_service.categorize_error.reset_mock()
