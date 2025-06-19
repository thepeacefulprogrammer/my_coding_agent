"""
Query processor for AI service requests.

Handles query processing, error handling, retry mechanisms, and response validation.
"""

import asyncio
import logging
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
        attempt = 0
        last_error = None

        while attempt <= self.retry_policy.max_retries:
            try:
                self._logger.debug(f"Processing query attempt {attempt + 1}")

                # Prepare query parameters
                kwargs = self._prepare_query_kwargs(request)

                # Send query to adapter
                response = await self.adapter.send_query(request.query, **kwargs)

                # Validate response
                if not self.response_validator.validate_response(response):
                    # Create error response for validation failure
                    return AIResponse(
                        content="",
                        success=False,
                        error="Response validation failed",
                        error_type="validation_error",
                        retry_count=attempt,
                    )

                # Add retry count to successful response
                response.retry_count = attempt
                return response

            except Exception as error:
                last_error = error
                self._logger.warning(f"Query attempt {attempt + 1} failed: {error}")

                # Check if we should retry
                if not self.retry_policy.should_retry(error, attempt):
                    self._logger.error(f"Query failed after {attempt + 1} attempts")
                    raise error

                # Calculate delay and wait before retry
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.calculate_delay(attempt)
                    self._logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)

                attempt += 1

        # This should not be reached, but just in case
        if last_error:
            raise last_error
        else:
            raise AIServiceError("Query processing failed for unknown reason")

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
        self._logger.debug("Processing streaming query")

        # Prepare query parameters
        kwargs = self._prepare_query_kwargs(request)

        try:
            # Send streaming query to adapter
            async for chunk in self.adapter.send_streaming_query(
                request.query, **kwargs
            ):
                # Validate streaming response
                if self.response_validator.validate_streaming_response(chunk):
                    yield chunk
                else:
                    self._logger.warning("Invalid streaming response chunk received")
                    # Continue processing other chunks

        except Exception as error:
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
