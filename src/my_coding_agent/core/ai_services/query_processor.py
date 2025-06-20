"""
Query Processor - Enhanced query handling with retry logic and validation.

This module provides intelligent query processing with retry mechanisms,
response validation, and comprehensive error handling for AI service interactions.
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from .ai_service_adapter import (
    AIResponse,
    AIServiceAdapter,
    AIServiceConnectionError,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIStreamingResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class QueryRequest:
    """Request structure for AI queries."""

    query: str
    context: dict[str, Any] = field(default_factory=dict)
    max_tokens: int | None = None
    temperature: float | None = None
    timeout: float | None = None

    def __post_init__(self) -> None:
        """Validate query request after initialization."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")


@dataclass
class QueryContext:
    """Context information for queries."""

    conversation_id: str | None = None
    user_id: str | None = None
    timestamp: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    retry_on_errors: list[type[Exception]] = field(
        default_factory=lambda: [
            AIServiceTimeoutError,
            AIServiceRateLimitError,
            AIServiceConnectionError,
        ]
    )

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt using exponential backoff."""
        delay = self.base_delay * (self.backoff_multiplier**attempt)
        return min(delay, self.max_delay)

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error should trigger a retry."""
        if attempt >= self.max_retries:
            return False

        return any(isinstance(error, error_type) for error_type in self.retry_on_errors)


class ResponseValidator:
    """Validates AI service responses."""

    def __init__(
        self,
        allow_empty_content: bool = True,
        max_content_length: int | None = None,
    ) -> None:
        self.allow_empty_content = allow_empty_content
        self.max_content_length = max_content_length

    def validate_response(self, response: AIResponse) -> bool:
        """Validate a standard AI response."""
        if not response.success:
            return False

        if not self.allow_empty_content and not response.content.strip():
            return False

        return not (
            self.max_content_length is not None
            and len(response.content) > self.max_content_length
        )

    def validate_streaming_response(self, response: AIStreamingResponse) -> bool:
        """Validate a streaming AI response."""
        if response.chunk_index < 0:
            return False

        if not self.allow_empty_content and not response.content.strip():
            return False

        return not (
            self.max_content_length is not None
            and len(response.content) > self.max_content_length
        )


class QueryProcessor:
    """Processes AI queries with error handling and retry logic."""

    def __init__(
        self,
        adapter: AIServiceAdapter,
        retry_policy: RetryPolicy | None = None,
        response_validator: ResponseValidator | None = None,
    ) -> None:
        self.adapter = adapter
        self.retry_policy = retry_policy or RetryPolicy()
        self.response_validator = response_validator or ResponseValidator()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Enhanced logging capabilities
        try:
            from .logging_utils import AIServiceLogger, LogContext
            self._ai_logger = AIServiceLogger(f"{__name__}.{self.__class__.__name__}")

            # Safely get adapter properties, handling Mock objects
            provider = None
            endpoint = None
            deployment_name = None

            try:
                if hasattr(adapter, 'provider') and not callable(getattr(adapter, 'provider', None)):
                    provider = getattr(adapter, 'provider', None)
                if hasattr(adapter, 'endpoint') and not callable(getattr(adapter, 'endpoint', None)):
                    endpoint = getattr(adapter, 'endpoint', None)
                if hasattr(adapter, 'deployment_name') and not callable(getattr(adapter, 'deployment_name', None)):
                    deployment_name = getattr(adapter, 'deployment_name', None)
            except (TypeError, AttributeError):
                # Handle cases where adapter is a Mock or has unusual attributes
                pass

            self._base_context = LogContext(
                operation="query_processing",
                provider=provider,
                endpoint=endpoint,
                deployment_name=deployment_name
            )
        except ImportError:
            # Fallback to basic logging if enhanced logging is not available
            self._ai_logger = None
            self._base_context = None

        # Log processor initialization
        if self._ai_logger:
            self._ai_logger.info("Query processor initialized", context=self._base_context)
        else:
            self._logger.info("Query processor initialized")

    async def process_query(self, request: QueryRequest) -> AIResponse:
        """
        Process a query with retry logic and error handling.

        Args:
            request: The query request to process.

        Returns:
            AIResponse: The response from the AI service.

        Raises:
            AIServiceError: If the query fails after all retries.
        """
        # Enhanced logging setup for query
        query_context = None
        if self._ai_logger and self._base_context:
            try:
                from .logging_utils import LogContext
                query_context = LogContext(
                    operation="process_query",
                    provider=self._base_context.provider,
                    endpoint=self._base_context.endpoint,
                    deployment_name=self._base_context.deployment_name,
                    correlation_id=f"query_{time.time()}"
                )
            except ImportError:
                query_context = None

        attempt = 0
        last_error = None
        start_time = time.time()

        # Log the query request
        if query_context and self._ai_logger:
            kwargs = self._prepare_query_kwargs(request)
            self._ai_logger.log_query_request(
                query_context,
                request.query,
                kwargs
            )

        # Track performance
        metrics_id = None
        if self._ai_logger and query_context:
            metrics_id = self._ai_logger.start_performance_tracking(
                "query_processing",
                query_context
            )

        while attempt <= self.retry_policy.max_retries:
            try:
                # Enhanced logging for attempt
                if self._ai_logger and query_context:
                    self._ai_logger.debug(
                        f"Processing query attempt {attempt + 1}/{self.retry_policy.max_retries + 1}",
                        context=query_context,
                        extra_data={"attempt": attempt + 1, "max_attempts": self.retry_policy.max_retries + 1}
                    )
                else:
                    self._logger.debug(f"Processing query attempt {attempt + 1}")

                # Prepare query parameters
                kwargs = self._prepare_query_kwargs(request)

                # Send query to adapter
                response = await self.adapter.send_query(request.query, **kwargs)

                # Validate response
                if not self.response_validator.validate_response(response):
                    # Create error response for validation failure
                    validation_response = AIResponse(
                        content="",
                        success=False,
                        error="Response validation failed",
                        error_type="validation_error",
                        retry_count=attempt,
                    )

                    # Log validation failure
                    if self._ai_logger and query_context:
                        self._ai_logger.log_query_response(
                            query_context,
                            validation_response,
                            (time.time() - start_time) * 1000
                        )
                        if metrics_id:
                            self._ai_logger.finish_performance_tracking(
                                metrics_id,
                                query_context,
                                success=False,
                                error_type="validation_error",
                                retry_count=attempt
                            )

                    return validation_response

                # Add retry count to successful response
                response.retry_count = attempt

                # Log successful response
                duration_ms = (time.time() - start_time) * 1000
                if self._ai_logger and query_context:
                    self._ai_logger.log_query_response(
                        query_context,
                        response,
                        duration_ms
                    )
                    if metrics_id:
                        self._ai_logger.finish_performance_tracking(
                            metrics_id,
                            query_context,
                            success=True,
                            retry_count=attempt
                        )
                else:
                    self._logger.info(f"Query completed successfully in {duration_ms:.1f}ms")

                return response

            except Exception as error:
                last_error = error

                # Enhanced error logging
                if self._ai_logger and query_context:
                    self._ai_logger.warning(
                        f"Query attempt {attempt + 1} failed",
                        context=query_context,
                        exception=error,
                        extra_data={
                            "attempt": attempt + 1,
                            "error_type": type(error).__name__,
                            "should_retry": self.retry_policy.should_retry(error, attempt)
                        }
                    )
                else:
                    self._logger.warning(f"Query attempt {attempt + 1} failed: {error}")

                # Check if we should retry
                if not self.retry_policy.should_retry(error, attempt):
                    # Final failure logging
                    if self._ai_logger and query_context:
                        self._ai_logger.error(
                            f"Query failed after {attempt + 1} attempts",
                            context=query_context,
                            exception=error,
                            extra_data={"total_attempts": attempt + 1}
                        )
                        if metrics_id:
                            self._ai_logger.finish_performance_tracking(
                                metrics_id,
                                query_context,
                                success=False,
                                error_type=type(error).__name__,
                                retry_count=attempt
                            )
                    else:
                        self._logger.error(f"Query failed after {attempt + 1} attempts")

                    raise error

                # Calculate delay and wait before retry
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.calculate_delay(attempt)

                    if self._ai_logger and query_context:
                        self._ai_logger.info(
                            f"Retrying query in {delay:.1f} seconds",
                            context=query_context,
                            extra_data={"retry_delay": delay, "attempt": attempt + 1}
                        )
                    else:
                        self._logger.info(f"Retrying in {delay:.1f} seconds...")

                    await asyncio.sleep(delay)

                attempt += 1

        # This should not be reached, but just in case
        if last_error:
            # Final cleanup
            if metrics_id and self._ai_logger and query_context:
                self._ai_logger.finish_performance_tracking(
                    metrics_id,
                    query_context,
                    success=False,
                    error_type=type(last_error).__name__,
                    retry_count=attempt
                )
            raise last_error
        else:
            unknown_error = AIServiceError("Query processing failed for unknown reason")
            if metrics_id and self._ai_logger and query_context:
                self._ai_logger.finish_performance_tracking(
                    metrics_id,
                    query_context,
                    success=False,
                    error_type="unknown_error",
                    retry_count=attempt
                )
            raise unknown_error

    async def process_streaming_query(
        self, request: QueryRequest
    ) -> AsyncIterator[AIStreamingResponse]:
        """
        Process a streaming query.

        Args:
            request: The query request to process.

        Yields:
            AIStreamingResponse: Streaming response chunks.

        Raises:
            AIServiceError: If the streaming query fails.
        """
        # Enhanced logging setup for streaming query
        streaming_context = None
        if self._ai_logger and self._base_context:
            try:
                from .logging_utils import LogContext
                streaming_context = LogContext(
                    operation="process_streaming_query",
                    provider=self._base_context.provider,
                    endpoint=self._base_context.endpoint,
                    deployment_name=self._base_context.deployment_name,
                    correlation_id=f"streaming_{time.time()}"
                )
            except ImportError:
                streaming_context = None

        start_time = time.time()
        chunk_count = 0

        # Log streaming start
        if streaming_context and self._ai_logger:
            self._ai_logger.log_streaming_start(streaming_context, request.query)
        else:
            self._logger.debug("Processing streaming query")

        # Track performance
        metrics_id = None
        if self._ai_logger and streaming_context:
            metrics_id = self._ai_logger.start_performance_tracking(
                "streaming_query_processing",
                streaming_context
            )

        try:
            # Prepare query parameters
            kwargs = self._prepare_query_kwargs(request)

            # Send streaming query to adapter
            async for chunk in self.adapter.send_streaming_query(
                request.query, **kwargs
            ):
                chunk_count += 1

                # Validate streaming response
                if self.response_validator.validate_streaming_response(chunk):
                    # Log valid chunk
                    if streaming_context and self._ai_logger:
                        self._ai_logger.log_streaming_chunk(streaming_context, chunk)

                    yield chunk
                else:
                    # Log invalid chunk
                    if streaming_context and self._ai_logger:
                        self._ai_logger.warning(
                            f"Invalid streaming response chunk {chunk.chunk_index} received",
                            context=streaming_context,
                            extra_data={
                                "chunk_index": chunk.chunk_index,
                                "content_length": len(chunk.content),
                                "is_complete": chunk.is_complete
                            }
                        )
                    else:
                        self._logger.warning("Invalid streaming response chunk received")
                    # Continue processing other chunks

            # Log streaming completion
            duration_ms = (time.time() - start_time) * 1000
            if streaming_context and self._ai_logger:
                self._ai_logger.log_streaming_complete(
                    streaming_context,
                    chunk_count,
                    duration_ms
                )
                if metrics_id:
                    self._ai_logger.finish_performance_tracking(
                        metrics_id,
                        streaming_context,
                        success=True
                    )
            else:
                self._logger.info(f"Streaming completed with {chunk_count} chunks in {duration_ms:.1f}ms")

        except Exception as error:
            # Log streaming error
            if streaming_context and self._ai_logger:
                self._ai_logger.error(
                    "Streaming query failed",
                    context=streaming_context,
                    exception=error,
                    extra_data={
                        "chunks_processed": chunk_count,
                        "duration_ms": (time.time() - start_time) * 1000
                    }
                )
                if metrics_id:
                    self._ai_logger.finish_performance_tracking(
                        metrics_id,
                        streaming_context,
                        success=False,
                        error_type=type(error).__name__
                    )
            else:
                self._logger.error(f"Streaming query failed: {error}")

            raise

    def _prepare_query_kwargs(self, request: QueryRequest) -> dict[str, Any]:
        """Prepare keyword arguments for the adapter query."""
        kwargs = {}

        # Add context if provided
        if request.context:
            kwargs["context"] = request.context

        # Add optional parameters if provided
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        if request.timeout is not None:
            kwargs["timeout"] = request.timeout

        return kwargs
