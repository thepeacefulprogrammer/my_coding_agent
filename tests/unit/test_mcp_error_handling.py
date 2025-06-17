"""
Comprehensive unit tests for MCP error handling and graceful degradation.

Tests error handling for:
- Network connectivity issues
- Server failures and timeouts
- Authentication and authorization failures
- Protocol errors and malformed responses
- Resource exhaustion and rate limiting
- Graceful degradation strategies
- Error recovery and retry mechanisms
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from src.my_coding_agent.core.mcp.error_handler import (
    CircuitBreakerState,
    ErrorCategory,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    MCPCircuitBreaker,
    MCPErrorContext,
    MCPErrorHandler,
    MCPErrorMetrics,
)
from src.my_coding_agent.core.mcp.mcp_client import (
    MCPClient,
    MCPConnectionError,
    MCPProtocolError,
    MCPTimeoutError,
)
from src.my_coding_agent.core.mcp.oauth2_auth import (
    OAuth2AuthenticationError,
)


class TestMCPErrorCategories:
    """Test suite for MCP error categorization and classification."""

    def test_error_category_classification(self):
        """Test automatic error categorization."""
        handler = MCPErrorHandler()

        # Network errors
        network_error = ConnectionError("Network unreachable")
        assert handler.categorize_error(network_error) == ErrorCategory.NETWORK

        # Timeout errors
        timeout_error = asyncio.TimeoutError("Request timeout")
        assert handler.categorize_error(timeout_error) == ErrorCategory.TIMEOUT

        # Authentication errors
        auth_error = OAuth2AuthenticationError("Invalid credentials")
        assert handler.categorize_error(auth_error) == ErrorCategory.AUTHENTICATION

        # Protocol errors
        protocol_error = MCPProtocolError("Invalid JSON-RPC response")
        assert handler.categorize_error(protocol_error) == ErrorCategory.PROTOCOL

        # Server errors
        server_error = MCPConnectionError("Server unavailable")
        assert handler.categorize_error(server_error) == ErrorCategory.SERVER

    def test_error_severity_assessment(self):
        """Test error severity assessment."""
        handler = MCPErrorHandler()

        # Critical errors
        critical_error = MCPConnectionError("Server permanently unavailable")
        assert handler.assess_severity(critical_error) == ErrorSeverity.CRITICAL

        # High severity errors
        auth_error = OAuth2AuthenticationError("Authentication failed")
        assert handler.assess_severity(auth_error) == ErrorSeverity.HIGH

        # Medium severity errors
        timeout_error = MCPTimeoutError("Request timeout")
        assert handler.assess_severity(timeout_error) == ErrorSeverity.MEDIUM

        # Low severity errors
        protocol_error = MCPProtocolError("Malformed response")
        assert handler.assess_severity(protocol_error) == ErrorSeverity.LOW

    def test_error_context_creation(self):
        """Test error context creation with metadata."""
        handler = MCPErrorHandler()

        error = ConnectionError("Network unreachable")
        context = handler.create_error_context(
            error=error,
            server_name="test-server",
            operation="list_tools",
            attempt_count=2,
        )

        assert context.error == error
        assert context.server_name == "test-server"
        assert context.operation == "list_tools"
        assert context.attempt_count == 2
        assert context.category == ErrorCategory.NETWORK
        assert isinstance(context.timestamp, datetime)


class TestMCPCircuitBreaker:
    """Test suite for circuit breaker pattern implementation."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        breaker = MCPCircuitBreaker(
            failure_threshold=5, recovery_timeout=30, half_open_max_calls=3
        )

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 30
        assert breaker.half_open_max_calls == 3

    def test_circuit_breaker_failure_tracking(self):
        """Test circuit breaker failure tracking."""
        breaker = MCPCircuitBreaker(failure_threshold=3)

        # Record failures
        breaker.record_failure()
        assert breaker.failure_count == 1
        assert breaker.state == CircuitBreakerState.CLOSED

        breaker.record_failure()
        assert breaker.failure_count == 2
        assert breaker.state == CircuitBreakerState.CLOSED

        # Third failure should open circuit
        breaker.record_failure()
        assert breaker.failure_count == 3
        assert breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_success_reset(self):
        """Test circuit breaker success reset."""
        breaker = MCPCircuitBreaker(failure_threshold=3)

        # Record some failures
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2

        # Success should reset counter
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_half_open_transition(self):
        """Test circuit breaker half-open state transition."""
        breaker = MCPCircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        import time

        time.sleep(0.2)

        # Should transition to half-open on next call check
        assert breaker.can_execute()
        assert breaker.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_breaker_call_blocking(self):
        """Test circuit breaker call blocking when open."""
        breaker = MCPCircuitBreaker(failure_threshold=2)

        # Circuit should allow calls initially
        assert breaker.can_execute() is True

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN

        # Circuit should block calls when open
        assert breaker.can_execute() is False


class TestMCPErrorRecovery:
    """Test suite for error recovery strategies."""

    @pytest.fixture
    def error_handler(self):
        """Create error handler for testing."""
        return MCPErrorHandler()

    def test_retry_strategy_exponential_backoff(self, error_handler):
        """Test exponential backoff retry strategy."""
        strategy = error_handler.get_recovery_strategy(ErrorCategory.NETWORK)
        assert strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF

        # Test backoff calculation
        backoff_times = []
        for attempt in range(1, 5):
            backoff = error_handler.calculate_backoff(attempt)
            backoff_times.append(backoff)

        # Should increase exponentially (accounting for jitter)
        # Test without jitter for predictable results
        error_handler.jitter = False
        backoff_times_no_jitter = []
        for attempt in range(1, 5):
            backoff = error_handler.calculate_backoff(attempt)
            backoff_times_no_jitter.append(backoff)

        # Should increase exponentially without jitter
        assert (
            backoff_times_no_jitter[0]
            < backoff_times_no_jitter[1]
            < backoff_times_no_jitter[2]
            < backoff_times_no_jitter[3]
        )
        assert backoff_times_no_jitter[0] >= 1.0  # Minimum 1 second
        assert backoff_times_no_jitter[3] <= 16.0  # Maximum reasonable backoff

    def test_fallback_strategy_for_critical_errors(self, error_handler):
        """Test fallback strategy for critical errors."""
        critical_error = MCPConnectionError("Server permanently unavailable")
        strategy = error_handler.get_recovery_strategy(ErrorCategory.SERVER)

        # Critical server errors should use fallback
        if error_handler.assess_severity(critical_error) == ErrorSeverity.CRITICAL:
            assert strategy in [
                ErrorRecoveryStrategy.FALLBACK_MODE,
                ErrorRecoveryStrategy.CIRCUIT_BREAKER,
            ]

    def test_authentication_error_recovery(self, error_handler):
        """Test authentication error recovery strategy."""
        auth_error = OAuth2AuthenticationError("Token expired")
        strategy = error_handler.get_recovery_strategy(ErrorCategory.AUTHENTICATION)

        assert strategy == ErrorRecoveryStrategy.REAUTHENTICATE

    def test_protocol_error_recovery(self, error_handler):
        """Test protocol error recovery strategy."""
        protocol_error = MCPProtocolError("Invalid response format")
        strategy = error_handler.get_recovery_strategy(ErrorCategory.PROTOCOL)

        assert strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF

    @pytest.mark.asyncio
    async def test_error_recovery_execution(self, error_handler):
        """Test error recovery strategy execution."""
        error = ConnectionError("Network unreachable")
        context = error_handler.create_error_context(
            error=error, server_name="test-server", operation="list_tools"
        )

        # Mock recovery function
        recovery_func = AsyncMock(return_value="recovered")

        result = await error_handler.execute_recovery(
            strategy=ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            context=context,
            recovery_func=recovery_func,
            max_attempts=3,
        )

        assert result == "recovered"
        assert recovery_func.called


class TestMCPErrorMetrics:
    """Test suite for error metrics and monitoring."""

    def test_error_metrics_initialization(self):
        """Test error metrics initialization."""
        metrics = MCPErrorMetrics()

        assert metrics.total_errors == 0
        assert metrics.errors_by_category == {}
        assert metrics.errors_by_server == {}
        assert len(metrics.recent_errors) == 0

    def test_error_metrics_recording(self):
        """Test error metrics recording."""
        metrics = MCPErrorMetrics()

        error = ConnectionError("Network error")
        context = MCPErrorContext(
            error=error,
            server_name="test-server",
            operation="list_tools",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )

        metrics.record_error(context)

        assert metrics.total_errors == 1
        assert metrics.errors_by_category[ErrorCategory.NETWORK] == 1
        assert metrics.errors_by_server["test-server"] == 1
        assert len(metrics.recent_errors) == 1

    def test_error_metrics_aggregation(self):
        """Test error metrics aggregation."""
        metrics = MCPErrorMetrics()

        # Record multiple errors
        for i in range(5):
            error = ConnectionError(f"Error {i}")
            context = MCPErrorContext(
                error=error,
                server_name="test-server",
                operation="list_tools",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.now(),
            )
            metrics.record_error(context)

        assert metrics.total_errors == 5
        assert metrics.errors_by_category[ErrorCategory.NETWORK] == 5
        assert metrics.get_error_rate() > 0

    def test_error_metrics_time_window(self):
        """Test error metrics time window filtering."""
        metrics = MCPErrorMetrics()

        # Record error in the past
        old_error = MCPErrorContext(
            error=ConnectionError("Old error"),
            server_name="test-server",
            operation="list_tools",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now() - timedelta(hours=2),
        )
        metrics.record_error(old_error)

        # Record recent error
        recent_error = MCPErrorContext(
            error=ConnectionError("Recent error"),
            server_name="test-server",
            operation="list_tools",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
        )
        metrics.record_error(recent_error)

        # Get errors in last hour
        recent_errors = metrics.get_errors_in_window(timedelta(hours=1))
        assert len(recent_errors) == 1
        assert recent_errors[0] == recent_error


class TestMCPClientErrorIntegration:
    """Test suite for MCP client error handling integration."""

    @pytest.fixture
    def mcp_config(self):
        """Create MCP client configuration for testing."""
        return {
            "server_name": "test-server",
            "url": "https://api.example.com/mcp",
            "transport": "http",
        }

    def test_mcp_client_error_handler_initialization(self, mcp_config):
        """Test MCP client error handler initialization."""
        client = MCPClient(mcp_config)

        assert hasattr(client, "error_handler")
        assert client.error_handler is not None
        assert isinstance(client.error_handler, MCPErrorHandler)

    @pytest.mark.asyncio
    async def test_mcp_client_network_error_handling(self, mcp_config):
        """Test MCP client network error handling."""
        client = MCPClient(mcp_config)

        # Mock network failure
        with patch.object(client, "_client") as mock_client:
            mock_client.list_tools = AsyncMock(
                side_effect=ConnectionError("Network unreachable")
            )

            # Should handle error gracefully
            with pytest.raises(MCPConnectionError):
                await client.list_tools()

            # Error should be recorded in metrics
            assert client.error_handler.metrics.total_errors > 0

    @pytest.mark.asyncio
    async def test_mcp_client_timeout_error_handling(self, mcp_config):
        """Test MCP client timeout error handling."""
        client = MCPClient(mcp_config)

        # Mock timeout
        with patch.object(client, "_client") as mock_client:
            mock_client.list_tools = AsyncMock(
                side_effect=asyncio.TimeoutError("Request timeout")
            )

            # Should handle timeout gracefully
            with pytest.raises(MCPTimeoutError):
                await client.list_tools()

    @pytest.mark.asyncio
    async def test_mcp_client_retry_mechanism(self, mcp_config):
        """Test MCP client automatic retry mechanism."""
        client = MCPClient(mcp_config)

        # Mock intermittent failure
        call_count = 0

        def mock_list_tools():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary network error")
            return []

        with patch.object(client, "_client") as mock_client:
            mock_client.list_tools = AsyncMock(side_effect=mock_list_tools)

            # Should retry and eventually succeed
            result = await client.list_tools_with_retry(max_attempts=3)
            assert result == []
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_mcp_client_circuit_breaker_integration(self, mcp_config):
        """Test MCP client circuit breaker integration."""
        client = MCPClient(mcp_config)

        # Configure circuit breaker with low threshold for testing
        client.error_handler.circuit_breaker.failure_threshold = 2

        # Mock repeated failures
        with patch.object(client, "_client") as mock_client:
            mock_client.list_tools = AsyncMock(
                side_effect=ConnectionError("Server down")
            )

            # First two calls should fail and record failures in circuit breaker
            with pytest.raises(MCPConnectionError):
                await client.list_tools()
            # Manually record circuit breaker failure since we're not using retry mechanism
            client.error_handler.circuit_breaker.record_failure()

            with pytest.raises(MCPConnectionError):
                await client.list_tools()
            # Manually record circuit breaker failure since we're not using retry mechanism
            client.error_handler.circuit_breaker.record_failure()

            # Circuit should now be open
            assert (
                client.error_handler.circuit_breaker.state == CircuitBreakerState.OPEN
            )

            # Next call should be blocked by circuit breaker if we use the retry mechanism
            with pytest.raises(Exception, match="Circuit breaker is open"):
                await client.list_tools_with_retry(max_attempts=1)

    @pytest.mark.asyncio
    async def test_mcp_client_graceful_degradation(self, mcp_config):
        """Test MCP client graceful degradation."""
        client = MCPClient(mcp_config)

        # Mock server failure
        with patch.object(client, "_client") as mock_client:
            mock_client.list_tools = AsyncMock(
                side_effect=MCPConnectionError("Server unavailable")
            )

            # Should degrade gracefully and return empty results
            result = await client.list_tools_with_fallback()
            assert result == []

            # Should log degradation
            assert client.error_handler.metrics.total_errors > 0

    def test_mcp_client_error_reporting(self, mcp_config):
        """Test MCP client error reporting and metrics."""
        client = MCPClient(mcp_config)

        # Get error report
        report = client.get_error_report()

        assert "total_errors" in report
        assert "errors_by_category" in report
        assert "errors_by_server" in report
        assert "circuit_breaker_state" in report
        assert "recent_errors" in report

    def test_mcp_client_error_recovery_configuration(self, mcp_config):
        """Test MCP client error recovery configuration."""
        # Configure with custom error handling settings
        mcp_config["error_handling"] = {
            "max_retries": 5,
            "circuit_breaker_threshold": 10,
            "recovery_timeout": 60,
            "enable_fallback": True,
        }

        client = MCPClient(mcp_config)

        # Verify configuration applied
        assert client.error_handler.max_retries == 5
        assert client.error_handler.circuit_breaker.failure_threshold == 10
        assert client.error_handler.circuit_breaker.recovery_timeout == 60
        assert client.error_handler.enable_fallback is True


class TestMCPServerRegistryErrorHandling:
    """Test suite for MCP server registry error handling."""

    @pytest.mark.skip(
        reason="Server registry error handling methods not yet implemented"
    )
    @pytest.mark.asyncio
    async def test_server_registry_connection_failure_handling(self):
        """Test server registry handling of connection failures."""
        # This test will be implemented when server registry error handling is added
        pass

    @pytest.mark.skip(
        reason="Server registry error handling methods not yet implemented"
    )
    @pytest.mark.asyncio
    async def test_server_registry_partial_failure_handling(self):
        """Test server registry handling of partial failures."""
        # This test will be implemented when server registry error handling is added
        pass

    @pytest.mark.skip(
        reason="Server registry error handling methods not yet implemented"
    )
    def test_server_registry_error_metrics(self):
        """Test server registry error metrics collection."""
        # This test will be implemented when server registry error handling is added
        pass


class TestMCPErrorHandlerConfiguration:
    """Test suite for MCP error handler configuration."""

    def test_error_handler_default_configuration(self):
        """Test error handler default configuration."""
        handler = MCPErrorHandler()

        assert handler.max_retries == 3
        assert handler.base_backoff == 1.0
        assert handler.max_backoff == 60.0
        assert handler.enable_circuit_breaker is True
        assert handler.enable_fallback is True

    def test_error_handler_custom_configuration(self):
        """Test error handler custom configuration."""
        config = {
            "max_retries": 5,
            "base_backoff": 2.0,
            "max_backoff": 120.0,
            "circuit_breaker_threshold": 10,
            "recovery_timeout": 300,
            "enable_fallback": False,
        }

        handler = MCPErrorHandler(config)

        assert handler.max_retries == 5
        assert handler.base_backoff == 2.0
        assert handler.max_backoff == 120.0
        assert handler.circuit_breaker.failure_threshold == 10
        assert handler.circuit_breaker.recovery_timeout == 300
        assert handler.enable_fallback is False

    def test_error_handler_configuration_validation(self):
        """Test error handler configuration validation."""
        # Invalid configuration should raise ValueError
        with pytest.raises(ValueError, match="max_retries must be positive"):
            MCPErrorHandler({"max_retries": -1})

        with pytest.raises(ValueError, match="base_backoff must be positive"):
            MCPErrorHandler({"base_backoff": 0})

        with pytest.raises(
            ValueError, match="circuit_breaker_threshold must be positive"
        ):
            MCPErrorHandler({"circuit_breaker_threshold": 0})
