"""Error handling service for AI agent operations.

This service provides centralized error handling, categorization, and retry logic
extracted from the ai_agent.py GOD object.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for classification and handling."""

    # File system errors
    FILE_NOT_FOUND = "file_not_found"
    FILE_EXISTS = "file_exists"
    PERMISSION_ERROR = "permission_error"

    # Network and connection errors
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"

    # Resource errors
    MEMORY_ERROR = "memory_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SYSTEM_ERROR = "system_error"

    # HTTP and API errors
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"

    # AI model specific errors
    TOKEN_LIMIT_ERROR = "token_limit_error"
    TOKEN_ERROR = "token_error"

    # Streaming errors
    STREAM_INTERRUPTED = "stream_interrupted"
    STREAM_CORRUPTION = "stream_corruption"
    STREAMING_ERROR = "streaming_error"

    # Validation and input errors
    VALIDATION_ERROR = "validation_error"
    DATA_ERROR = "data_error"

    # System errors
    DEPENDENCY_ERROR = "dependency_error"
    OPERATION_CANCELLED = "operation_cancelled"
    SSL_ERROR = "ssl_error"

    # Unknown errors
    UNKNOWN = "unknown"


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 30.0  # Maximum delay in seconds
    backoff_factor: float = 2.0  # Exponential backoff factor


@dataclass
class ErrorInfo:
    """Information about a categorized error."""

    category: ErrorCategory
    message: str
    original_exception: Exception
    retry_count: int = 0


class RetryableError(Exception):
    """Exception raised when max retries are exceeded for a retryable error."""

    def __init__(
        self, message: str, original_error: Exception, retry_count: int
    ) -> None:
        super().__init__(message)
        self.original_error = original_error
        self.retry_count = retry_count


class ErrorHandlingService:
    """Service for handling errors, categorization, and retry logic."""

    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        """Initialize the error handling service.

        Args:
            retry_policy: Custom retry policy. Uses default if None.
        """
        self._retry_policy = retry_policy or RetryPolicy()

        # Error statistics tracking
        self._error_stats = {
            "total_errors": 0,
            "total_retries": 0,
            "error_categories": defaultdict(int),
            "retryable_errors": 0,
            "non_retryable_errors": 0,
        }

        # Define which error categories are retryable
        self._retryable_categories = {
            ErrorCategory.CONNECTION_ERROR,
            ErrorCategory.TIMEOUT_ERROR,
            ErrorCategory.RATE_LIMIT_ERROR,
            ErrorCategory.SERVER_ERROR,
            ErrorCategory.STREAM_CORRUPTION,
            ErrorCategory.STREAMING_ERROR,
            ErrorCategory.RESOURCE_EXHAUSTION,
            ErrorCategory.SYSTEM_ERROR,
        }

    def categorize_error(self, exception: Exception) -> tuple[ErrorCategory, str]:
        """Categorize an error and return error type and user-friendly message.

        Args:
            exception: The exception to categorize

        Returns:
            Tuple of (error_category, user_friendly_message)
        """
        # File system errors (check these before OSError since they inherit from it)
        if isinstance(exception, FileNotFoundError):
            return ErrorCategory.FILE_NOT_FOUND, "Requested file was not found."

        if isinstance(exception, FileExistsError):
            return ErrorCategory.FILE_EXISTS, "File already exists."

        if isinstance(exception, PermissionError):
            return (
                ErrorCategory.PERMISSION_ERROR,
                "Permission denied. Please check your access rights.",
            )

        # Network and connection errors
        if isinstance(
            exception, ConnectionError | ConnectionRefusedError | ConnectionResetError
        ):
            return (
                ErrorCategory.CONNECTION_ERROR,
                "Network connection failed. Please check your internet connection and try again.",
            )

        # Timeout errors
        if isinstance(exception, asyncio.TimeoutError | TimeoutError):
            return (
                ErrorCategory.TIMEOUT_ERROR,
                "Request timed out. The service may be experiencing high load. Please try again.",
            )

        # Memory and resource errors
        if isinstance(exception, MemoryError):
            return (
                ErrorCategory.MEMORY_ERROR,
                "Insufficient memory available. Try reducing the request size or closing other applications.",
            )

        if isinstance(exception, OSError):
            if "Too many open files" in str(exception):
                return (
                    ErrorCategory.RESOURCE_EXHAUSTION,
                    "System resource limit reached. Please try again in a moment.",
                )
            return (
                ErrorCategory.SYSTEM_ERROR,
                "System error occurred. Please try again.",
            )

        # HTTP and API specific errors
        status_code = getattr(exception, "status_code", None)
        if status_code is None:
            response = getattr(exception, "response", None)
            if response is not None:
                status_code = getattr(response, "status_code", None)

        if status_code:
            if status_code == 401:
                return (
                    ErrorCategory.AUTHENTICATION_ERROR,
                    "Authentication failed. Please check your API credentials.",
                )
            elif status_code == 403:
                return (
                    ErrorCategory.AUTHORIZATION_ERROR,
                    "Access forbidden. You don't have permission for this operation.",
                )
            elif status_code == 429:
                return (
                    ErrorCategory.RATE_LIMIT_ERROR,
                    "Rate limit exceeded. Please wait before making another request.",
                )
            elif status_code >= 500:
                return (
                    ErrorCategory.SERVER_ERROR,
                    "Server error occurred. Please try again later.",
                )
            elif status_code >= 400:
                return (
                    ErrorCategory.CLIENT_ERROR,
                    f"Request error (HTTP {status_code}). Please check your request.",
                )

        # AI model specific errors
        exception_str = str(exception).lower()
        if "token" in exception_str:
            if "limit" in exception_str or "exceeded" in exception_str:
                return (
                    ErrorCategory.TOKEN_LIMIT_ERROR,
                    "Token limit exceeded. Please try with a shorter message.",
                )
            return ErrorCategory.TOKEN_ERROR, "Token-related error occurred."

        # Streaming specific errors
        if "stream" in exception_str:
            if "interrupted" in exception_str or "cancelled" in exception_str:
                return (
                    ErrorCategory.STREAM_INTERRUPTED,
                    "Stream was interrupted. You can try sending the message again.",
                )
            if "corrupted" in exception_str:
                return (
                    ErrorCategory.STREAM_CORRUPTION,
                    "Stream data was corrupted. Retrying automatically.",
                )
            return (
                ErrorCategory.STREAMING_ERROR,
                "Streaming error occurred. Falling back to standard response.",
            )

        # Validation and input errors
        if isinstance(exception, ValueError | TypeError):
            return (
                ErrorCategory.VALIDATION_ERROR,
                "Invalid input provided. Please check your request and try again.",
            )

        # Import and module errors
        if isinstance(exception, ImportError | ModuleNotFoundError):
            return (
                ErrorCategory.DEPENDENCY_ERROR,
                "Required dependency is missing. Please check your installation.",
            )

        # Asyncio specific errors
        if isinstance(exception, asyncio.CancelledError):
            return ErrorCategory.OPERATION_CANCELLED, "Operation was cancelled."

        # JSON and data parsing errors
        if "json" in exception_str or isinstance(exception, KeyError | AttributeError):
            return (
                ErrorCategory.DATA_ERROR,
                "Data parsing error occurred. The response format may be unexpected.",
            )

        # SSL and security errors
        if "ssl" in exception_str or "certificate" in exception_str:
            return (
                ErrorCategory.SSL_ERROR,
                "SSL/TLS error occurred. Please check your connection security settings.",
            )

        # Default fallback for unknown errors
        return ErrorCategory.UNKNOWN, f"An unexpected error occurred: {str(exception)}"

    def is_retryable_error(self, category: ErrorCategory) -> bool:
        """Check if an error category is retryable.

        Args:
            category: The error category to check

        Returns:
            True if the error is retryable, False otherwise
        """
        return category in self._retryable_categories

    def calculate_backoff_time(self, attempt: int) -> float:
        """Calculate backoff time for retry attempts.

        Args:
            attempt: The attempt number (0-based)

        Returns:
            Backoff time in seconds
        """
        delay = self._retry_policy.base_delay * (
            self._retry_policy.backoff_factor**attempt
        )
        return min(delay, self._retry_policy.max_delay)

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with automatic retry on retryable errors.

        Args:
            func: The async function to execute
            *args: Positional arguments for the function
            max_retries: Maximum number of retries (uses policy default if None)
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function execution

        Raises:
            RetryableError: If max retries exceeded for retryable errors
            Exception: The original exception for non-retryable errors
        """
        if max_retries is None:
            max_retries = self._retry_policy.max_retries

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                last_exception = e
                category, message = self.categorize_error(e)

                # Update statistics
                self._error_stats["total_errors"] += 1
                self._error_stats["error_categories"][category.name] += 1

                # Check if error is retryable
                if not self.is_retryable_error(category):
                    self._error_stats["non_retryable_errors"] += 1
                    logger.error(f"Non-retryable error: {message}")
                    raise e

                self._error_stats["retryable_errors"] += 1

                # If we've exhausted retries, raise RetryableError
                if attempt >= max_retries:
                    error_msg = f"Max retries ({max_retries}) exceeded for {category.name}: {message}"
                    logger.error(error_msg)
                    raise RetryableError(error_msg, e, attempt) from e

                # Calculate backoff and retry
                self._error_stats["total_retries"] += 1
                backoff_time = self.calculate_backoff_time(attempt)

                logger.warning(
                    f"Retryable error (attempt {attempt + 1}/{max_retries + 1}): {message}. "
                    f"Retrying in {backoff_time}s..."
                )

                await asyncio.sleep(backoff_time)

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected state in retry logic")

    def safe_execute(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> tuple[Any, ErrorInfo | None]:
        """Execute a function safely, capturing any errors.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Tuple of (result, error_info). If successful, error_info is None.
            If failed, result is None and error_info contains error details.
        """
        try:
            result = func(*args, **kwargs)
            return result, None

        except Exception as e:
            category, message = self.categorize_error(e)
            error_info = ErrorInfo(
                category=category, message=message, original_exception=e
            )

            # Update statistics
            self._error_stats["total_errors"] += 1
            self._error_stats["error_categories"][category.name] += 1

            if self.is_retryable_error(category):
                self._error_stats["retryable_errors"] += 1
            else:
                self._error_stats["non_retryable_errors"] += 1

            return None, error_info

    def get_retry_policy(self) -> RetryPolicy:
        """Get the current retry policy.

        Returns:
            The current retry policy configuration
        """
        return self._retry_policy

    def set_retry_policy(self, policy: RetryPolicy) -> None:
        """Set a new retry policy.

        Args:
            policy: The new retry policy to use
        """
        self._retry_policy = policy

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics.

        Returns:
            Dictionary containing error statistics
        """
        return {
            "total_errors": self._error_stats["total_errors"],
            "total_retries": self._error_stats["total_retries"],
            "error_categories": dict(self._error_stats["error_categories"]),
            "retryable_errors": self._error_stats["retryable_errors"],
            "non_retryable_errors": self._error_stats["non_retryable_errors"],
        }

    def reset_error_statistics(self) -> None:
        """Reset error statistics."""
        self._error_stats = {
            "total_errors": 0,
            "total_retries": 0,
            "error_categories": defaultdict(int),
            "retryable_errors": 0,
            "non_retryable_errors": 0,
        }
