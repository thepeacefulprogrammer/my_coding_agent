"""
Logging utilities for AI service interactions.

This module provides comprehensive logging and debugging capabilities for
AI service operations including structured logging, performance metrics,
and sensitive data sanitization.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from functools import wraps
from typing import Any

from .ai_service_adapter import AIResponse, AIServiceConfig, AIStreamingResponse


@dataclass
class LogContext:
    """Context information for structured logging."""

    operation: str
    provider: str | None = None
    endpoint: str | None = None
    deployment_name: str | None = None
    correlation_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for AI service operations."""

    operation: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    success: bool = False
    retry_count: int = 0
    error_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error_type: str | None = None) -> None:
        """Mark the operation as finished and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error_type = error_type


class SensitiveDataSanitizer:
    """Sanitizes sensitive data from logs."""

    def __init__(self) -> None:
        self.sensitive_keys = {
            "api_key", "api-key", "apikey", "authorization", "auth", "token",
            "secret", "password", "passwd", "pwd", "private_key", "privatekey",
            "access_token", "refresh_token", "bearer", "x-api-key"
        }
        self.sanitized_value = "***REDACTED***"

    def sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize sensitive data from a dictionary."""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                sanitized[key] = self.sanitized_value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def sanitize_config(self, config: AIServiceConfig) -> dict[str, Any]:
        """Sanitize an AI service configuration for logging."""
        config_dict = asdict(config)
        return self.sanitize_dict(config_dict)

    def sanitize_content(self, content: str, max_length: int = 500) -> str:
        """Sanitize and truncate content for logging."""
        if not content:
            return content

        # Truncate if too long
        if len(content) > max_length:
            content = content[:max_length] + "...[TRUNCATED]"

        # Could add more content sanitization here if needed
        return content

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key contains sensitive data."""
        return key.lower() in self.sensitive_keys


class AIServiceLogger:
    """Enhanced logger for AI service operations with structured logging."""

    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.sanitizer = SensitiveDataSanitizer()
        self._metrics: dict[str, PerformanceMetrics] = {}

    def _log_structured(
        self,
        level: int,
        message: str,
        context: LogContext | None = None,
        extra_data: dict[str, Any] | None = None,
        exception: Exception | None = None
    ) -> None:
        """Log a structured message with context and metadata."""
        log_data = {
            "message": message,
            "timestamp": time.time(),
        }

        if context:
            log_data.update({
                "operation": context.operation,
                "provider": context.provider,
                "endpoint": self._sanitize_endpoint(context.endpoint),
                "deployment_name": context.deployment_name,
                "correlation_id": context.correlation_id,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "context_metadata": self.sanitizer.sanitize_dict(context.metadata),
            })

        if extra_data:
            log_data["extra"] = self.sanitizer.sanitize_dict(extra_data)

        if exception:
            log_data.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
            })

        # Create a formatted message for the log record
        formatted_message = f"{message}"
        if context:
            formatted_message += f" [op={context.operation}]"
            if context.correlation_id:
                formatted_message += f" [corr_id={context.correlation_id}]"

        # Use the extra parameter to include structured data
        self.logger.log(level, formatted_message, extra={"structured_data": log_data})

    def debug(
        self,
        message: str,
        context: LogContext | None = None,
        extra_data: dict[str, Any] | None = None
    ) -> None:
        """Log a debug message."""
        self._log_structured(logging.DEBUG, message, context, extra_data)

    def info(
        self,
        message: str,
        context: LogContext | None = None,
        extra_data: dict[str, Any] | None = None
    ) -> None:
        """Log an info message."""
        self._log_structured(logging.INFO, message, context, extra_data)

    def warning(
        self,
        message: str,
        context: LogContext | None = None,
        extra_data: dict[str, Any] | None = None,
        exception: Exception | None = None
    ) -> None:
        """Log a warning message."""
        self._log_structured(logging.WARNING, message, context, extra_data, exception)

    def error(
        self,
        message: str,
        context: LogContext | None = None,
        extra_data: dict[str, Any] | None = None,
        exception: Exception | None = None
    ) -> None:
        """Log an error message."""
        self._log_structured(logging.ERROR, message, context, extra_data, exception)

    def log_connection_attempt(
        self,
        context: LogContext,
        attempt: int,
        max_attempts: int
    ) -> None:
        """Log a connection attempt."""
        self.debug(
            f"Connection attempt {attempt}/{max_attempts}",
            context=context,
            extra_data={"attempt": attempt, "max_attempts": max_attempts}
        )

    def log_connection_success(
        self,
        context: LogContext,
        duration_ms: float,
        attempts: int
    ) -> None:
        """Log successful connection."""
        self.info(
            f"Successfully connected in {duration_ms:.1f}ms after {attempts} attempts",
            context=context,
            extra_data={
                "duration_ms": duration_ms,
                "total_attempts": attempts,
                "success": True
            }
        )

    def log_connection_failure(
        self,
        context: LogContext,
        error: Exception,
        attempts: int
    ) -> None:
        """Log connection failure."""
        self.error(
            f"Connection failed after {attempts} attempts",
            context=context,
            extra_data={"total_attempts": attempts, "success": False},
            exception=error
        )

    def log_query_request(
        self,
        context: LogContext,
        query: str,
        parameters: dict[str, Any] | None = None
    ) -> None:
        """Log a query request."""
        sanitized_query = self.sanitizer.sanitize_content(query)
        sanitized_params = self.sanitizer.sanitize_dict(parameters or {})

        self.debug(
            "Sending query request",
            context=context,
            extra_data={
                "query_preview": sanitized_query,
                "parameters": sanitized_params,
                "query_length": len(query)
            }
        )

    def log_query_response(
        self,
        context: LogContext,
        response: AIResponse,
        duration_ms: float | None = None
    ) -> None:
        """Log a query response."""
        sanitized_content = self.sanitizer.sanitize_content(response.content)

        log_data = {
            "success": response.success,
            "content_preview": sanitized_content,
            "content_length": len(response.content),
            "retry_count": response.retry_count,
            "response_time": response.response_time,
            "metadata": self.sanitizer.sanitize_dict(response.metadata)
        }

        if duration_ms is not None:
            log_data["total_duration_ms"] = duration_ms

        if response.error:
            log_data.update({
                "error": response.error,
                "error_type": response.error_type
            })

        level = logging.INFO if response.success else logging.WARNING
        message = "Query completed successfully" if response.success else "Query failed"

        self._log_structured(level, message, context, log_data)

    def log_streaming_start(
        self,
        context: LogContext,
        query: str
    ) -> None:
        """Log the start of a streaming query."""
        sanitized_query = self.sanitizer.sanitize_content(query)

        self.debug(
            "Starting streaming query",
            context=context,
            extra_data={
                "query_preview": sanitized_query,
                "query_length": len(query)
            }
        )

    def log_streaming_chunk(
        self,
        context: LogContext,
        chunk: AIStreamingResponse
    ) -> None:
        """Log a streaming response chunk."""
        sanitized_content = self.sanitizer.sanitize_content(chunk.content)

        self.debug(
            f"Received streaming chunk {chunk.chunk_index}",
            context=context,
            extra_data={
                "chunk_index": chunk.chunk_index,
                "is_complete": chunk.is_complete,
                "content_preview": sanitized_content,
                "content_length": len(chunk.content),
                "timestamp": chunk.timestamp,
                "metadata": self.sanitizer.sanitize_dict(chunk.metadata)
            }
        )

    def log_streaming_complete(
        self,
        context: LogContext,
        total_chunks: int,
        duration_ms: float | None = None
    ) -> None:
        """Log completion of streaming query."""
        log_data: dict[str, Any] = {"total_chunks": total_chunks}
        if duration_ms is not None:
            log_data["total_duration_ms"] = duration_ms

        self.info(
            f"Streaming completed with {total_chunks} chunks",
            context=context,
            extra_data=log_data
        )

    def log_health_check(
        self,
        context: LogContext,
        success: bool,
        duration_ms: float | None = None,
        error: Exception | None = None
    ) -> None:
        """Log a health check result."""
        log_data = {
            "success": success,
            "check_type": "health"
        }

        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        level = logging.DEBUG if success else logging.WARNING
        message = "Health check passed" if success else "Health check failed"

        self._log_structured(level, message, context, log_data, error)

    def start_performance_tracking(
        self,
        operation: str,
        context: LogContext | None = None
    ) -> str:
        """Start tracking performance for an operation."""
        metrics_id = f"{operation}_{time.time()}_{id(context) if context else 'none'}"

        self._metrics[metrics_id] = PerformanceMetrics(
            operation=operation,
            start_time=time.time()
        )

        self.debug(
            f"Started performance tracking for {operation}",
            context=context,
            extra_data={"metrics_id": metrics_id}
        )

        return metrics_id

    def finish_performance_tracking(
        self,
        metrics_id: str,
        context: LogContext | None = None,
        success: bool = True,
        error_type: str | None = None,
        retry_count: int = 0
    ) -> PerformanceMetrics | None:
        """Finish tracking performance for an operation."""
        if metrics_id not in self._metrics:
            self.warning(
                f"Performance tracking not found for metrics_id: {metrics_id}",
                context=context
            )
            return None

        metrics = self._metrics.pop(metrics_id)
        metrics.finish(success=success, error_type=error_type)
        metrics.retry_count = retry_count

        self.info(
            f"Performance tracking completed for {metrics.operation}",
            context=context,
            extra_data={
                "duration_ms": metrics.duration_ms,
                "success": metrics.success,
                "retry_count": metrics.retry_count,
                "error_type": metrics.error_type
            }
        )

        return metrics

    @asynccontextmanager
    async def performance_context(
        self,
        operation: str,
        context: LogContext | None = None
    ):
        """Async context manager for performance tracking."""
        metrics_id = self.start_performance_tracking(operation, context)

        try:
            yield metrics_id
            self.finish_performance_tracking(
                metrics_id, context, success=True
            )
        except Exception as error:
            self.finish_performance_tracking(
                metrics_id,
                context,
                success=False,
                error_type=type(error).__name__
            )
            raise

    def _sanitize_endpoint(self, endpoint: str | None) -> str | None:
        """Sanitize endpoint URL for logging."""
        if not endpoint:
            return endpoint

        # Remove query parameters and fragments that might contain sensitive data
        if "?" in endpoint:
            endpoint = endpoint.split("?")[0]
        if "#" in endpoint:
            endpoint = endpoint.split("#")[0]

        return endpoint


def logged_operation(operation_name: str):
    """Decorator for automatically logging AI service operations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if not hasattr(self, '_ai_logger'):
                return await func(self, *args, **kwargs)

            logger: AIServiceLogger = self._ai_logger

            # Safely get object properties, handling Mock objects
            provider = None
            endpoint = None
            deployment_name = None

            try:
                if hasattr(self, 'provider') and not callable(getattr(self, 'provider', None)):
                    provider = getattr(self, 'provider', None)
                if hasattr(self, 'endpoint') and not callable(getattr(self, 'endpoint', None)):
                    endpoint = getattr(self, 'endpoint', None)
                if hasattr(self, 'deployment_name') and not callable(getattr(self, 'deployment_name', None)):
                    deployment_name = getattr(self, 'deployment_name', None)
            except (TypeError, AttributeError):
                # Handle cases where self is a Mock or has unusual attributes
                pass

            context = LogContext(
                operation=operation_name,
                provider=provider,
                endpoint=endpoint,
                deployment_name=deployment_name
            )

            async with logger.performance_context(operation_name, context):
                logger.debug(f"Starting {operation_name}", context=context)
                try:
                    result = await func(self, *args, **kwargs)
                    logger.debug(f"Completed {operation_name}", context=context)
                    return result
                except Exception as error:
                    logger.error(
                        f"Failed {operation_name}",
                        context=context,
                        exception=error
                    )
                    raise

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            if not hasattr(self, '_ai_logger'):
                return func(self, *args, **kwargs)

            logger: AIServiceLogger = self._ai_logger

            # Safely get object properties, handling Mock objects
            provider = None
            endpoint = None
            deployment_name = None

            try:
                if hasattr(self, 'provider') and not callable(getattr(self, 'provider', None)):
                    provider = getattr(self, 'provider', None)
                if hasattr(self, 'endpoint') and not callable(getattr(self, 'endpoint', None)):
                    endpoint = getattr(self, 'endpoint', None)
                if hasattr(self, 'deployment_name') and not callable(getattr(self, 'deployment_name', None)):
                    deployment_name = getattr(self, 'deployment_name', None)
            except (TypeError, AttributeError):
                # Handle cases where self is a Mock or has unusual attributes
                pass

            context = LogContext(
                operation=operation_name,
                provider=provider,
                endpoint=endpoint,
                deployment_name=deployment_name
            )

            metrics_id = logger.start_performance_tracking(operation_name, context)
            logger.debug(f"Starting {operation_name}", context=context)

            try:
                result = func(self, *args, **kwargs)
                logger.finish_performance_tracking(metrics_id, context, success=True)
                logger.debug(f"Completed {operation_name}", context=context)
                return result
            except Exception as error:
                logger.finish_performance_tracking(
                    metrics_id,
                    context,
                    success=False,
                    error_type=type(error).__name__
                )
                logger.error(
                    f"Failed {operation_name}",
                    context=context,
                    exception=error
                )
                raise

        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
