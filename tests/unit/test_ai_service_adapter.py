"""
Unit tests for AIServiceAdapter class interface and basic functionality.

Tests the core AI service adapter interface, basic functionality,
and abstract method contracts.
"""

from typing import Any

import pytest

from src.my_coding_agent.core.ai_services.ai_service_adapter import (
    AIResponse,
    AIServiceAdapter,
    AIServiceConfig,
    AIServiceConnectionError,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIStreamingResponse,
)


class TestAIServiceConfig:
    """Test AI service configuration data structures."""

    def test_ai_service_config_creation(self):
        """Test basic AI service configuration creation."""
        config = AIServiceConfig(
            provider="azure_openai",
            endpoint="https://test.openai.azure.com/",
            api_key="test-key",
            deployment_name="test-deployment",
            api_version="2024-02-15-preview",
            max_tokens=2000,
            temperature=0.7,
            timeout=30.0,
            max_retries=3,
        )

        assert config.provider == "azure_openai"
        assert config.endpoint == "https://test.openai.azure.com/"
        assert config.api_key == "test-key"
        assert config.deployment_name == "test-deployment"
        assert config.api_version == "2024-02-15-preview"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_ai_service_config_defaults(self):
        """Test AI service configuration with default values."""
        config = AIServiceConfig(
            provider="azure_openai",
            endpoint="https://test.openai.azure.com/",
            api_key="test-key",
            deployment_name="test-deployment",
        )

        # Check defaults
        assert config.api_version == "2024-02-15-preview"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_ai_service_config_validation(self):
        """Test AI service configuration validation."""
        # Test missing required fields
        with pytest.raises(ValueError, match="provider is required"):
            AIServiceConfig(
                provider="",
                endpoint="https://test.openai.azure.com/",
                api_key="test-key",
                deployment_name="test-deployment",
            )

        with pytest.raises(ValueError, match="endpoint is required"):
            AIServiceConfig(
                provider="azure_openai",
                endpoint="",
                api_key="test-key",
                deployment_name="test-deployment",
            )

        with pytest.raises(ValueError, match="api_key is required"):
            AIServiceConfig(
                provider="azure_openai",
                endpoint="https://test.openai.azure.com/",
                api_key="",
                deployment_name="test-deployment",
            )


class TestAIResponse:
    """Test AI response data structures."""

    def test_ai_response_creation(self):
        """Test basic AI response creation."""
        response = AIResponse(
            content="Hello, how can I help you?",
            success=True,
            metadata={"model": "gpt-4", "tokens_used": 25},
            response_time=1.23,
        )

        assert response.content == "Hello, how can I help you?"
        assert response.success is True
        assert response.error is None
        assert response.metadata["model"] == "gpt-4"
        assert response.metadata["tokens_used"] == 25
        assert response.response_time == 1.23

    def test_ai_response_with_error(self):
        """Test AI response with error information."""
        response = AIResponse(
            content="",
            success=False,
            error="Rate limit exceeded",
            error_type="rate_limit",
            retry_count=2,
        )

        assert response.content == ""
        assert response.success is False
        assert response.error == "Rate limit exceeded"
        assert response.error_type == "rate_limit"
        assert response.retry_count == 2

    def test_ai_streaming_response(self):
        """Test AI streaming response data structure."""
        response = AIStreamingResponse(
            content="Partial response",
            is_complete=False,
            chunk_index=1,
            metadata={"stream_id": "test-123"},
        )

        assert response.content == "Partial response"
        assert response.is_complete is False
        assert response.chunk_index == 1
        assert response.metadata["stream_id"] == "test-123"


class TestAIServiceExceptions:
    """Test AI service exception classes."""

    def test_ai_service_error(self):
        """Test base AI service error."""
        error = AIServiceError("Something went wrong", error_code="AI001")

        assert str(error) == "Something went wrong"
        assert error.error_code == "AI001"

    def test_ai_service_connection_error(self):
        """Test AI service connection error."""
        error = AIServiceConnectionError(
            "Connection failed",
            error_code="CONN001",
            endpoint="https://test.openai.azure.com/",
        )

        assert str(error) == "Connection failed"
        assert error.error_code == "CONN001"
        assert error.endpoint == "https://test.openai.azure.com/"

    def test_ai_service_timeout_error(self):
        """Test AI service timeout error."""
        error = AIServiceTimeoutError(
            "Request timed out", error_code="TIMEOUT001", timeout_duration=30.0
        )

        assert str(error) == "Request timed out"
        assert error.error_code == "TIMEOUT001"
        assert error.timeout_duration == 30.0

    def test_ai_service_rate_limit_error(self):
        """Test AI service rate limit error."""
        error = AIServiceRateLimitError(
            "Rate limit exceeded", error_code="RATE001", retry_after=60
        )

        assert str(error) == "Rate limit exceeded"
        assert error.error_code == "RATE001"
        assert error.retry_after == 60


class TestAIServiceAdapter:
    """Test AI service adapter abstract base class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock AI service configuration."""
        return AIServiceConfig(
            provider="test_provider",
            endpoint="https://test.api.com/",
            api_key="test-key",
            deployment_name="test-model",
        )

    def test_ai_service_adapter_is_abstract(self):
        """Test that AIServiceAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            AIServiceAdapter()

    def test_ai_service_adapter_abstract_methods(self):
        """Test that AIServiceAdapter defines required abstract methods."""
        # Check that abstract methods are defined
        abstract_methods = AIServiceAdapter.__abstractmethods__

        expected_methods = {
            "initialize",
            "send_query",
            "send_streaming_query",
            "get_health_status",
            "cleanup",
        }

        assert expected_methods.issubset(abstract_methods)

    def test_concrete_ai_service_adapter_implementation(self, mock_config):
        """Test that a concrete implementation can be created."""

        class ConcreteAIServiceAdapter(AIServiceAdapter):
            """Concrete implementation for testing."""

            def __init__(self, config: AIServiceConfig):
                super().__init__(config)
                self._initialized = False
                self._health_status = {"status": "unknown"}

            async def initialize(self) -> bool:
                """Initialize the AI service."""
                self._initialized = True
                return True

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                """Send a query to the AI service."""
                return AIResponse(
                    content=f"Response to: {query}",
                    success=True,
                    metadata={"test": True},
                )

            async def send_streaming_query(self, query: str, **kwargs):
                """Send a streaming query to the AI service."""
                yield AIStreamingResponse(
                    content=f"Streaming response to: {query}",
                    is_complete=True,
                    chunk_index=0,
                )

            async def get_health_status(self) -> dict[str, Any]:
                """Get health status of the AI service."""
                return self._health_status

            async def cleanup(self) -> None:
                """Clean up resources."""
                self._initialized = False

        # Test that concrete implementation works
        adapter = ConcreteAIServiceAdapter(mock_config)

        assert adapter.config == mock_config
        assert adapter.provider == "test_provider"
        assert adapter.endpoint == "https://test.api.com/"

    @pytest.mark.asyncio
    async def test_concrete_adapter_functionality(self, mock_config):
        """Test that concrete adapter methods work correctly."""

        class ConcreteAIServiceAdapter(AIServiceAdapter):
            """Concrete implementation for testing."""

            def __init__(self, config: AIServiceConfig):
                super().__init__(config)
                self._initialized = False

            async def initialize(self) -> bool:
                self._initialized = True
                return True

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                if not self._initialized:
                    raise AIServiceError("Service not initialized")

                return AIResponse(
                    content=f"Response to: {query}",
                    success=True,
                    metadata={"query_length": len(query)},
                )

            async def send_streaming_query(self, query: str, **kwargs):
                if not self._initialized:
                    raise AIServiceError("Service not initialized")

                # Simulate streaming response
                words = query.split()
                for i, word in enumerate(words):
                    yield AIStreamingResponse(
                        content=f"Processing: {word}",
                        is_complete=(i == len(words) - 1),
                        chunk_index=i,
                    )

            async def get_health_status(self) -> dict[str, Any]:
                return {
                    "status": "healthy" if self._initialized else "not_initialized",
                    "initialized": self._initialized,
                }

            async def cleanup(self) -> None:
                self._initialized = False

        adapter = ConcreteAIServiceAdapter(mock_config)

        # Test initialization
        assert await adapter.initialize() is True

        # Test query
        response = await adapter.send_query("Hello world")
        assert response.success is True
        assert response.content == "Response to: Hello world"
        assert response.metadata["query_length"] == 11

        # Test streaming query
        chunks = []
        async for chunk in adapter.send_streaming_query("Hello world test"):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].content == "Processing: Hello"
        assert chunks[1].content == "Processing: world"
        assert chunks[2].content == "Processing: test"
        assert chunks[2].is_complete is True

        # Test health status
        health = await adapter.get_health_status()
        assert health["status"] == "healthy"
        assert health["initialized"] is True

        # Test cleanup
        await adapter.cleanup()
        health = await adapter.get_health_status()
        assert health["status"] == "not_initialized"

    def test_ai_service_adapter_properties(self, mock_config):
        """Test AIServiceAdapter base class properties."""

        class ConcreteAIServiceAdapter(AIServiceAdapter):
            """Minimal concrete implementation."""

            async def initialize(self) -> bool:
                return True

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                return AIResponse(content="test", success=True)

            async def send_streaming_query(self, query: str, **kwargs):
                yield AIStreamingResponse(
                    content="test", is_complete=True, chunk_index=0
                )

            async def get_health_status(self) -> dict[str, Any]:
                return {"status": "healthy"}

            async def cleanup(self) -> None:
                pass

        adapter = ConcreteAIServiceAdapter(mock_config)

        # Test properties
        assert adapter.provider == "test_provider"
        assert adapter.endpoint == "https://test.api.com/"
        assert adapter.deployment_name == "test-model"
        assert adapter.max_tokens == 2000
        assert adapter.temperature == 0.7
        assert adapter.timeout == 30.0
        assert adapter.max_retries == 3

    @pytest.mark.asyncio
    async def test_error_handling_in_concrete_implementation(self, mock_config):
        """Test error handling in concrete adapter implementation."""

        class ErrorProneAIServiceAdapter(AIServiceAdapter):
            """Concrete implementation that raises errors for testing."""

            async def initialize(self) -> bool:
                raise AIServiceConnectionError("Failed to connect")

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                if "timeout" in query.lower():
                    raise AIServiceTimeoutError("Query timed out")
                elif "rate" in query.lower():
                    raise AIServiceRateLimitError("Rate limit exceeded")
                else:
                    raise AIServiceError("General error")

            async def send_streaming_query(self, query: str, **kwargs):
                raise AIServiceError("Streaming not supported")
                yield  # Make it an async generator (unreachable code)

            async def get_health_status(self) -> dict[str, Any]:
                return {"status": "error"}

            async def cleanup(self) -> None:
                pass

        adapter = ErrorProneAIServiceAdapter(mock_config)

        # Test initialization error
        with pytest.raises(AIServiceConnectionError, match="Failed to connect"):
            await adapter.initialize()

        # Test query errors
        with pytest.raises(AIServiceTimeoutError, match="Query timed out"):
            await adapter.send_query("This will timeout")

        with pytest.raises(AIServiceRateLimitError, match="Rate limit exceeded"):
            await adapter.send_query("This will hit rate limit")

        with pytest.raises(AIServiceError, match="General error"):
            await adapter.send_query("This will fail")

        # Test streaming error
        with pytest.raises(AIServiceError, match="Streaming not supported"):
            async for _chunk in adapter.send_streaming_query("test"):
                pass
