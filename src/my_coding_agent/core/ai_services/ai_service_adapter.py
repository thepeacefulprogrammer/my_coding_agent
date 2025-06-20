"""
AI Service Adapter - Core interface for AI service integrations.

This module provides the abstract base class and data structures for
integrating with various AI services (Azure OpenAI, OpenAI, etc.).
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

# Import circular reference will be handled by having logging_utils import these classes
logger = logging.getLogger(__name__)

# Will import logging utilities after the class definitions to avoid circular imports


# Data Structures


@dataclass
class AIServiceConfig:
    """Configuration for AI service providers."""

    provider: str
    endpoint: str
    api_key: str
    deployment_name: str
    api_version: str = "2024-02-15-preview"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: float = 30.0
    max_retries: int = 3

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.provider or not self.provider.strip():
            raise ValueError("provider is required")
        if not self.endpoint or not self.endpoint.strip():
            raise ValueError("endpoint is required")
        if not self.api_key or not self.api_key.strip():
            raise ValueError("api_key is required")


@dataclass
class AIResponse:
    """Response from an AI service query."""

    content: str
    success: bool
    error: str | None = None
    error_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    response_time: float | None = None
    retry_count: int = 0


@dataclass
class AIStreamingResponse:
    """Streaming response chunk from an AI service."""

    content: str
    is_complete: bool
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


# Exception Classes


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code


class AIServiceConnectionError(AIServiceError):
    """Exception for AI service connection errors."""

    def __init__(
        self, message: str, error_code: str | None = None, endpoint: str | None = None
    ) -> None:
        super().__init__(message, error_code)
        self.endpoint = endpoint


class AIServiceTimeoutError(AIServiceError):
    """Exception for AI service timeout errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        timeout_duration: float | None = None,
    ) -> None:
        super().__init__(message, error_code)
        self.timeout_duration = timeout_duration


class AIServiceRateLimitError(AIServiceError):
    """Exception for AI service rate limit errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, error_code)
        self.retry_after = retry_after


# Abstract Base Class


class AIServiceAdapter(ABC):
    """Abstract base class for AI service adapters."""

    def __init__(self, config: AIServiceConfig) -> None:
        """Initialize the AI service adapter with configuration."""
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Enhanced logging capabilities - import here to avoid circular dependency
        try:
            from .logging_utils import AIServiceLogger, LogContext
            self._ai_logger = AIServiceLogger(f"{__name__}.{self.__class__.__name__}")
            self._log_context = LogContext(
                operation="adapter_lifecycle",
                provider=self.provider,
                endpoint=self.endpoint,
                deployment_name=self.deployment_name
            )
        except ImportError:
            # Fallback to basic logging if enhanced logging is not available
            self._ai_logger = None
            self._log_context = None

        self._connection_state = "disconnected"
        self._connection_attempts = 0
        self._last_connection_time: float | None = None

        # Log adapter initialization
        if self._ai_logger:
            self._ai_logger.info("AI service adapter initialized", context=self._log_context)
        else:
            self._logger.info(f"AI service adapter initialized for {self.provider}")

    @property
    def provider(self) -> str:
        """Get the AI service provider name."""
        return self.config.provider

    @property
    def endpoint(self) -> str:
        """Get the AI service endpoint URL."""
        return self.config.endpoint

    @property
    def deployment_name(self) -> str:
        """Get the deployment/model name."""
        return self.config.deployment_name

    @property
    def max_tokens(self) -> int:
        """Get the maximum tokens setting."""
        return self.config.max_tokens

    @property
    def temperature(self) -> float:
        """Get the temperature setting."""
        return self.config.temperature

    @property
    def timeout(self) -> float:
        """Get the timeout setting."""
        return self.config.timeout

    @property
    def max_retries(self) -> int:
        """Get the maximum retries setting."""
        return self.config.max_retries

    @property
    def connection_state(self) -> str:
        """Get the current connection state."""
        return self._connection_state

    @property
    def connection_attempts(self) -> int:
        """Get the number of connection attempts made."""
        return self._connection_attempts

    @property
    def last_connection_time(self) -> float | None:
        """Get the timestamp of the last successful connection."""
        return self._last_connection_time

    async def connect_with_retry(self) -> bool:
        """
        Connect to the AI service with retry logic and timeout handling.

        This method implements exponential backoff retry logic with configurable
        timeout and maximum retry attempts.

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            AIServiceConnectionError: If connection fails after all retries.
            AIServiceTimeoutError: If connection attempts timeout.
        """
        # Enhanced logging setup
        connection_context = None
        if self._ai_logger and self._log_context:
            try:
                from .logging_utils import LogContext
                connection_context = LogContext(
                    operation="connect_with_retry",
                    provider=self._log_context.provider,
                    endpoint=self._log_context.endpoint,
                    deployment_name=self._log_context.deployment_name,
                    correlation_id=f"conn_{time.time()}"
                )
            except ImportError:
                connection_context = None

        start_time = time.time()
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                self._connection_attempts += 1

                # Enhanced logging for connection attempt
                if self._ai_logger and connection_context:
                    self._ai_logger.log_connection_attempt(
                        connection_context,
                        attempt + 1,
                        self.max_retries + 1
                    )
                else:
                    self._logger.debug(f"Connection attempt {attempt + 1}/{self.max_retries + 1}")

                # Attempt connection with timeout
                await self._attempt_connection()

                # Mark connection as successful
                self._connection_state = "connected"
                self._last_connection_time = time.time()

                # Enhanced logging for connection success
                duration_ms = (time.time() - start_time) * 1000
                if self._ai_logger and connection_context:
                    self._ai_logger.log_connection_success(
                        connection_context,
                        duration_ms,
                        attempt + 1
                    )
                else:
                    self._logger.info(f"Successfully connected to {self.endpoint}")

                return True

            except AIServiceTimeoutError as error:
                last_error = error

                # Enhanced logging for timeout
                if self._ai_logger and connection_context:
                    self._ai_logger.warning(
                        f"Connection attempt {attempt + 1} timed out",
                        context=connection_context,
                        exception=error,
                        extra_data={
                            "attempt": attempt + 1,
                            "timeout_duration": error.timeout_duration
                        }
                    )
                else:
                    self._logger.warning(f"Connection attempt {attempt + 1} timed out: {error}")

                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)

                    if self._ai_logger and connection_context:
                        self._ai_logger.info(
                            f"Retrying connection in {delay:.1f} seconds",
                            context=connection_context,
                            extra_data={"retry_delay": delay, "attempt": attempt + 1}
                        )
                    else:
                        self._logger.info(f"Retrying connection in {delay:.1f} seconds...")

                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final failure logging
                    if self._ai_logger and connection_context:
                        self._ai_logger.log_connection_failure(
                            connection_context,
                            error,
                            self.max_retries + 1
                        )
                    else:
                        self._logger.error(f"Connection failed after {self.max_retries + 1} timeout attempts")

                    raise error

            except AIServiceConnectionError as error:
                last_error = error

                # Enhanced logging for connection error
                if self._ai_logger and connection_context:
                    self._ai_logger.warning(
                        f"Connection attempt {attempt + 1} failed",
                        context=connection_context,
                        exception=error,
                        extra_data={"attempt": attempt + 1, "endpoint": error.endpoint}
                    )
                else:
                    self._logger.warning(f"Connection attempt {attempt + 1} failed: {error}")

                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)

                    if self._ai_logger and connection_context:
                        self._ai_logger.info(
                            f"Retrying connection in {delay:.1f} seconds",
                            context=connection_context,
                            extra_data={"retry_delay": delay, "attempt": attempt + 1}
                        )
                    else:
                        self._logger.info(f"Retrying connection in {delay:.1f} seconds...")

                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final failure logging
                    if self._ai_logger and connection_context:
                        self._ai_logger.log_connection_failure(
                            connection_context,
                            error,
                            self.max_retries + 1
                        )
                    else:
                        self._logger.error(f"Connection failed after {self.max_retries + 1} attempts")

                    raise error

            except Exception as error:
                # Wrap unexpected errors in AIServiceConnectionError
                connection_error = AIServiceConnectionError(
                    f"Unexpected connection error: {str(error)}",
                    endpoint=self.endpoint
                )
                last_error = connection_error

                # Enhanced logging for unexpected error
                if self._ai_logger and connection_context:
                    self._ai_logger.warning(
                        f"Connection attempt {attempt + 1} failed with unexpected error",
                        context=connection_context,
                        exception=error,
                        extra_data={
                            "attempt": attempt + 1,
                            "original_error_type": type(error).__name__
                        }
                    )
                else:
                    self._logger.warning(f"Connection attempt {attempt + 1} failed with unexpected error: {error}")

                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)

                    if self._ai_logger and connection_context:
                        self._ai_logger.info(
                            f"Retrying connection in {delay:.1f} seconds",
                            context=connection_context,
                            extra_data={"retry_delay": delay, "attempt": attempt + 1}
                        )
                    else:
                        self._logger.info(f"Retrying connection in {delay:.1f} seconds...")

                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final failure logging
                    if self._ai_logger and connection_context:
                        self._ai_logger.log_connection_failure(
                            connection_context,
                            connection_error,
                            self.max_retries + 1
                        )
                    else:
                        self._logger.error(f"Connection failed after {self.max_retries + 1} attempts with unexpected errors")

                    raise connection_error

        # This should not be reached, but just in case
        if last_error:
            raise last_error
        else:
            raise AIServiceConnectionError(
                "Connection failed for unknown reason",
                endpoint=self.endpoint
            )

    async def _attempt_connection(self) -> None:
        """
        Attempt a single connection to the AI service with timeout.

        This is an abstract method that concrete implementations must override
        to provide specific connection logic for their AI service.

        Raises:
            AIServiceTimeoutError: If connection times out.
            AIServiceConnectionError: If connection fails.
        """
        try:
            await asyncio.wait_for(
                self._perform_connection(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            raise AIServiceTimeoutError(
                f"Connection timeout after {self.timeout}s",
                timeout_duration=self.timeout
            )
        except Exception as error:
            raise AIServiceConnectionError(
                f"Connection failed: {str(error)}",
                endpoint=self.endpoint
            )

    @abstractmethod
    async def _perform_connection(self) -> None:
        """
        Perform the actual connection to the AI service.

        Concrete implementations must override this method to provide
        service-specific connection logic (e.g., authentication, handshake).

        Raises:
            Exception: Any connection-related errors.
        """
        pass

    async def check_connection(self) -> bool:
        """
        Check if the connection to the AI service is still alive.

        Performs a lightweight health check to verify the connection
        is still valid and responsive.

        Returns:
            bool: True if connection is healthy, False otherwise.
        """
        if self._connection_state != "connected":
            if self._ai_logger and self._log_context:
                self._ai_logger.debug(
                    "Connection check skipped - not connected",
                    context=self._log_context,
                    extra_data={"connection_state": self._connection_state}
                )
            return False

        # Enhanced logging setup for health check
        health_context = None
        if self._ai_logger and self._log_context:
            try:
                from .logging_utils import LogContext
                health_context = LogContext(
                    operation="health_check",
                    provider=self._log_context.provider,
                    endpoint=self._log_context.endpoint,
                    deployment_name=self._log_context.deployment_name,
                    correlation_id=f"health_{time.time()}"
                )
            except ImportError:
                health_context = None

        start_time = time.time()

        try:
            # Use a shorter timeout for health checks
            health_timeout = min(self.timeout / 2, 10.0)

            if health_context and self._ai_logger:
                self._ai_logger.debug(
                    f"Starting health check with {health_timeout}s timeout",
                    context=health_context,
                    extra_data={"timeout": health_timeout}
                )

            await asyncio.wait_for(
                self._perform_health_check(),
                timeout=health_timeout
            )

            # Health check successful
            duration_ms = (time.time() - start_time) * 1000
            if health_context and self._ai_logger:
                self._ai_logger.log_health_check(
                    health_context,
                    success=True,
                    duration_ms=duration_ms
                )
            else:
                self._logger.debug(f"Health check passed in {duration_ms:.1f}ms")

            return True

        except (asyncio.TimeoutError, Exception) as error:
            duration_ms = (time.time() - start_time) * 1000
            self._connection_state = "disconnected"

            if health_context and self._ai_logger:
                self._ai_logger.log_health_check(
                    health_context,
                    success=False,
                    duration_ms=duration_ms,
                    error=error
                )
            else:
                self._logger.warning(f"Connection health check failed: {error}")

            return False

    @abstractmethod
    async def _perform_health_check(self) -> None:
        """
        Perform a health check on the AI service connection.

        Concrete implementations must override this method to provide
        service-specific health check logic.

        Raises:
            Exception: Any health check related errors.
        """
        pass

    async def reconnect_if_needed(self) -> bool:
        """
        Reconnect to the AI service if the connection is lost.

        Checks the current connection status and attempts to reconnect
        if the connection is not healthy.

        Returns:
            bool: True if connection is available (existing or new), False otherwise.

        Raises:
            AIServiceConnectionError: If reconnection fails.
            AIServiceTimeoutError: If reconnection times out.
        """
        # Check if current connection is still healthy
        if await self.check_connection():
            return True

        # Connection is lost, attempt to reconnect
        self._logger.info("Connection lost, attempting to reconnect...")
        return await self.connect_with_retry()

    async def close_connection(self) -> None:
        """
        Close the connection to the AI service.

        Performs cleanup of connection resources and marks the
        connection as disconnected.
        """
        try:
            await self._perform_connection_cleanup()
            self._logger.info("Connection closed successfully")
        except Exception as error:
            self._logger.warning(f"Error during connection cleanup: {error}")
        finally:
            self._connection_state = "disconnected"

    async def _perform_connection_cleanup(self) -> None:
        """
        Perform service-specific connection cleanup.

        Concrete implementations can override this method to provide
        custom cleanup logic. Default implementation does nothing.
        """
        pass

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt using exponential backoff.

        Args:
            attempt: The current attempt number (0-based).

        Returns:
            float: Delay in seconds before next retry.
        """
        base_delay = 1.0
        max_delay = 30.0
        backoff_multiplier = 2.0

        delay = base_delay * (backoff_multiplier ** attempt)
        return min(delay, max_delay)

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the AI service connection.

        Returns:
            bool: True if initialization successful, False otherwise.

        Raises:
            AIServiceConnectionError: If connection fails.
            AIServiceError: For other initialization errors.
        """
        pass

    @abstractmethod
    async def send_query(self, query: str, **kwargs: Any) -> AIResponse:  # noqa: ANN401
        """
        Send a query to the AI service.

        Args:
            query: The query text to send.
            **kwargs: Additional parameters for the query.

        Returns:
            AIResponse: The response from the AI service.

        Raises:
            AIServiceError: For general service errors.
            AIServiceTimeoutError: If the request times out.
            AIServiceRateLimitError: If rate limit is exceeded.
            AIServiceConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    def send_streaming_query(
        self,
        query: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> AsyncIterator[AIStreamingResponse]:
        """
        Send a streaming query to the AI service.

        Args:
            query: The query text to send.
            **kwargs: Additional parameters for the query.

        Yields:
            AIStreamingResponse: Streaming response chunks.

        Raises:
            AIServiceError: For general service errors.
            AIServiceTimeoutError: If the request times out.
            AIServiceRateLimitError: If rate limit is exceeded.
            AIServiceConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    async def get_health_status(self) -> dict[str, Any]:
        """
        Get the health status of the AI service.

        Returns:
            Dict[str, Any]: Health status information.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources and connections.

        This method should be called when the adapter is no longer needed.
        """
        pass
