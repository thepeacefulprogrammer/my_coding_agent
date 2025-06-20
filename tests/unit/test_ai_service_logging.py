"""
Unit tests for AI service logging capabilities.

Tests comprehensive logging, sanitization, performance tracking,
and structured logging features for AI service operations.
"""

import asyncio
import logging
import time
from unittest.mock import MagicMock, patch

import pytest
from src.my_coding_agent.core.ai_services.ai_service_adapter import (
    AIResponse,
    AIServiceConfig,
    AIStreamingResponse,
)
from src.my_coding_agent.core.ai_services.logging_utils import (
    AIServiceLogger,
    LogContext,
    PerformanceMetrics,
    SensitiveDataSanitizer,
    logged_operation,
)


class TestSensitiveDataSanitizer:
    """Test the sensitive data sanitizer."""

    def test_sanitizer_initialization(self):
        """Test sanitizer initialization with default sensitive keys."""
        sanitizer = SensitiveDataSanitizer()

        assert "api_key" in sanitizer.sensitive_keys
        assert "password" in sanitizer.sensitive_keys
        assert "token" in sanitizer.sensitive_keys
        assert sanitizer.sanitized_value == "***REDACTED***"

    def test_sanitize_dict_with_sensitive_keys(self):
        """Test dictionary sanitization with sensitive keys."""
        sanitizer = SensitiveDataSanitizer()

        data = {
            "api_key": "secret123",
            "username": "testuser",
            "password": "mypassword",
            "public_data": "visible"
        }

        sanitized = sanitizer.sanitize_dict(data)

        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["username"] == "testuser"
        assert sanitized["public_data"] == "visible"

    def test_sanitize_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        sanitizer = SensitiveDataSanitizer()

        data = {
            "config": {
                "api_key": "secret123",
                "endpoint": "https://api.example.com"
            },
            "credentials": {
                "token": "bearer_token_123",
                "user": "testuser"
            }
        }

        sanitized = sanitizer.sanitize_dict(data)

        assert sanitized["config"]["api_key"] == "***REDACTED***"
        assert sanitized["config"]["endpoint"] == "https://api.example.com"
        assert sanitized["credentials"]["token"] == "***REDACTED***"
        assert sanitized["credentials"]["user"] == "testuser"

    def test_sanitize_config(self):
        """Test AI service configuration sanitization."""
        sanitizer = SensitiveDataSanitizer()

        config = AIServiceConfig(
            provider="test_provider",
            endpoint="https://api.example.com",
            api_key="secret_key_123",
            deployment_name="test_deployment"
        )

        sanitized = sanitizer.sanitize_config(config)

        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["provider"] == "test_provider"
        assert sanitized["endpoint"] == "https://api.example.com"
        assert sanitized["deployment_name"] == "test_deployment"

    def test_sanitize_content_truncation(self):
        """Test content sanitization and truncation."""
        sanitizer = SensitiveDataSanitizer()

        # Test normal content
        short_content = "This is a short message"
        assert sanitizer.sanitize_content(short_content) == short_content

        # Test long content truncation
        long_content = "A" * 1000
        sanitized = sanitizer.sanitize_content(long_content, max_length=100)
        assert len(sanitized) == 100 + len("...[TRUNCATED]")
        assert sanitized.endswith("...[TRUNCATED]")

    def test_case_insensitive_key_detection(self):
        """Test that sensitive key detection is case insensitive."""
        sanitizer = SensitiveDataSanitizer()

        data = {
            "API_KEY": "secret123",
            "Api-Key": "secret456",
            "PASSWORD": "mypassword"
        }

        sanitized = sanitizer.sanitize_dict(data)

        assert sanitized["API_KEY"] == "***REDACTED***"
        assert sanitized["Api-Key"] == "***REDACTED***"
        assert sanitized["PASSWORD"] == "***REDACTED***"


class TestLogContext:
    """Test the log context data structure."""

    def test_log_context_creation(self):
        """Test log context creation with all fields."""
        context = LogContext(
            operation="test_operation",
            provider="test_provider",
            endpoint="https://api.example.com",
            deployment_name="test_deployment",
            correlation_id="test_correlation_123",
            user_id="user123",
            session_id="session456"
        )

        assert context.operation == "test_operation"
        assert context.provider == "test_provider"
        assert context.endpoint == "https://api.example.com"
        assert context.deployment_name == "test_deployment"
        assert context.correlation_id == "test_correlation_123"
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert isinstance(context.metadata, dict)

    def test_log_context_minimal(self):
        """Test log context creation with minimal fields."""
        context = LogContext(operation="test_operation")

        assert context.operation == "test_operation"
        assert context.provider is None
        assert context.endpoint is None
        assert context.correlation_id is None


class TestPerformanceMetrics:
    """Test the performance metrics tracking."""

    def test_performance_metrics_creation(self):
        """Test performance metrics creation."""
        start_time = time.time()
        metrics = PerformanceMetrics(
            operation="test_operation",
            start_time=start_time
        )

        assert metrics.operation == "test_operation"
        assert metrics.start_time == start_time
        assert metrics.end_time is None
        assert metrics.duration_ms is None
        assert metrics.success is False
        assert metrics.retry_count == 0

    def test_performance_metrics_finish(self):
        """Test finishing performance metrics calculation."""
        start_time = time.time()
        metrics = PerformanceMetrics(
            operation="test_operation",
            start_time=start_time
        )

        # Simulate some work
        time.sleep(0.01)

        metrics.finish(success=True, error_type=None)

        assert metrics.end_time is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms > 0
        assert metrics.success is True
        assert metrics.error_type is None

    def test_performance_metrics_finish_with_error(self):
        """Test finishing performance metrics with error."""
        start_time = time.time()
        metrics = PerformanceMetrics(
            operation="test_operation",
            start_time=start_time
        )

        metrics.finish(success=False, error_type="TestError")

        assert metrics.success is False
        assert metrics.error_type == "TestError"


class TestAIServiceLogger:
    """Test the enhanced AI service logger."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = AIServiceLogger("test_logger")

        assert logger.logger.name == "test_logger"
        assert isinstance(logger.sanitizer, SensitiveDataSanitizer)
        assert isinstance(logger._metrics, dict)

    @patch('logging.getLogger')
    def test_structured_logging(self, mock_get_logger):
        """Test structured logging with context."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AIServiceLogger("test_logger")
        context = LogContext(
            operation="test_operation",
            provider="test_provider",
            correlation_id="test_123"
        )

        logger.info("Test message", context=context)

        # Verify log was called
        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args

        assert args[0] == logging.INFO  # log level
        assert "test_operation" in args[1]  # formatted message
        assert "structured_data" in kwargs["extra"]

    def test_connection_logging_methods(self):
        """Test specialized connection logging methods."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            logger = AIServiceLogger("test_logger")
            context = LogContext(operation="connect", provider="test")

            # Test connection attempt logging
            logger.log_connection_attempt(context, 1, 3)
            assert mock_logger.log.called

            # Reset mock
            mock_logger.reset_mock()

            # Test connection success logging
            logger.log_connection_success(context, 100.0, 1)
            assert mock_logger.log.called

            # Reset mock
            mock_logger.reset_mock()

            # Test connection failure logging
            error = Exception("Connection failed")
            logger.log_connection_failure(context, error, 3)
            assert mock_logger.log.called

    def test_query_logging_methods(self):
        """Test specialized query logging methods."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            logger = AIServiceLogger("test_logger")
            context = LogContext(operation="query", provider="test")

            # Test query request logging
            logger.log_query_request(context, "test query", {"param": "value"})
            assert mock_logger.log.called

            # Reset mock
            mock_logger.reset_mock()

            # Test query response logging
            response = AIResponse(
                content="test response",
                success=True,
                response_time=0.5,
                retry_count=0
            )
            logger.log_query_response(context, response, 500.0)
            assert mock_logger.log.called

    def test_streaming_logging_methods(self):
        """Test specialized streaming logging methods."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            logger = AIServiceLogger("test_logger")
            context = LogContext(operation="streaming", provider="test")

            # Test streaming start
            logger.log_streaming_start(context, "test query")
            assert mock_logger.log.called

            # Reset mock
            mock_logger.reset_mock()

            # Test streaming chunk
            chunk = AIStreamingResponse(
                content="chunk content",
                is_complete=False,
                chunk_index=0
            )
            logger.log_streaming_chunk(context, chunk)
            assert mock_logger.log.called

            # Reset mock
            mock_logger.reset_mock()

            # Test streaming complete
            logger.log_streaming_complete(context, 5, 1000.0)
            assert mock_logger.log.called

    def test_performance_tracking(self):
        """Test performance tracking functionality."""
        logger = AIServiceLogger("test_logger")
        context = LogContext(operation="test", provider="test")

        # Start tracking
        metrics_id = logger.start_performance_tracking("test_operation", context)
        assert metrics_id in logger._metrics

        # Finish tracking
        metrics = logger.finish_performance_tracking(
            metrics_id, context, success=True, retry_count=2
        )

        assert metrics is not None
        assert metrics.operation == "test_operation"
        assert metrics.success is True
        assert metrics.retry_count == 2
        assert metrics.duration_ms is not None
        assert metrics_id not in logger._metrics  # Should be removed

    @pytest.mark.asyncio
    async def test_performance_context_manager(self):
        """Test async performance context manager."""
        logger = AIServiceLogger("test_logger")
        context = LogContext(operation="test", provider="test")

        # Test successful operation
        async with logger.performance_context("test_operation", context) as metrics_id:
            assert metrics_id in logger._metrics
            await asyncio.sleep(0.01)  # Simulate work

        # Metrics should be cleaned up
        assert metrics_id not in logger._metrics

    @pytest.mark.asyncio
    async def test_performance_context_manager_with_error(self):
        """Test async performance context manager with error."""
        logger = AIServiceLogger("test_logger")
        context = LogContext(operation="test", provider="test")

        # Test operation with error
        with pytest.raises(ValueError):
            async with logger.performance_context("test_operation", context) as metrics_id:
                assert metrics_id in logger._metrics
                raise ValueError("Test error")

        # Metrics should be cleaned up even with error
        assert metrics_id not in logger._metrics

    def test_endpoint_sanitization(self):
        """Test endpoint URL sanitization."""
        logger = AIServiceLogger("test_logger")

        # Test endpoint with query parameters
        endpoint_with_params = "https://api.example.com/v1/chat?api_key=secret"
        sanitized = logger._sanitize_endpoint(endpoint_with_params)
        assert sanitized == "https://api.example.com/v1/chat"

        # Test endpoint with fragment
        endpoint_with_fragment = "https://api.example.com/v1/chat#token=secret"
        sanitized = logger._sanitize_endpoint(endpoint_with_fragment)
        assert sanitized == "https://api.example.com/v1/chat"

        # Test clean endpoint
        clean_endpoint = "https://api.example.com/v1/chat"
        sanitized = logger._sanitize_endpoint(clean_endpoint)
        assert sanitized == clean_endpoint

        # Test None endpoint
        assert logger._sanitize_endpoint(None) is None


class TestLoggedOperationDecorator:
    """Test the logged operation decorator."""

    def test_decorator_with_sync_function(self):
        """Test decorator with synchronous function."""

        class TestClass:
            def __init__(self):
                self._ai_logger = AIServiceLogger("test")
                self.provider = "test_provider"
                self.endpoint = "https://api.example.com"
                self.deployment_name = "test_deployment"

            @logged_operation("test_sync_operation")
            def test_method(self, value):
                return value * 2

        obj = TestClass()
        result = obj.test_method(5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_decorator_with_async_function(self):
        """Test decorator with asynchronous function."""

        class TestClass:
            def __init__(self):
                self._ai_logger = AIServiceLogger("test")
                self.provider = "test_provider"
                self.endpoint = "https://api.example.com"
                self.deployment_name = "test_deployment"

            @logged_operation("test_async_operation")
            async def test_method(self, value):
                await asyncio.sleep(0.01)
                return value * 2

        obj = TestClass()
        result = await obj.test_method(5)

        assert result == 10

    def test_decorator_without_logger(self):
        """Test decorator behavior when logger is not available."""

        class TestClass:
            @logged_operation("test_operation")
            def test_method(self, value):
                return value * 2

        obj = TestClass()
        result = obj.test_method(5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_decorator_with_error(self):
        """Test decorator behavior with errors."""

        class TestClass:
            def __init__(self):
                self._ai_logger = AIServiceLogger("test")
                self.provider = "test_provider"

            @logged_operation("test_error_operation")
            async def test_method(self):
                raise ValueError("Test error")

        obj = TestClass()

        with pytest.raises(ValueError, match="Test error"):
            await obj.test_method()


@pytest.mark.asyncio
async def test_integration_logging_flow():
    """Test integration of logging components in a realistic flow."""
    # This test verifies that all logging components work together
    logger = AIServiceLogger("integration_test")

    context = LogContext(
        operation="integration_test",
        provider="test_provider",
        endpoint="https://api.example.com",
        deployment_name="test_deployment",
        correlation_id="integration_123"
    )

    # Test full flow with performance tracking
    async with logger.performance_context("integration_operation", context):
        # Log connection attempt
        logger.log_connection_attempt(context, 1, 3)

        # Simulate connection delay
        await asyncio.sleep(0.01)

        # Log connection success
        logger.log_connection_success(context, 50.0, 1)

        # Log query request
        logger.log_query_request(context, "test query", {"param": "value"})

        # Log query response
        response = AIResponse(
            content="test response",
            success=True,
            response_time=0.1,
            retry_count=0
        )
        logger.log_query_response(context, response, 100.0)

    # Performance tracking should be completed and cleaned up
    assert len(logger._metrics) == 0
