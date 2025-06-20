"""
Unit tests for AIServiceAdapter class interface and basic functionality.

Tests the core AI service adapter interface, basic functionality,
and abstract method contracts.
"""

import asyncio
import time
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
            "_perform_connection",
            "_perform_health_check",
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

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                await asyncio.sleep(0.01)

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await asyncio.sleep(0.01)

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

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                await asyncio.sleep(0.01)

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await asyncio.sleep(0.01)

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

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                await asyncio.sleep(0.01)

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await asyncio.sleep(0.01)

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

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                await asyncio.sleep(0.01)

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await asyncio.sleep(0.01)

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


class TestConnectionManagement:
    """Test connection management functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock AI service configuration with connection parameters."""
        return AIServiceConfig(
            provider="test_provider",
            endpoint="https://test.api.com/",
            api_key="test-key",
            deployment_name="test-model",
            timeout=5.0,
            max_retries=3,
        )

    @pytest.fixture
    def connection_adapter(self, mock_config):
        """Create a connection-aware AI service adapter for testing."""

        class ConnectionAwareAdapter(AIServiceAdapter):
            def __init__(self, config: AIServiceConfig):
                super().__init__(config)
                self._connection_state = "disconnected"
                self._connection_attempts = 0
                self.connection_timeout_count = 0
                self._last_connection_time = None
                self._connection_pool = {}

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                await self._simulate_connection()

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await self._simulate_health_check()

            async def initialize(self) -> bool:
                """Initialize with connection management."""
                return await self.connect_with_retry()

            async def connect_with_retry(self) -> bool:
                """Connect with retry logic and timeout handling."""
                for attempt in range(self.max_retries + 1):
                    try:
                        self._connection_attempts += 1
                        await self._attempt_connection()
                        self._connection_state = "connected"
                        self._last_connection_time = time.time()
                        return True
                    except AIServiceTimeoutError:
                        self.connection_timeout_count += 1
                        if attempt < self.max_retries:
                            delay = 2 ** attempt  # Exponential backoff
                            await asyncio.sleep(delay)
                            continue
                        raise
                    except AIServiceConnectionError:
                        if attempt < self.max_retries:
                            delay = 2 ** attempt
                            await asyncio.sleep(delay)
                            continue
                        raise
                return False

            async def _attempt_connection(self):
                """Attempt a single connection with timeout."""
                # Simulate connection attempt with timeout
                try:
                    await asyncio.wait_for(
                        self._simulate_connection(),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    raise AIServiceTimeoutError(
                        f"Connection timeout after {self.timeout}s",
                        timeout_duration=self.timeout
                    )
                except Exception as e:
                    raise AIServiceConnectionError(
                        f"Connection failed: {str(e)}",
                        endpoint=self.endpoint
                    )

            async def _simulate_connection(self):
                """Simulate connection process."""
                # This would be overridden in real implementations
                await asyncio.sleep(0.1)  # Simulate connection time

            async def check_connection(self) -> bool:
                """Check if connection is still alive."""
                if self._connection_state != "connected":
                    return False

                # Simulate connection health check
                try:
                    await asyncio.wait_for(
                        self._simulate_health_check(),
                        timeout=self.timeout / 2
                    )
                    return True
                except (asyncio.TimeoutError, Exception):
                    self._connection_state = "disconnected"
                    return False

            async def _simulate_health_check(self):
                """Simulate health check."""
                await asyncio.sleep(0.05)

            async def reconnect_if_needed(self) -> bool:
                """Reconnect if connection is lost."""
                if await self.check_connection():
                    return True

                self._logger.info("Connection lost, attempting to reconnect...")
                return await self.connect_with_retry()

            async def close_connection(self):
                """Close the connection."""
                self._connection_state = "disconnected"
                self._connection_pool.clear()

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                """Send query with connection management."""
                # Ensure connection is available
                if not await self.reconnect_if_needed():
                    raise AIServiceConnectionError(
                        "Unable to establish connection",
                        endpoint=self.endpoint
                    )

                # Simulate query execution
                return AIResponse(
                    content=f"Response to: {query}",
                    success=True,
                    metadata={"connection_state": self._connection_state}
                )

            async def send_streaming_query(self, query: str, **kwargs):
                """Send streaming query with connection management."""
                # Ensure connection is available
                if not await self.reconnect_if_needed():
                    raise AIServiceConnectionError(
                        "Unable to establish connection",
                        endpoint=self.endpoint
                    )

                # Simulate streaming response
                for i in range(3):
                    yield AIStreamingResponse(
                        content=f"Chunk {i+1}: {query}",
                        is_complete=(i == 2),
                        chunk_index=i
                    )
                    await asyncio.sleep(0.1)

            async def get_health_status(self) -> dict[str, Any]:
                """Get health status with connection info."""
                return {
                    "status": "healthy" if self._connection_state == "connected" else "unhealthy",
                    "connection_state": self._connection_state,
                    "connection_attempts": self._connection_attempts,
                    "timeout_count": self.connection_timeout_count,
                    "last_connection_time": self._last_connection_time,
                }

            async def cleanup(self) -> None:
                """Cleanup with connection management."""
                await self.close_connection()

        return ConnectionAwareAdapter(mock_config)

    @pytest.mark.asyncio
    async def test_successful_connection_with_retry(self, connection_adapter):
        """Test successful connection establishment with retry capability."""
        # Test successful connection
        success = await connection_adapter.initialize()

        assert success is True
        assert connection_adapter.connection_state == "connected"
        assert connection_adapter.connection_attempts == 1
        assert connection_adapter.last_connection_time is not None

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, mock_config):
        """Test connection timeout handling and retry logic."""

        class TimeoutAdapter(AIServiceAdapter):
            def __init__(self, config: AIServiceConfig):
                super().__init__(config)
                self.timeout_count = 0

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                await asyncio.sleep(10)  # Simulate long connection time

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await asyncio.sleep(0.01)

            async def initialize(self) -> bool:
                return await self.connect_with_retry()

            async def connect_with_retry(self) -> bool:
                for attempt in range(self.max_retries + 1):
                    try:
                        self.timeout_count += 1
                        await asyncio.wait_for(
                            asyncio.sleep(10),  # Simulate long connection time
                            timeout=0.1  # Very short timeout
                        )
                        return True
                    except asyncio.TimeoutError:
                        if attempt < self.max_retries:
                            continue
                        raise AIServiceTimeoutError(
                            "Connection timeout after retries",
                            timeout_duration=self.timeout
                        )
                return False

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                return AIResponse(content="", success=False)

            async def send_streaming_query(self, query: str, **kwargs):
                yield AIStreamingResponse(content="", is_complete=True, chunk_index=0)

            async def get_health_status(self) -> dict[str, Any]:
                return {"status": "timeout_test"}

            async def cleanup(self) -> None:
                pass

        adapter = TimeoutAdapter(mock_config)

        with pytest.raises(AIServiceTimeoutError) as exc_info:
            await adapter.initialize()

        assert "Connection timeout after retries" in str(exc_info.value)
        assert adapter.timeout_count == mock_config.max_retries + 1

    @pytest.mark.asyncio
    async def test_connection_health_check(self, connection_adapter):
        """Test connection health checking functionality."""
        # Initialize connection
        await connection_adapter.initialize()

        # Test healthy connection
        is_healthy = await connection_adapter.check_connection()
        assert is_healthy is True

        # Simulate connection loss
        connection_adapter._connection_state = "disconnected"
        is_healthy = await connection_adapter.check_connection()
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_automatic_reconnection(self, connection_adapter):
        """Test automatic reconnection when connection is lost."""
        # Initialize connection
        await connection_adapter.initialize()
        initial_attempts = connection_adapter.connection_attempts

        # Simulate connection loss
        connection_adapter._connection_state = "disconnected"

        # Attempt to reconnect
        reconnected = await connection_adapter.reconnect_if_needed()

        assert reconnected is True
        assert connection_adapter.connection_state == "connected"
        assert connection_adapter.connection_attempts > initial_attempts

    @pytest.mark.asyncio
    async def test_query_with_connection_management(self, connection_adapter):
        """Test query execution with connection management."""
        # Initialize connection
        await connection_adapter.initialize()

        # Simulate connection loss
        connection_adapter._connection_state = "disconnected"

        # Send query (should trigger reconnection)
        response = await connection_adapter.send_query("test query")

        assert response.success is True
        assert "Response to: test query" in response.content
        assert connection_adapter.connection_state == "connected"

    @pytest.mark.asyncio
    async def test_streaming_with_connection_management(self, connection_adapter):
        """Test streaming query with connection management."""
        # Initialize connection
        await connection_adapter.initialize()

        # Simulate connection loss
        connection_adapter._connection_state = "disconnected"

        # Send streaming query (should trigger reconnection)
        chunks = []
        async for chunk in connection_adapter.send_streaming_query("test stream"):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].content == "Chunk 1: test stream"
        assert chunks[2].is_complete is True
        assert connection_adapter.connection_state == "connected"

    @pytest.mark.asyncio
    async def test_connection_cleanup(self, connection_adapter):
        """Test proper connection cleanup."""
        # Initialize connection
        await connection_adapter.initialize()
        assert connection_adapter.connection_state == "connected"

        # Cleanup
        await connection_adapter.cleanup()
        assert connection_adapter.connection_state == "disconnected"
        assert len(connection_adapter._connection_pool) == 0

    @pytest.mark.asyncio
    async def test_health_status_with_connection_info(self, connection_adapter):
        """Test health status reporting with connection information."""
        # Initialize connection
        await connection_adapter.initialize()

        # Get health status
        health = await connection_adapter.get_health_status()

        assert health["status"] == "healthy"
        assert health["connection_state"] == "connected"
        assert health["connection_attempts"] >= 1
        assert health["last_connection_time"] is not None

    @pytest.mark.asyncio
    async def test_connection_failure_after_max_retries(self, mock_config):
        """Test connection failure after exceeding max retries."""

        class FailingAdapter(AIServiceAdapter):
            def __init__(self, config: AIServiceConfig):
                super().__init__(config)
                self.attempt_count = 0

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                raise Exception("Connection failed for testing")

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await asyncio.sleep(0.01)

            async def initialize(self) -> bool:
                for attempt in range(self.max_retries + 1):
                    self.attempt_count += 1
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.1)
                        continue
                    raise AIServiceConnectionError(
                        "Connection failed after all retries",
                        endpoint=self.endpoint
                    )
                return False

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                return AIResponse(content="", success=False)

            async def send_streaming_query(self, query: str, **kwargs):
                yield AIStreamingResponse(content="", is_complete=True, chunk_index=0)

            async def get_health_status(self) -> dict[str, Any]:
                return {"status": "failing"}

            async def cleanup(self) -> None:
                pass

        adapter = FailingAdapter(mock_config)

        with pytest.raises(AIServiceConnectionError) as exc_info:
            await adapter.initialize()

        assert "Connection failed after all retries" in str(exc_info.value)
        assert adapter.attempt_count == mock_config.max_retries + 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self, mock_config):
        """Test exponential backoff timing in retry logic."""

        class TimingAdapter(AIServiceAdapter):
            def __init__(self, config: AIServiceConfig):
                super().__init__(config)
                self.attempt_times = []

            async def _perform_connection(self) -> None:
                """Perform connection for testing."""
                await asyncio.sleep(0.01)

            async def _perform_health_check(self) -> None:
                """Perform health check for testing."""
                await asyncio.sleep(0.01)

            async def initialize(self) -> bool:
                start_time = time.time()

                for attempt in range(self.max_retries + 1):
                    self.attempt_times.append(time.time() - start_time)

                    if attempt < self.max_retries:
                        delay = 2 ** attempt * 0.1  # Short delays for testing
                        await asyncio.sleep(delay)
                        continue

                    # Succeed on final attempt
                    return True

                return False

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                return AIResponse(content="", success=True)

            async def send_streaming_query(self, query: str, **kwargs):
                yield AIStreamingResponse(content="", is_complete=True, chunk_index=0)

            async def get_health_status(self) -> dict[str, Any]:
                return {"status": "timing_test"}

            async def cleanup(self) -> None:
                pass

        adapter = TimingAdapter(mock_config)
        success = await adapter.initialize()

        assert success is True
        assert len(adapter.attempt_times) == mock_config.max_retries + 1

        # Verify exponential backoff (allowing for timing variance)
        for i in range(1, len(adapter.attempt_times)):
            time_diff = adapter.attempt_times[i] - adapter.attempt_times[i-1]
            expected_min_delay = (2 ** (i-1)) * 0.1 * 0.8  # 20% tolerance
            assert time_diff >= expected_min_delay


class TestAIServiceAdapterConnectionMethods:
    """Test connection management methods in the base AIServiceAdapter class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock AI service configuration."""
        return AIServiceConfig(
            provider="test_provider",
            endpoint="https://test.api.com/",
            api_key="test-key",
            deployment_name="test-model",
            timeout=2.0,
            max_retries=2,
        )

    @pytest.fixture
    def base_adapter(self, mock_config):
        """Create a concrete implementation of AIServiceAdapter for testing."""

        class TestableAdapter(AIServiceAdapter):
            def __init__(self, config: AIServiceConfig):
                super().__init__(config)
                self.perform_connection_calls = 0
                self.perform_health_check_calls = 0
                self.perform_cleanup_calls = 0
                self.should_connection_fail = False
                self.should_health_check_fail = False

            async def _perform_connection(self) -> None:
                """Test implementation of connection."""
                self.perform_connection_calls += 1
                if self.should_connection_fail:
                    raise Exception("Connection failed for testing")
                await asyncio.sleep(0.1)  # Simulate connection time

            async def _perform_health_check(self) -> None:
                """Test implementation of health check."""
                self.perform_health_check_calls += 1
                if self.should_health_check_fail:
                    raise Exception("Health check failed for testing")
                await asyncio.sleep(0.05)  # Simulate health check time

            async def _perform_connection_cleanup(self) -> None:
                """Test implementation of cleanup."""
                self.perform_cleanup_calls += 1
                await asyncio.sleep(0.05)  # Simulate cleanup time

            async def initialize(self) -> bool:
                """Test implementation of initialize."""
                return await self.connect_with_retry()

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                """Test implementation of send_query."""
                return AIResponse(content=f"Response: {query}", success=True)

            async def send_streaming_query(self, query: str, **kwargs):
                """Test implementation of streaming query."""
                yield AIStreamingResponse(
                    content=f"Stream: {query}",
                    is_complete=True,
                    chunk_index=0
                )

            async def get_health_status(self) -> dict[str, Any]:
                """Test implementation of health status."""
                return {
                    "status": "healthy" if self.connection_state == "connected" else "unhealthy",
                    "connection_state": self.connection_state,
                    "connection_attempts": self.connection_attempts,
                }

            async def cleanup(self) -> None:
                """Test implementation of cleanup."""
                await self.close_connection()

        return TestableAdapter(mock_config)

    @pytest.mark.asyncio
    async def test_connection_state_properties(self, base_adapter):
        """Test connection state properties."""
        # Initial state
        assert base_adapter.connection_state == "disconnected"
        assert base_adapter.connection_attempts == 0
        assert base_adapter.last_connection_time is None

        # After successful connection
        success = await base_adapter.connect_with_retry()
        assert success is True
        assert base_adapter.connection_state == "connected"
        assert base_adapter.connection_attempts == 1
        assert base_adapter.last_connection_time is not None

    @pytest.mark.asyncio
    async def test_connect_with_retry_success(self, base_adapter):
        """Test successful connection with retry logic."""
        success = await base_adapter.connect_with_retry()

        assert success is True
        assert base_adapter.connection_state == "connected"
        assert base_adapter.perform_connection_calls == 1

    @pytest.mark.asyncio
    async def test_connect_with_retry_failure(self, base_adapter):
        """Test connection failure after max retries."""
        base_adapter.should_connection_fail = True

        with pytest.raises(AIServiceConnectionError):
            await base_adapter.connect_with_retry()

        # Should have tried max_retries + 1 times
        assert base_adapter.perform_connection_calls == base_adapter.max_retries + 1
        assert base_adapter.connection_state == "disconnected"

    @pytest.mark.asyncio
    async def test_check_connection_healthy(self, base_adapter):
        """Test connection health check when healthy."""
        # Connect first
        await base_adapter.connect_with_retry()

        # Check health
        is_healthy = await base_adapter.check_connection()
        assert is_healthy is True
        assert base_adapter.perform_health_check_calls == 1

    @pytest.mark.asyncio
    async def test_check_connection_unhealthy(self, base_adapter):
        """Test connection health check when unhealthy."""
        # Connect first
        await base_adapter.connect_with_retry()

        # Make health check fail
        base_adapter.should_health_check_fail = True

        # Check health
        is_healthy = await base_adapter.check_connection()
        assert is_healthy is False
        assert base_adapter.connection_state == "disconnected"

    @pytest.mark.asyncio
    async def test_check_connection_when_disconnected(self, base_adapter):
        """Test connection health check when already disconnected."""
        # Don't connect, just check
        is_healthy = await base_adapter.check_connection()
        assert is_healthy is False
        assert base_adapter.perform_health_check_calls == 0  # Should not call health check

    @pytest.mark.asyncio
    async def test_reconnect_if_needed_when_healthy(self, base_adapter):
        """Test reconnect when connection is healthy."""
        # Connect first
        await base_adapter.connect_with_retry()
        initial_attempts = base_adapter.connection_attempts

        # Reconnect should not be needed
        success = await base_adapter.reconnect_if_needed()
        assert success is True
        assert base_adapter.connection_attempts == initial_attempts  # No new attempts

    @pytest.mark.asyncio
    async def test_reconnect_if_needed_when_unhealthy(self, base_adapter):
        """Test reconnect when connection is unhealthy."""
        # Connect first
        await base_adapter.connect_with_retry()
        initial_attempts = base_adapter.connection_attempts

        # Simulate connection loss
        base_adapter._connection_state = "disconnected"

        # Reconnect should be triggered
        success = await base_adapter.reconnect_if_needed()
        assert success is True
        assert base_adapter.connection_attempts > initial_attempts

    @pytest.mark.asyncio
    async def test_close_connection(self, base_adapter):
        """Test connection closure."""
        # Connect first
        await base_adapter.connect_with_retry()
        assert base_adapter.connection_state == "connected"

        # Close connection
        await base_adapter.close_connection()
        assert base_adapter.connection_state == "disconnected"
        assert base_adapter.perform_cleanup_calls == 1

    @pytest.mark.asyncio
    async def test_calculate_backoff_delay(self, base_adapter):
        """Test exponential backoff delay calculation."""
        # Test different attempt numbers
        delay_0 = base_adapter._calculate_backoff_delay(0)
        delay_1 = base_adapter._calculate_backoff_delay(1)
        delay_2 = base_adapter._calculate_backoff_delay(2)
        delay_10 = base_adapter._calculate_backoff_delay(10)

        # Should increase exponentially
        assert delay_0 == 1.0  # Base delay
        assert delay_1 == 2.0  # 1 * 2^1
        assert delay_2 == 4.0  # 1 * 2^2
        assert delay_10 == 30.0  # Should be capped at max_delay

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, base_adapter):
        """Test connection timeout handling."""
        # Create adapter with very short timeout
        config = AIServiceConfig(
            provider="test_provider",
            endpoint="https://test.api.com/",
            api_key="test-key",
            deployment_name="test-model",
            timeout=0.1,  # Very short timeout
            max_retries=1,
        )

        class SlowAdapter(AIServiceAdapter):
            async def _perform_connection(self) -> None:
                await asyncio.sleep(1.0)  # Longer than timeout

            async def _perform_health_check(self) -> None:
                pass

            async def initialize(self) -> bool:
                return True

            async def send_query(self, query: str, **kwargs) -> AIResponse:
                return AIResponse(content="", success=True)

            async def send_streaming_query(self, query: str, **kwargs):
                yield AIStreamingResponse(content="", is_complete=True, chunk_index=0)

            async def get_health_status(self) -> dict[str, Any]:
                return {"status": "test"}

            async def cleanup(self) -> None:
                pass

        slow_adapter = SlowAdapter(config)

        with pytest.raises(AIServiceTimeoutError) as exc_info:
            await slow_adapter.connect_with_retry()

        assert "Connection timeout after" in str(exc_info.value)
        assert exc_info.value.timeout_duration == 0.1
