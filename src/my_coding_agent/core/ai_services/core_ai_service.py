"""Core AI Service for Azure OpenAI communication.

This module provides the essential AI communication functionality
without the additional complexities of MCP, file systems, or other integrations.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

logger = logging.getLogger(__name__)


class AIResponse(BaseModel):
    """Response from the AI Service."""

    content: str = Field(description="The AI response content")
    success: bool = Field(description="Whether the request was successful")
    error: str | None = Field(
        default=None, description="Error message if request failed"
    )
    error_type: str | None = Field(
        default=None, description="Type of error that occurred"
    )
    tokens_used: int = Field(
        default=0, description="Number of tokens used in the response"
    )
    retry_count: int = Field(default=0, description="Number of retries attempted")
    stream_id: str | None = Field(
        default=None, description="Stream ID if this was a streaming response"
    )


class CoreAIService:
    """Core AI service for Azure OpenAI communication."""

    def __init__(self, config) -> None:
        """Initialize the core AI service.

        Args:
            config: AIAgentConfig instance with Azure OpenAI settings
        """
        self.config = config
        self._model = None
        self._agent = None
        self._setup_logging()
        self._create_model()
        self._create_agent()

    def _setup_logging(self) -> None:
        """Setup logging for the AI service."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _create_model(self) -> None:
        """Create and configure the OpenAI model."""
        try:
            self._model = OpenAIModel(
                model_name=self.config.deployment_name,
                base_url=f"{self.config.azure_endpoint.rstrip('/')}/openai/deployments/{self.config.deployment_name}",
                api_key=self.config.azure_api_key,
                openai_client_kwargs={
                    "api_version": self.config.api_version,
                    "timeout": self.config.request_timeout,
                    "max_retries": self.config.max_retries,
                },
            )
            self.logger.info("OpenAI model created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create OpenAI model: {e}")
            raise

    def _create_agent(self) -> None:
        """Create and configure the AI agent."""
        try:
            system_prompt = (
                "You are an AI coding assistant, powered by Claude Sonnet 4. "
                "You operate in Cursor and help with software development tasks. "
                "You are knowledgeable, helpful, and focused on providing accurate solutions."
            )

            self._agent = Agent(
                model=self._model,
                system_prompt=system_prompt,
            )
            self.logger.info("AI agent created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create AI agent: {e}")
            raise

    async def send_message(self, message: str) -> AIResponse:
        """Send a message to the AI and get a response."""
        # Validate input
        if not message or not message.strip():
            return AIResponse(
                success=False,
                content="",
                error="Message cannot be empty",
                tokens_used=0,
            )

        try:
            self.logger.info(f"Sending message to AI (length: {len(message)})")

            # Run the agent with retries
            response = await self._run_with_retries(message)

            self.logger.info("AI response received successfully")
            return AIResponse(
                success=True,
                content=response.data,
                tokens_used=getattr(response, "usage", {}).get("total_tokens", 0),
            )

        except Exception as e:
            error_type, error_msg = self._categorize_error(e)
            self.logger.error(f"Error sending message to AI: {error_msg}")
            return AIResponse(
                success=False,
                content="",
                error=error_msg,
                error_type=error_type,
                tokens_used=0,
            )

    async def _run_with_retries(self, message: str, max_retries: int = None):
        """Run the agent with retry logic for transient errors."""
        if max_retries is None:
            max_retries = self.config.max_retries

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = await self._agent.run(message)
                return response

            except Exception as e:
                last_exception = e
                error_type, _ = self._categorize_error(e)

                # Don't retry for non-retryable errors
                if error_type in ["AuthenticationError", "ValidationError"]:
                    raise e

                if attempt < max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    self.logger.warning(
                        f"Retry {attempt + 1}/{max_retries} in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)

        raise last_exception

    def _categorize_error(self, exception: Exception) -> tuple[str, str]:
        """Categorize an exception and return error type and message."""
        exception_name = type(exception).__name__
        error_message = str(exception)

        # Authentication errors
        if "401" in error_message or "unauthorized" in error_message.lower():
            return (
                "AuthenticationError",
                "Authentication failed. Please check your API key.",
            )

        # Rate limiting
        if "429" in error_message or "rate limit" in error_message.lower():
            return "RateLimitError", "Rate limit exceeded. Please try again later."

        # Timeout errors
        if (
            isinstance(exception, asyncio.TimeoutError)
            or "timeout" in error_message.lower()
        ):
            return "TimeoutError", "Request timed out. Please try again."

        # Connection errors
        if "connection" in error_message.lower():
            return "ConnectionError", "Network connection error."

        # Default to generic error
        return exception_name, f"{exception_name}: {error_message}"

    @property
    def is_configured(self) -> bool:
        """Check if the AI service is properly configured."""
        return self._model is not None and self._agent is not None

    @property
    def model_info(self) -> str:
        """Get information about the configured model."""
        if self._model:
            return f"Azure OpenAI - {self.config.deployment_name}"
        return "Not configured"

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the AI service."""
        return {
            "service": "CoreAIService",
            "configured": self.is_configured,
            "model": self.model_info,
            "endpoint": self.config.azure_endpoint,
            "deployment": self.config.deployment_name,
            "api_version": self.config.api_version,
        }
