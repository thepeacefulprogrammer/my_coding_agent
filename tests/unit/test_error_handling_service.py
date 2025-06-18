"""Unit tests for ErrorHandlingService."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from src.my_coding_agent.core.ai_services.error_handling_service import (
    ErrorCategory,
    ErrorHandlingService,
    RetryPolicy,
)


class TestErrorHandlingService:
    """Test cases for ErrorHandlingService."""

    @pytest.fixture
    def error_service(self):
        """Create an ErrorHandlingService instance for testing."""
        return ErrorHandlingService()

    def test_categorize_error_file_not_found(self, error_service):
        """Test error categorization for FileNotFoundError."""
        error = FileNotFoundError("File not found")
        category, message = error_service.categorize_error(error)

        assert category == ErrorCategory.FILE_NOT_FOUND
        assert "file was not found" in message.lower()

    def test_categorize_error_connection_error(self, error_service):
        """Test error categorization for connection errors."""
        error = ConnectionError("Connection failed")
        category, message = error_service.categorize_error(error)

        assert category == ErrorCategory.CONNECTION_ERROR
        assert "connection" in message.lower()

    def test_categorize_error_timeout_error(self, error_service):
        """Test error categorization for timeout errors."""
        error = asyncio.TimeoutError("Request timed out")
        category, message = error_service.categorize_error(error)

        assert category == ErrorCategory.TIMEOUT_ERROR
        assert "timed out" in message.lower()

    def test_categorize_error_validation_error(self, error_service):
        """Test error categorization for validation errors."""
        error = ValueError("Invalid input")
        category, message = error_service.categorize_error(error)

        assert category == ErrorCategory.VALIDATION_ERROR
        assert "invalid input" in message.lower()

    def test_is_retryable_error_timeout(self, error_service):
        """Test that timeout errors are retryable."""
        assert error_service.is_retryable_error(ErrorCategory.TIMEOUT_ERROR)

    def test_is_not_retryable_error_validation(self, error_service):
        """Test that validation errors are not retryable."""
        assert not error_service.is_retryable_error(ErrorCategory.VALIDATION_ERROR)

    def test_calculate_backoff_time_exponential(self, error_service):
        """Test exponential backoff calculation."""
        assert error_service.calculate_backoff_time(0) == 1
        assert error_service.calculate_backoff_time(1) == 2
        assert error_service.calculate_backoff_time(2) == 4

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, error_service):
        """Test successful execution on first attempt."""
        mock_func = AsyncMock(return_value="success")

        result = await error_service.execute_with_retry(mock_func)

        assert result == "success"
        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retry(self, error_service):
        """Test successful execution after retries."""
        mock_func = AsyncMock()
        mock_func.side_effect = [ConnectionError("Connection failed"), "success"]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await error_service.execute_with_retry(mock_func, max_retries=3)

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self, error_service):
        """Test immediate failure for non-retryable errors."""
        mock_func = AsyncMock()
        mock_func.side_effect = ValueError("Invalid input")

        with pytest.raises(ValueError):
            await error_service.execute_with_retry(mock_func, max_retries=3)

        assert mock_func.call_count == 1

    def test_safe_execute_success(self, error_service):
        """Test safe execution with successful result."""

        def test_func():
            return "success"

        result, error = error_service.safe_execute(test_func)

        assert result == "success"
        assert error is None

    def test_safe_execute_with_error(self, error_service):
        """Test safe execution with error capture."""

        def test_func():
            raise ValueError("Test error")

        result, error = error_service.safe_execute(test_func)

        assert result is None
        assert error is not None
        assert error.category == ErrorCategory.VALIDATION_ERROR

    def test_get_retry_policy_default(self, error_service):
        """Test getting default retry policy."""
        policy = error_service.get_retry_policy()

        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 30.0
        assert policy.backoff_factor == 2.0

    def test_set_retry_policy_custom(self, error_service):
        """Test setting custom retry policy."""
        custom_policy = RetryPolicy(max_retries=5, base_delay=2.0)

        error_service.set_retry_policy(custom_policy)
        policy = error_service.get_retry_policy()

        assert policy.max_retries == 5
        assert policy.base_delay == 2.0

    def test_get_error_statistics_initial(self, error_service):
        """Test getting error statistics when no errors have occurred."""
        stats = error_service.get_error_statistics()

        assert stats["total_errors"] == 0
        assert stats["total_retries"] == 0
        assert stats["retryable_errors"] == 0
        assert stats["non_retryable_errors"] == 0

    def test_reset_error_statistics(self, error_service):
        """Test resetting error statistics."""
        # Generate some error first
        error_service.safe_execute(lambda: 1 / 0)

        # Reset and verify
        error_service.reset_error_statistics()
        stats = error_service.get_error_statistics()

        assert stats["total_errors"] == 0
