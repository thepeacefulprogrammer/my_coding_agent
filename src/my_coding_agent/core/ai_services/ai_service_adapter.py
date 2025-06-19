"""
AI Service Adapter - Core interface for AI service integrations.

This module provides the abstract base class and data structures for
integrating with various AI services (Azure OpenAI, OpenAI, etc.).
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


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
