"""
Comprehensive error handling and graceful degradation for MCP failures.

This module provides:
- Error categorization and severity assessment
- Circuit breaker pattern for fault tolerance
- Retry mechanisms with exponential backoff
- Graceful degradation strategies
- Error metrics and monitoring
- Recovery strategies for different error types
"""

import asyncio
import logging
import random
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .oauth2_auth import OAuth2AuthenticationError, OAuth2TokenExpiredError

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of MCP errors for targeted handling."""

    NETWORK = "network"
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    PROTOCOL = "protocol"
    SERVER = "server"
    RESOURCE = "resource"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severity levels for error assessment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorRecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    RETRY_IMMEDIATE = "retry_immediate"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_MODE = "fallback_mode"
    REAUTHENTICATE = "reauthenticate"
    RATE_LIMIT_WAIT = "rate_limit_wait"
    FAIL_FAST = "fail_fast"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class MCPErrorContext:
    """Context information for MCP errors."""

    error: Exception
    server_name: str
    operation: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    attempt_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPErrorMetrics:
    """Metrics for tracking MCP errors."""

    total_errors: int = 0
    errors_by_category: dict[ErrorCategory, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    errors_by_server: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_severity: dict[ErrorSeverity, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=100))
    first_error_time: datetime | None = None
    last_error_time: datetime | None = None

    def record_error(self, context: MCPErrorContext) -> None:
        """Record an error in metrics."""
        self.total_errors += 1
        self.errors_by_category[context.category] += 1
        self.errors_by_server[context.server_name] += 1
        self.errors_by_severity[context.severity] += 1
        self.recent_errors.append(context)

        if self.first_error_time is None:
            self.first_error_time = context.timestamp
        self.last_error_time = context.timestamp

    def get_error_rate(self, window_minutes: int = 60) -> float:
        """Get error rate per minute in the specified window."""
        if not self.recent_errors:
            return 0.0

        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_count = sum(
            1 for error in self.recent_errors if error.timestamp >= cutoff_time
        )

        return recent_count / window_minutes if window_minutes > 0 else 0.0

    def get_errors_in_window(self, window: timedelta) -> list[MCPErrorContext]:
        """Get errors within the specified time window."""
        cutoff_time = datetime.now() - window
        return [error for error in self.recent_errors if error.timestamp >= cutoff_time]

    def get_server_error_rate(
        self, server_name: str, window_minutes: int = 60
    ) -> float:
        """Get error rate for a specific server."""
        if not self.recent_errors:
            return 0.0

        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        server_errors = sum(
            1
            for error in self.recent_errors
            if error.server_name == server_name and error.timestamp >= cutoff_time
        )

        return server_errors / window_minutes if window_minutes > 0 else 0.0


class MCPCircuitBreaker:
    """Circuit breaker implementation for MCP operations."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.half_open_calls = 0

    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (
                self.last_failure_time
                and datetime.now() - self.last_failure_time
                >= timedelta(seconds=self.recovery_timeout)
            ):
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls

        return False

    def record_success(self) -> None:
        """Record successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED

        self.failure_count = 0
        self.half_open_calls = 0

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if (
            self.state == CircuitBreakerState.HALF_OPEN
            or self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitBreakerState.OPEN

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1


class MCPErrorHandler:
    """Comprehensive error handler for MCP operations."""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize error handler.

        Args:
            config: Configuration dictionary for error handling
        """
        config = config or {}

        # Retry configuration
        self.max_retries = config.get("max_retries", 3)
        self.base_backoff = config.get("base_backoff", 1.0)
        self.max_backoff = config.get("max_backoff", 60.0)
        self.backoff_multiplier = config.get("backoff_multiplier", 2.0)
        self.jitter = config.get("jitter", True)

        # Circuit breaker configuration
        self.enable_circuit_breaker = config.get("enable_circuit_breaker", True)
        circuit_breaker_config = config.get("circuit_breaker", {})

        # Handle both nested and flat configuration
        failure_threshold = circuit_breaker_config.get(
            "failure_threshold"
        ) or config.get("circuit_breaker_threshold", 5)
        recovery_timeout = circuit_breaker_config.get("recovery_timeout") or config.get(
            "recovery_timeout", 60.0
        )

        self.circuit_breaker = MCPCircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=circuit_breaker_config.get("half_open_max_calls", 3),
        )

        # Fallback configuration
        self.enable_fallback = config.get("enable_fallback", True)

        # Metrics
        self.metrics = MCPErrorMetrics()

        # Validate configuration
        self._validate_config()

        logger.info("MCP error handler initialized with configuration")

    def _validate_config(self) -> None:
        """Validate error handler configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be positive")
        if self.base_backoff <= 0:
            raise ValueError("base_backoff must be positive")
        if self.max_backoff <= 0:
            raise ValueError("max_backoff must be positive")
        if self.circuit_breaker.failure_threshold <= 0:
            raise ValueError("circuit_breaker_threshold must be positive")

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error for targeted handling."""
        # Check timeout first since TimeoutError is a subclass of OSError
        if isinstance(error, asyncio.TimeoutError):
            return ErrorCategory.TIMEOUT
        elif isinstance(error, (ConnectionError, OSError)):
            return ErrorCategory.NETWORK
        elif isinstance(error, (OAuth2AuthenticationError, OAuth2TokenExpiredError)):
            return ErrorCategory.AUTHENTICATION
        elif isinstance(error, PermissionError):
            return ErrorCategory.AUTHORIZATION
        elif "protocol" in str(error).lower() or "json-rpc" in str(error).lower():
            return ErrorCategory.PROTOCOL
        elif "server" in str(error).lower() or "unavailable" in str(error).lower():
            return ErrorCategory.SERVER
        elif (
            "rate limit" in str(error).lower()
            or "too many requests" in str(error).lower()
        ):
            return ErrorCategory.RATE_LIMIT
        elif "resource" in str(error).lower() or "memory" in str(error).lower():
            return ErrorCategory.RESOURCE
        else:
            return ErrorCategory.UNKNOWN

    def assess_severity(self, error: Exception) -> ErrorSeverity:
        """Assess error severity."""
        error_str = str(error).lower()

        # Critical errors
        if any(
            keyword in error_str
            for keyword in [
                "permanently",
                "fatal",
                "critical",
                "corrupted",
                "invalid credentials",
            ]
        ):
            return ErrorSeverity.CRITICAL

        # High severity errors
        elif any(
            keyword in error_str
            for keyword in [
                "authentication",
                "authorization",
                "forbidden",
                "unauthorized",
            ]
        ):
            return ErrorSeverity.HIGH

        # Medium severity errors
        elif any(
            keyword in error_str
            for keyword in ["timeout", "unavailable", "connection", "network"]
        ):
            return ErrorSeverity.MEDIUM

        # Low severity errors
        else:
            return ErrorSeverity.LOW

    def get_recovery_strategy(self, category: ErrorCategory) -> ErrorRecoveryStrategy:
        """Get recovery strategy for error category."""
        strategy_map = {
            ErrorCategory.NETWORK: ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            ErrorCategory.TIMEOUT: ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            ErrorCategory.AUTHENTICATION: ErrorRecoveryStrategy.REAUTHENTICATE,
            ErrorCategory.AUTHORIZATION: ErrorRecoveryStrategy.FAIL_FAST,
            ErrorCategory.PROTOCOL: ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            ErrorCategory.SERVER: ErrorRecoveryStrategy.CIRCUIT_BREAKER,
            ErrorCategory.RESOURCE: ErrorRecoveryStrategy.FALLBACK_MODE,
            ErrorCategory.RATE_LIMIT: ErrorRecoveryStrategy.RATE_LIMIT_WAIT,
            ErrorCategory.UNKNOWN: ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
        }

        return strategy_map.get(category, ErrorRecoveryStrategy.RETRY_WITH_BACKOFF)

    def create_error_context(
        self,
        error: Exception,
        server_name: str,
        operation: str,
        attempt_count: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> MCPErrorContext:
        """Create error context with metadata."""
        category = self.categorize_error(error)
        severity = self.assess_severity(error)

        return MCPErrorContext(
            error=error,
            server_name=server_name,
            operation=operation,
            category=category,
            severity=severity,
            timestamp=datetime.now(),
            attempt_count=attempt_count,
            metadata=metadata or {},
        )

    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff time with exponential backoff and jitter."""
        backoff = min(
            self.base_backoff * (self.backoff_multiplier ** (attempt - 1)),
            self.max_backoff,
        )

        if self.jitter:
            # Add random jitter (±25%)
            jitter_range = backoff * 0.25
            backoff += random.uniform(-jitter_range, jitter_range)

        return max(backoff, 0.1)  # Minimum 100ms

    async def execute_with_retry(
        self,
        operation: Callable,
        server_name: str,
        operation_name: str,
        max_attempts: int | None = None,
        **kwargs,
    ) -> Any:
        """Execute operation with retry logic."""
        max_attempts = max_attempts if max_attempts is not None else self.max_retries
        last_error = None

        # Type assertion to help type checker
        assert max_attempts is not None

        for attempt in range(1, max_attempts + 1):
            try:
                # Check circuit breaker
                if (
                    self.enable_circuit_breaker
                    and not self.circuit_breaker.can_execute()
                ):
                    raise Exception("Circuit breaker is open")

                # Execute operation
                result = await operation(**kwargs)

                # Record success
                if self.enable_circuit_breaker:
                    self.circuit_breaker.record_success()

                return result

            except Exception as error:
                last_error = error

                # Create error context
                context = self.create_error_context(
                    error=error,
                    server_name=server_name,
                    operation=operation_name,
                    attempt_count=attempt,
                )

                # Record error in metrics
                self.metrics.record_error(context)

                # Record circuit breaker failure
                if self.enable_circuit_breaker:
                    self.circuit_breaker.record_failure()

                # Log error
                logger.warning(
                    f"MCP operation failed (attempt {attempt}/{max_attempts}): "
                    f"{operation_name} on {server_name} - {error}"
                )

                # Don't retry on last attempt
                if attempt >= max_attempts:
                    break

                # Calculate backoff and wait
                backoff_time = self.calculate_backoff(attempt)
                logger.debug(f"Retrying in {backoff_time:.2f} seconds...")
                await asyncio.sleep(backoff_time)

        # All attempts failed
        if last_error:
            raise last_error
        else:
            raise Exception(
                f"Operation {operation_name} failed after {max_attempts} attempts"
            )

    async def execute_recovery(
        self,
        strategy: ErrorRecoveryStrategy,
        context: MCPErrorContext,
        recovery_func: Callable,
        max_attempts: int = 3,
    ) -> Any:
        """Execute recovery strategy."""
        if strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF:
            return await self.execute_with_retry(
                operation=recovery_func,
                server_name=context.server_name,
                operation_name=context.operation,
                max_attempts=max_attempts,
            )

        elif strategy == ErrorRecoveryStrategy.RETRY_IMMEDIATE:
            return await recovery_func()

        elif strategy == ErrorRecoveryStrategy.REAUTHENTICATE:
            # This would be handled by the calling code
            logger.info(f"Reauthentication required for {context.server_name}")
            raise context.error

        elif strategy == ErrorRecoveryStrategy.RATE_LIMIT_WAIT:
            # Wait for rate limit reset
            wait_time = self._extract_rate_limit_wait_time(context.error)
            logger.info(f"Rate limited, waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)
            return await recovery_func()

        elif strategy == ErrorRecoveryStrategy.FALLBACK_MODE:
            # Return empty/default result
            logger.info(f"Entering fallback mode for {context.operation}")
            return self._get_fallback_result(context.operation)

        elif strategy == ErrorRecoveryStrategy.FAIL_FAST:
            raise context.error

        else:
            # Default to retry with backoff
            return await self.execute_with_retry(
                operation=recovery_func,
                server_name=context.server_name,
                operation_name=context.operation,
                max_attempts=max_attempts,
            )

    def _extract_rate_limit_wait_time(self, error: Exception) -> float:
        """Extract wait time from rate limit error."""
        # Try to extract from error message or headers
        error_str = str(error)

        # Look for common patterns
        import re

        patterns = [
            r"retry after (\d+)",
            r"wait (\d+) seconds",
            r"rate limit reset in (\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_str, re.IGNORECASE)
            if match:
                return float(match.group(1))

        # Default wait time
        return 60.0

    def _get_fallback_result(self, operation: str) -> Any:
        """Get fallback result for operation."""
        fallback_results = {
            "list_tools": [],
            "list_resources": [],
            "call_tool": [],
            "read_resource": [],
            "ping": None,
        }

        return fallback_results.get(operation)

    def get_error_report(self) -> dict[str, Any]:
        """Get comprehensive error report."""
        return {
            "total_errors": self.metrics.total_errors,
            "errors_by_category": {
                category.value: count
                for category, count in self.metrics.errors_by_category.items()
            },
            "errors_by_server": dict(self.metrics.errors_by_server),
            "errors_by_severity": {
                severity.value: count
                for severity, count in self.metrics.errors_by_severity.items()
            },
            "error_rate_per_minute": self.metrics.get_error_rate(),
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failure_count": self.circuit_breaker.failure_count,
            "recent_errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "server": error.server_name,
                    "operation": error.operation,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "message": str(error.error),
                }
                for error in list(self.metrics.recent_errors)[-10:]  # Last 10 errors
            ],
            "configuration": {
                "max_retries": self.max_retries,
                "base_backoff": self.base_backoff,
                "max_backoff": self.max_backoff,
                "circuit_breaker_enabled": self.enable_circuit_breaker,
                "fallback_enabled": self.enable_fallback,
            },
        }

    def reset_metrics(self) -> None:
        """Reset error metrics."""
        self.metrics = MCPErrorMetrics()
        logger.info("Error metrics reset")

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker state."""
        self.circuit_breaker.state = CircuitBreakerState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.half_open_calls = 0
        logger.info("Circuit breaker reset")

    def is_healthy(self) -> bool:
        """Check if error handler is in healthy state."""
        # Consider healthy if:
        # - Circuit breaker is not open
        # - Error rate is below threshold
        # - No critical errors in recent window

        if self.circuit_breaker.state == CircuitBreakerState.OPEN:
            return False

        # Check error rate (threshold: 10 errors per minute)
        if self.metrics.get_error_rate() > 10:
            return False

        # Check for recent critical errors
        recent_errors = self.metrics.get_errors_in_window(timedelta(minutes=5))
        critical_errors = [
            error for error in recent_errors if error.severity == ErrorSeverity.CRITICAL
        ]

        if len(critical_errors) > 0:
            return False

        return True
