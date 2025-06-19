"""
Unit tests for AI query processing logic and response management.

Tests query processing, error handling, retry mechanisms, and response formatting.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.my_coding_agent.core.ai_services.ai_service_adapter import (
    AIResponse,
    AIServiceAdapter,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIStreamingResponse,
)
from src.my_coding_agent.core.ai_services.query_processor import (
    QueryProcessor,
    QueryRequest,
    ResponseValidator,
    RetryPolicy,
)


class TestQueryRequest:
    """Test query request data structures."""

    def test_query_request_creation(self):
        """Test basic query request creation."""
        request = QueryRequest(
            query="What is the weather like?",
            context={"user_id": "123", "session_id": "abc"},
            max_tokens=1000,
            temperature=0.8,
            timeout=25.0,
        )

        assert request.query == "What is the weather like?"
        assert request.context["user_id"] == "123"
        assert request.context["session_id"] == "abc"
        assert request.max_tokens == 1000
        assert request.temperature == 0.8
        assert request.timeout == 25.0

    def test_query_request_defaults(self):
        """Test query request with default values."""
        request = QueryRequest(query="Hello world")

        assert request.query == "Hello world"
        assert request.context == {}
        assert request.max_tokens is None
        assert request.temperature is None
        assert request.timeout is None

    def test_query_request_validation(self):
        """Test query request validation."""
        # Test empty query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            QueryRequest(query="")

        with pytest.raises(ValueError, match="Query cannot be empty"):
            QueryRequest(query="   ")


class TestRetryPolicy:
    """Test retry policy configuration and logic."""

    def test_retry_policy_creation(self):
        """Test retry policy creation."""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
            backoff_multiplier=2.5,
            retry_on_errors=[AIServiceTimeoutError, AIServiceRateLimitError],
        )

        assert policy.max_retries == 5
        assert policy.base_delay == 2.0
        assert policy.max_delay == 60.0
        assert policy.backoff_multiplier == 2.5
        assert AIServiceTimeoutError in policy.retry_on_errors
        assert AIServiceRateLimitError in policy.retry_on_errors

    def test_calculate_delay(self):
        """Test retry delay calculation."""
        policy = RetryPolicy(base_delay=1.0, backoff_multiplier=2.0, max_delay=10.0)

        # Test exponential backoff
        assert policy.calculate_delay(0) == 1.0
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(2) == 4.0
        assert policy.calculate_delay(3) == 8.0

        # Test max delay cap
        assert policy.calculate_delay(10) == 10.0

    def test_should_retry(self):
        """Test retry decision logic."""
        policy = RetryPolicy(
            max_retries=3,
            retry_on_errors=[AIServiceTimeoutError, AIServiceRateLimitError],
        )

        # Test retry on allowed errors
        assert policy.should_retry(AIServiceTimeoutError("timeout"), 0) is True
        assert policy.should_retry(AIServiceRateLimitError("rate limit"), 1) is True

        # Test no retry on max retries reached
        assert policy.should_retry(AIServiceTimeoutError("timeout"), 3) is False

        # Test no retry on non-retryable errors
        assert policy.should_retry(AIServiceError("general error"), 0) is False


class TestQueryProcessor:
    """Test query processor implementation."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock AI service adapter."""
        adapter = Mock(spec=AIServiceAdapter)
        adapter.send_query = AsyncMock()
        adapter.send_streaming_query = AsyncMock()
        return adapter

    @pytest.fixture
    def query_processor(self, mock_adapter):
        """Create a query processor with mocked adapter."""
        return QueryProcessor(
            adapter=mock_adapter,
            retry_policy=RetryPolicy(max_retries=2),
            response_validator=ResponseValidator(),
        )

    @pytest.mark.asyncio
    async def test_process_query_success(self, query_processor, mock_adapter):
        """Test successful query processing."""
        # Setup mock response
        expected_response = AIResponse(
            content="Hello! How can I help you?",
            success=True,
            metadata={"model": "gpt-4", "tokens": 25},
        )
        mock_adapter.send_query.return_value = expected_response

        # Process query
        request = QueryRequest(query="Hello")
        response = await query_processor.process_query(request)

        # Verify response
        assert response.success is True
        assert response.content == "Hello! How can I help you?"
        assert response.metadata["model"] == "gpt-4"

        # Verify adapter was called correctly
        mock_adapter.send_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_with_retry(self, query_processor, mock_adapter):
        """Test query processing with retry on timeout."""
        # Setup mock to fail first, then succeed
        timeout_error = AIServiceTimeoutError("Request timed out")
        success_response = AIResponse(content="Success after retry", success=True)

        mock_adapter.send_query.side_effect = [timeout_error, success_response]

        # Process query
        request = QueryRequest(query="Test retry")
        response = await query_processor.process_query(request)

        # Verify successful response after retry
        assert response.success is True
        assert response.content == "Success after retry"
        assert response.retry_count == 1

        # Verify adapter was called twice
        assert mock_adapter.send_query.call_count == 2

    @pytest.mark.asyncio
    async def test_process_query_max_retries_exceeded(
        self, query_processor, mock_adapter
    ):
        """Test query processing when max retries are exceeded."""
        # Setup mock to always fail
        timeout_error = AIServiceTimeoutError("Persistent timeout")
        mock_adapter.send_query.side_effect = timeout_error

        # Process query
        request = QueryRequest(query="Will fail")

        # Should raise the error after max retries
        with pytest.raises(AIServiceTimeoutError, match="Persistent timeout"):
            await query_processor.process_query(request)

        # Verify adapter was called max_retries + 1 times
        assert mock_adapter.send_query.call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_process_query_non_retryable_error(
        self, query_processor, mock_adapter
    ):
        """Test query processing with non-retryable error."""
        # Setup mock to fail with non-retryable error
        general_error = AIServiceError("General error")
        mock_adapter.send_query.side_effect = general_error

        # Process query
        request = QueryRequest(query="Will fail immediately")

        # Should raise the error immediately without retries
        with pytest.raises(AIServiceError, match="General error"):
            await query_processor.process_query(request)

        # Verify adapter was called only once
        assert mock_adapter.send_query.call_count == 1

    @pytest.mark.asyncio
    async def test_process_streaming_query_success(self, query_processor, mock_adapter):
        """Test successful streaming query processing."""

        # Setup mock streaming response
        async def mock_streaming(query, **kwargs):
            yield AIStreamingResponse(
                content="Chunk 1", is_complete=False, chunk_index=0
            )
            yield AIStreamingResponse(
                content="Chunk 2", is_complete=False, chunk_index=1
            )
            yield AIStreamingResponse(content="Final", is_complete=True, chunk_index=2)

        # Configure mock to return the async generator directly
        mock_adapter.send_streaming_query = mock_streaming

        # Process streaming query
        request = QueryRequest(query="Stream test")
        chunks = []
        async for chunk in query_processor.process_streaming_query(request):
            chunks.append(chunk)

        # Verify chunks
        assert len(chunks) == 3
        assert chunks[0].content == "Chunk 1"
        assert chunks[1].content == "Chunk 2"
        assert chunks[2].content == "Final"
        assert chunks[2].is_complete is True

    @pytest.mark.asyncio
    async def test_process_streaming_query_with_error(
        self, query_processor, mock_adapter
    ):
        """Test streaming query processing with error."""

        # Setup mock to raise error
        async def mock_streaming_error(query, **kwargs):
            yield AIStreamingResponse(
                content="Chunk 1", is_complete=False, chunk_index=0
            )
            raise AIServiceError("Streaming error")

        mock_adapter.send_streaming_query = mock_streaming_error

        # Process streaming query
        request = QueryRequest(query="Stream error test")

        chunks = []
        with pytest.raises(AIServiceError, match="Streaming error"):
            async for chunk in query_processor.process_streaming_query(request):
                chunks.append(chunk)

        # Should have received first chunk before error
        assert len(chunks) == 1
        assert chunks[0].content == "Chunk 1"

    @pytest.mark.asyncio
    async def test_query_context_handling(self, query_processor, mock_adapter):
        """Test query context is properly passed through."""
        # Setup mock response
        mock_adapter.send_query.return_value = AIResponse(
            content="Response", success=True
        )

        # Create request with context
        context_dict = {
            "conversation_id": "conv-123",
            "user_id": "user-456",
            "metadata": {"priority": "high"},
        }
        request = QueryRequest(query="Test", context=context_dict)

        # Process query
        await query_processor.process_query(request)

        # Verify context was passed to adapter
        call_kwargs = mock_adapter.send_query.call_args[1]
        assert "context" in call_kwargs
        assert call_kwargs["context"] == context_dict

    @pytest.mark.asyncio
    async def test_query_parameter_override(self, query_processor, mock_adapter):
        """Test that request parameters override defaults."""
        # Setup mock response
        mock_adapter.send_query.return_value = AIResponse(
            content="Response", success=True
        )

        # Create request with custom parameters
        request = QueryRequest(
            query="Test",
            max_tokens=500,
            temperature=0.9,
            timeout=45.0,
        )

        # Process query
        await query_processor.process_query(request)

        # Verify parameters were passed to adapter
        call_kwargs = mock_adapter.send_query.call_args[1]
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["temperature"] == 0.9
        assert call_kwargs["timeout"] == 45.0

    def test_query_processor_initialization(self, mock_adapter):
        """Test query processor initialization."""
        retry_policy = RetryPolicy(max_retries=5)
        validator = ResponseValidator(allow_empty_content=False)

        processor = QueryProcessor(
            adapter=mock_adapter,
            retry_policy=retry_policy,
            response_validator=validator,
        )

        assert processor.adapter == mock_adapter
        assert processor.retry_policy == retry_policy
        assert processor.response_validator == validator

    @pytest.mark.asyncio
    async def test_response_validation_integration(self, mock_adapter):
        """Test response validation integration."""
        # Create processor with strict validation
        validator = ResponseValidator(allow_empty_content=False)
        processor = QueryProcessor(
            adapter=mock_adapter,
            retry_policy=RetryPolicy(max_retries=1),
            response_validator=validator,
        )

        # Setup mock to return empty response
        empty_response = AIResponse(content="", success=True)
        mock_adapter.send_query.return_value = empty_response

        # Process query - should handle validation failure
        request = QueryRequest(query="Test")
        response = await processor.process_query(request)

        # Should return error response due to validation failure
        assert response.success is False
        assert response.error is not None
        assert "validation failed" in response.error.lower()
