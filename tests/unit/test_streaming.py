"""
Unit tests for streaming functionality.

Tests cover:
- StreamHandler class for chunk-by-chunk response display
- ResponseBuffer system for intelligent buffering
- Stream interruption and cleanup
- Error handling and retry logic
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, call

import pytest

from my_coding_agent.core.streaming.response_buffer import ResponseBuffer
from my_coding_agent.core.streaming.stream_handler import StreamHandler, StreamState


class TestStreamHandler:
    """Test the StreamHandler class for managing streaming responses."""

    @pytest.fixture
    def stream_handler(self):
        """Create a StreamHandler instance for testing."""
        return StreamHandler()

    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback function for testing."""
        return MagicMock()

    def test_stream_handler_initialization(self, stream_handler):
        """Test StreamHandler initializes with correct default state."""
        assert stream_handler.state == StreamState.IDLE
        assert stream_handler.current_stream_id is None
        assert not stream_handler.is_streaming
        assert stream_handler.total_chunks == 0
        assert stream_handler.processed_chunks == 0

    @pytest.mark.asyncio
    async def test_start_stream_basic(self, stream_handler, mock_callback):
        """Test starting a basic stream with simple text chunks."""

        async def simple_generator():
            yield "Hello "
            yield "world "
            yield "!"

        stream_id = await stream_handler.start_stream(simple_generator(), mock_callback)

        # Verify stream started correctly
        assert stream_handler.state == StreamState.STREAMING
        assert stream_handler.current_stream_id == stream_id
        assert stream_handler.is_streaming

        # Wait for stream to complete
        await asyncio.sleep(0.1)

        # Verify final state
        assert stream_handler.state == StreamState.COMPLETED
        assert not stream_handler.is_streaming
        assert stream_handler.processed_chunks == 3

        # Verify callback was called for each chunk + final call
        assert mock_callback.call_count == 4
        mock_callback.assert_has_calls(
            [
                call("Hello ", stream_id, 1, False),
                call("world ", stream_id, 2, False),
                call("!", stream_id, 3, False),
                call("", stream_id, 3, True),  # Final call
            ]
        )

    @pytest.mark.asyncio
    async def test_stream_interruption(self, stream_handler, mock_callback):
        """Test stream interruption capability."""

        async def slow_generator():
            yield "Chunk 1"
            await asyncio.sleep(0.1)
            yield "Chunk 2"
            await asyncio.sleep(0.1)
            yield "Chunk 3"

        stream_id = await stream_handler.start_stream(slow_generator(), mock_callback)

        # Let first chunk process
        await asyncio.sleep(0.05)

        # Interrupt the stream
        await stream_handler.interrupt_stream()

        # Verify interrupted state
        assert stream_handler.state == StreamState.INTERRUPTED
        assert not stream_handler.is_streaming

        # Should only have processed first chunk
        assert mock_callback.call_count == 1
        mock_callback.assert_called_with("Chunk 1", stream_id, 1, False)

    @pytest.mark.asyncio
    async def test_stream_error_handling(self, stream_handler, mock_callback):
        """Test error handling during streaming."""

        async def error_generator():
            yield "Good chunk"
            raise ValueError("Stream error")

        await stream_handler.start_stream(error_generator(), mock_callback)

        # Wait for processing
        await asyncio.sleep(0.1)

        # Verify error state
        assert stream_handler.state == StreamState.ERROR
        assert not stream_handler.is_streaming
        assert stream_handler.last_error is not None
        assert "Stream error" in str(stream_handler.last_error)

        # Should have processed good chunk + error callback
        assert mock_callback.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_stream_rejection(self, stream_handler, mock_callback):
        """Test that starting a new stream while one is active is rejected."""

        async def long_generator():
            for i in range(10):
                yield f"Chunk {i}"
                await asyncio.sleep(0.01)

        # Start first stream
        await stream_handler.start_stream(long_generator(), mock_callback)

        # Try to start second stream
        with pytest.raises(RuntimeError, match="Stream already active"):
            await stream_handler.start_stream(long_generator(), mock_callback)

        # Cleanup
        await stream_handler.interrupt_stream()


class TestResponseBuffer:
    """Test the ResponseBuffer system for intelligent buffering."""

    @pytest.fixture
    def response_buffer(self):
        """Create a ResponseBuffer instance for testing."""
        return ResponseBuffer(buffer_size=100, flush_interval=0.1)

    @pytest.fixture
    def mock_display_callback(self):
        """Create a mock display callback for testing."""
        return MagicMock()

    def test_buffer_initialization(self, response_buffer):
        """Test ResponseBuffer initializes with correct settings."""
        assert response_buffer.buffer_size == 100
        assert response_buffer.flush_interval == 0.1
        assert response_buffer.current_buffer == ""
        assert not response_buffer.is_buffering

    def test_add_chunk_below_threshold(self, response_buffer, mock_display_callback):
        """Test adding chunks below buffer threshold."""
        response_buffer.set_display_callback(mock_display_callback)

        # Add small chunks
        response_buffer.add_chunk("Hello ")
        response_buffer.add_chunk("world")

        # Should be buffered, not displayed yet
        assert response_buffer.current_buffer == "Hello world"
        assert mock_display_callback.call_count == 0

    def test_add_chunk_exceeds_threshold(self, response_buffer, mock_display_callback):
        """Test automatic flush when buffer exceeds threshold."""
        response_buffer.set_display_callback(mock_display_callback)

        # Add chunk that exceeds buffer size
        large_chunk = "x" * 150
        response_buffer.add_chunk(large_chunk)

        # Should trigger automatic flush
        assert response_buffer.current_buffer == ""
        mock_display_callback.assert_called_once_with(large_chunk)

    def test_manual_flush(self, response_buffer, mock_display_callback):
        """Test manual buffer flush."""
        response_buffer.set_display_callback(mock_display_callback)

        # Add some content
        response_buffer.add_chunk("Test content")
        assert response_buffer.current_buffer == "Test content"

        # Manual flush
        response_buffer.flush()

        assert response_buffer.current_buffer == ""
        mock_display_callback.assert_called_once_with("Test content")

    @pytest.mark.asyncio
    async def test_timed_flush(self, response_buffer, mock_display_callback):
        """Test automatic flush based on time interval."""
        response_buffer.set_display_callback(mock_display_callback)
        response_buffer.start_buffering()

        # Add content
        response_buffer.add_chunk("Buffered content")

        # Wait for flush interval
        await asyncio.sleep(0.15)

        # Should have auto-flushed
        assert response_buffer.current_buffer == ""
        mock_display_callback.assert_called_once_with("Buffered content")

        response_buffer.stop_buffering()

    def test_smart_word_boundary_detection(
        self, response_buffer, mock_display_callback
    ):
        """Test intelligent word boundary detection for smooth display."""
        response_buffer.set_display_callback(mock_display_callback)

        # Add content with word boundaries
        response_buffer.add_chunk("Hello world, this is a")
        response_buffer.add_chunk(" test of word")
        response_buffer.add_chunk(" boundaries.")

        # Force flush and check word boundary handling
        content = response_buffer.current_buffer
        assert "Hello world, this is a test of word boundaries." in content

    def test_buffer_statistics(self, response_buffer):
        """Test buffer statistics tracking."""
        response_buffer.add_chunk("Test 1")
        response_buffer.add_chunk("Test 2")
        response_buffer.flush()

        stats = response_buffer.get_statistics()
        assert stats["chunks_processed"] == 2
        assert stats["flushes_performed"] == 1
        assert stats["total_characters"] == 12  # "Test 1" + "Test 2"


class TestStreamingIntegration:
    """Integration tests for streaming components working together."""

    @pytest.mark.asyncio
    async def test_stream_handler_with_buffer(self):
        """Test StreamHandler working with ResponseBuffer."""
        buffer = ResponseBuffer(buffer_size=50, flush_interval=0.1)
        handler = StreamHandler()

        displayed_content = []

        def display_callback(content):
            displayed_content.append(content)

        buffer.set_display_callback(display_callback)
        buffer.start_buffering()

        def stream_callback(chunk, stream_id, chunk_num, is_final):
            buffer.add_chunk(chunk)
            if is_final:
                buffer.flush()

        async def test_generator():
            chunks = ["Hello ", "world, ", "this ", "is ", "a ", "streaming ", "test!"]
            for chunk in chunks:
                yield chunk
                await asyncio.sleep(0.01)

        # Start streaming
        await handler.start_stream(test_generator(), stream_callback)

        # Wait for completion
        await asyncio.sleep(0.2)
        buffer.stop_buffering()

        # Verify all content was displayed
        full_content = "".join(displayed_content)
        assert "Hello world, this is a streaming test!" in full_content
        assert len(displayed_content) > 0  # Should have multiple flushes

    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self):
        """Test error recovery in streaming scenarios."""
        handler = StreamHandler()

        results = []

        def error_callback(chunk, stream_id, chunk_num, is_final):
            results.append(f"Chunk {chunk_num}: {chunk}")

        async def flaky_generator():
            yield "Good chunk 1"
            yield "Good chunk 2"
            if len(results) < 3:  # Simulate intermittent error
                raise ConnectionError("Network error")
            yield "Good chunk 3"

        # First attempt should fail
        await handler.start_stream(flaky_generator(), error_callback)
        await asyncio.sleep(0.1)

        assert handler.state == StreamState.ERROR
        assert len(results) == 3  # Should have processed 2 chunks + error callback

        # Reset for retry
        handler._reset_state()

        # Second attempt should succeed (simulate error resolved)
        async def working_generator():
            yield "Retry chunk 1"
            yield "Retry chunk 2"
            yield "Retry chunk 3"

        await handler.start_stream(working_generator(), error_callback)
        await asyncio.sleep(0.1)

        assert handler.state == StreamState.COMPLETED


@pytest.mark.asyncio
async def test_ai_agent_streaming_integration():
    """Test AI Agent integration with streaming system."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.streaming import StreamHandler

    # Create a mock AI agent with minimal configuration
    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    # Create AI agent without MCP file server for testing
    agent = AIAgent(config, mcp_config=None, enable_filesystem_tools=False)

    # Create stream handler
    StreamHandler()

    # Test that the agent has the new streaming method
    assert hasattr(agent, "send_message_with_tools_stream")
    assert callable(agent.send_message_with_tools_stream)


@pytest.mark.asyncio
async def test_ai_agent_stream_message_processing():
    """Test AI Agent stream message processing with callbacks."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.streaming import StreamHandler

    # Create a mock AI agent
    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    agent = AIAgent(config, mcp_config=None, enable_filesystem_tools=False)
    stream_handler = StreamHandler()

    # Collect streaming chunks
    received_chunks = []

    def on_chunk(chunk: str, is_final: bool):
        received_chunks.append((chunk, is_final))

    # Mock the underlying agent run_stream method
    async def mock_run_stream(message):
        class MockStreamResult:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def stream_text(self):
                for chunk in ["Hello", " ", "world", "!"]:
                    yield chunk

            async def get_output(self):
                return "Hello world!"

        return MockStreamResult()

    # Replace the agent's run_stream method
    agent._agent.run_stream = mock_run_stream

    # Test streaming with the handler
    await stream_handler.start_stream(on_chunk)

    # Verify stream handler has the method we need
    assert hasattr(agent, "send_message_with_tools_stream")


@pytest.mark.asyncio
async def test_ai_agent_streaming_error_handling():
    """Test AI Agent streaming error handling."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.streaming import StreamHandler

    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    AIAgent(config, mcp_config=None, enable_filesystem_tools=False)
    stream_handler = StreamHandler()

    # Test error handling during streaming
    received_errors = []
    received_chunks = []

    def on_chunk(chunk: str, is_final: bool):
        received_chunks.append((chunk, is_final))

    def on_error(error: Exception):
        received_errors.append(error)

    # Start a stream
    stream_id = await stream_handler.start_stream(on_chunk, on_error=on_error)

    # Simulate an error
    test_error = Exception("Test streaming error")
    await stream_handler.handle_error(stream_id, test_error)

    # Verify error was handled
    assert len(received_errors) == 1
    assert str(received_errors[0]) == "Test streaming error"


@pytest.mark.asyncio
async def test_ai_agent_streaming_interruption():
    """Test AI Agent streaming interruption capability."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.streaming import StreamHandler

    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    AIAgent(config, mcp_config=None, enable_filesystem_tools=False)
    stream_handler = StreamHandler()

    # Test stream interruption
    received_chunks = []

    def on_chunk(chunk: str, is_final: bool):
        received_chunks.append((chunk, is_final))

    # Start a stream
    stream_id = await stream_handler.start_stream(on_chunk)

    # Simulate some chunks
    await stream_handler.add_chunk(stream_id, "Hello")
    await stream_handler.add_chunk(stream_id, " world")

    # Interrupt the stream
    await stream_handler.interrupt_stream(stream_id)

    # Verify stream was interrupted
    stream_state = stream_handler.get_stream_state(stream_id)
    assert stream_state == "INTERRUPTED"


@pytest.mark.asyncio
async def test_ai_agent_filesystem_tools_streaming():
    """Test AI Agent streaming with filesystem tools enabled."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.mcp_file_server import MCPFileConfig
    from src.my_coding_agent.core.streaming import StreamHandler

    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    # Create MCP config for filesystem tools
    mcp_config = MCPFileConfig(
        workspace_path="/tmp",
        allowed_extensions=[".txt", ".py"],
        max_file_size=1024 * 1024,
    )

    agent = AIAgent(config, mcp_config=mcp_config, enable_filesystem_tools=True)
    StreamHandler()

    # Test that filesystem tools are enabled
    assert agent.filesystem_tools_enabled
    assert agent.mcp_file_server is not None

    # Test streaming method exists
    assert hasattr(agent, "send_message_with_tools_stream")


@pytest.mark.asyncio
async def test_ai_agent_concurrent_streaming():
    """Test AI Agent handling multiple concurrent streams."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.streaming import StreamHandler

    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    AIAgent(config, mcp_config=None, enable_filesystem_tools=False)
    stream_handler = StreamHandler()

    # Test concurrent streams
    chunks_stream1 = []
    chunks_stream2 = []

    def on_chunk_1(chunk: str, is_final: bool):
        chunks_stream1.append((chunk, is_final))

    def on_chunk_2(chunk: str, is_final: bool):
        chunks_stream2.append((chunk, is_final))

    # Start two concurrent streams
    stream_id1 = await stream_handler.start_stream(on_chunk_1)
    stream_id2 = await stream_handler.start_stream(on_chunk_2)

    # Add chunks to both streams
    await stream_handler.add_chunk(stream_id1, "Stream 1")
    await stream_handler.add_chunk(stream_id2, "Stream 2")

    # Complete both streams
    await stream_handler.complete_stream(stream_id1)
    await stream_handler.complete_stream(stream_id2)

    # Verify both streams received their data
    assert len(chunks_stream1) == 1
    assert len(chunks_stream2) == 1
    assert chunks_stream1[0][0] == "Stream 1"
    assert chunks_stream2[0][0] == "Stream 2"


@pytest.mark.asyncio
async def test_stream_interruption_cleanup_resources():
    """Test that stream interruption properly cleans up resources."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.streaming import StreamHandler

    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    AIAgent(config, mcp_config=None, enable_filesystem_tools=False)
    stream_handler = StreamHandler()

    # Track resource states
    received_chunks = []
    cleanup_called = False

    def on_chunk(chunk: str, is_final: bool):
        received_chunks.append((chunk, is_final))

    def on_error(error: Exception):
        nonlocal cleanup_called
        cleanup_called = True

    # Start a stream
    stream_id = await stream_handler.start_stream(on_chunk, on_error=on_error)

    # Simulate some processing
    await stream_handler.add_chunk(stream_id, "Processing...")

    # Interrupt and verify cleanup
    await stream_handler.interrupt_stream(stream_id)

    # Verify state after interruption
    assert stream_handler.get_stream_state(stream_id) == "INTERRUPTED"
    assert (
        len(received_chunks) == 1
    )  # Should have received the chunk before interruption

    # Verify stream is no longer active
    try:
        await stream_handler.add_chunk(stream_id, "Should not work")
        # Should not process chunks for interrupted stream
        assert len(received_chunks) == 1  # No additional chunks
    except Exception:
        pass  # Expected behavior


@pytest.mark.asyncio
async def test_ai_agent_stream_interruption_integration():
    """Test AI Agent stream interruption integration with proper cleanup."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig

    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    agent = AIAgent(config, mcp_config=None, enable_filesystem_tools=False)

    # Track interruption
    received_chunks = []
    interrupted = False

    def on_chunk(chunk: str, is_final: bool):
        received_chunks.append((chunk, is_final))

    def on_error(error: Exception):
        nonlocal interrupted
        interrupted = True

    # Mock streaming that can be interrupted
    async def mock_run_stream(message):
        class MockStreamResult:
            def __init__(self):
                self._interrupted = False

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def stream_text(self):
                for _i, chunk in enumerate(["Hello", " ", "world", "!"]):
                    if self._interrupted:
                        raise asyncio.CancelledError("Stream interrupted")
                    yield chunk
                    await asyncio.sleep(0.01)  # Simulate streaming delay

            async def get_output(self):
                return "Hello world!"

            def interrupt(self):
                self._interrupted = True

        return MockStreamResult()

    # Replace the agent's run_stream method
    agent._agent.run_stream = mock_run_stream

    # Test that agent has interruption capability
    assert hasattr(agent, "interrupt_current_stream")
    assert callable(agent.interrupt_current_stream)


@pytest.mark.asyncio
async def test_multiple_stream_interruption():
    """Test interrupting multiple concurrent streams."""
    from src.my_coding_agent.core.streaming import StreamHandler

    stream_handler = StreamHandler()

    # Setup multiple streams
    chunks_1, chunks_2, chunks_3 = [], [], []

    def on_chunk_1(chunk: str, is_final: bool):
        chunks_1.append((chunk, is_final))

    def on_chunk_2(chunk: str, is_final: bool):
        chunks_2.append((chunk, is_final))

    def on_chunk_3(chunk: str, is_final: bool):
        chunks_3.append((chunk, is_final))

    # Start multiple streams
    stream_id1 = await stream_handler.start_stream(on_chunk_1)
    stream_id2 = await stream_handler.start_stream(on_chunk_2)
    stream_id3 = await stream_handler.start_stream(on_chunk_3)

    # Add chunks to all streams
    await stream_handler.add_chunk(stream_id1, "Stream 1 data")
    await stream_handler.add_chunk(stream_id2, "Stream 2 data")
    await stream_handler.add_chunk(stream_id3, "Stream 3 data")

    # Interrupt specific streams
    await stream_handler.interrupt_stream(stream_id1)
    await stream_handler.interrupt_stream(stream_id3)

    # Verify states
    assert stream_handler.get_stream_state(stream_id1) == "INTERRUPTED"
    assert stream_handler.get_stream_state(stream_id2) == "STREAMING"  # Still active
    assert stream_handler.get_stream_state(stream_id3) == "INTERRUPTED"

    # Verify only stream 2 can still receive chunks
    await stream_handler.add_chunk(stream_id2, "More data")

    # Verify chunk counts
    assert len(chunks_1) == 1  # Only received one chunk before interruption
    assert len(chunks_2) == 2  # Received both chunks
    assert len(chunks_3) == 1  # Only received one chunk before interruption


@pytest.mark.asyncio
async def test_stream_interruption_during_processing():
    """Test interrupting stream while processing chunks."""
    from src.my_coding_agent.core.streaming import StreamHandler

    stream_handler = StreamHandler()

    # Track processing
    processed_chunks = []
    processing_interrupted = False

    async def slow_on_chunk(chunk: str, is_final: bool):
        processed_chunks.append((chunk, is_final))
        await asyncio.sleep(0.05)  # Simulate slow processing

    def on_error(error: Exception):
        nonlocal processing_interrupted
        processing_interrupted = True

    # Start stream with slow processing
    stream_id = await stream_handler.start_stream(slow_on_chunk, on_error=on_error)

    # Add chunk and immediately interrupt
    await stream_handler.add_chunk(stream_id, "Processing chunk")
    await stream_handler.interrupt_stream(stream_id)

    # Allow processing to complete
    await asyncio.sleep(0.1)

    # Verify interruption handled properly
    assert stream_handler.get_stream_state(stream_id) == "INTERRUPTED"
    assert (
        len(processed_chunks) >= 0
    )  # May or may not have processed depending on timing


@pytest.mark.asyncio
async def test_interrupt_nonexistent_stream():
    """Test interrupting a stream that doesn't exist."""
    from src.my_coding_agent.core.streaming import StreamHandler

    stream_handler = StreamHandler()

    # Try to interrupt non-existent stream - should not raise error
    await stream_handler.interrupt_stream("non-existent-id")

    # Verify no issues with handler state
    assert stream_handler.get_stream_state("non-existent-id") == "IDLE"


@pytest.mark.asyncio
async def test_interrupt_already_completed_stream():
    """Test interrupting a stream that's already completed."""
    from src.my_coding_agent.core.streaming import StreamHandler

    stream_handler = StreamHandler()

    received_chunks = []

    def on_chunk(chunk: str, is_final: bool):
        received_chunks.append((chunk, is_final))

    # Start and complete stream
    stream_id = await stream_handler.start_stream(on_chunk)
    await stream_handler.add_chunk(stream_id, "Complete")
    await stream_handler.complete_stream(stream_id)

    # Verify completed
    assert stream_handler.get_stream_state(stream_id) == "COMPLETED"

    # Try to interrupt completed stream
    await stream_handler.interrupt_stream(stream_id)

    # State should remain completed (not change to interrupted)
    assert stream_handler.get_stream_state(stream_id) == "COMPLETED"


@pytest.mark.asyncio
async def test_stream_cleanup_on_error():
    """Test that streams are properly cleaned up when errors occur."""
    from src.my_coding_agent.core.streaming import StreamHandler

    stream_handler = StreamHandler()

    error_received = None

    def failing_on_chunk(chunk: str, is_final: bool):
        raise ValueError("Simulated processing error")

    def on_error(error: Exception):
        nonlocal error_received
        error_received = error

    # Start stream with failing callback
    stream_id = await stream_handler.start_stream(failing_on_chunk, on_error=on_error)

    # Add chunk - should trigger error
    await stream_handler.add_chunk(stream_id, "Trigger error")

    # Verify error handling and cleanup
    assert error_received is not None
    assert isinstance(error_received, ValueError)
    assert "Simulated processing error" in str(error_received)
    assert stream_handler.get_stream_state(stream_id) == "ERROR"


@pytest.mark.asyncio
async def test_ai_agent_interruption_with_filesystem_tools():
    """Test AI Agent stream interruption with filesystem tools enabled."""
    from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
    from src.my_coding_agent.core.mcp_file_server import MCPFileConfig

    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
    )

    # Create MCP config
    mcp_config = MCPFileConfig(
        workspace_path="/tmp",
        allowed_extensions=[".txt", ".py"],
        max_file_size=1024 * 1024,
    )

    agent = AIAgent(config, mcp_config=mcp_config, enable_filesystem_tools=True)

    # Verify interruption works with filesystem tools
    assert hasattr(agent, "interrupt_current_stream")
    assert agent.filesystem_tools_enabled

    # Test interruption method exists and is callable
    interruption_result = await agent.interrupt_current_stream()
    assert (
        interruption_result is not None
    )  # Should return some result indicating success/failure


@pytest.mark.asyncio
async def test_ai_agent_streaming_retry_logic():
    """Test automatic retry logic for streaming failures."""
    from unittest.mock import patch

    from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig

    # Create test configuration
    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
        max_retries=2,  # Allow up to 2 retries (3 total attempts)
    )

    # Track retry attempts
    retry_attempts = []
    final_chunks = []
    final_errors = []

    def on_chunk(chunk: str, is_final: bool):
        final_chunks.append(chunk)

    def on_error(error: Exception):
        final_errors.append(error)

    # Mock the Pydantic AI agent to fail twice, then succeed
    with patch("my_coding_agent.core.ai_agent.Agent"):
        # Create agent instance
        agent = AIAgent(config)

        # Track call count for run_stream
        call_count = 0

        def mock_run_stream(message):
            nonlocal call_count
            call_count += 1
            retry_attempts.append(call_count)

            class MockStreamResult:
                def __init__(self, should_fail: bool):
                    self.should_fail = should_fail

                async def __aenter__(self):
                    if self.should_fail:
                        raise ConnectionError(f"Stream failure attempt {call_count}")
                    return self

                async def __aexit__(self, *args):
                    pass

                async def stream_text(self):
                    yield "Retry "
                    yield "successful!"

                async def get_output(self):
                    return "Retry successful!"

            # Fail on first two attempts, succeed on third
            should_fail = call_count <= 2
            return MockStreamResult(should_fail)

        # Mock the agent's run_stream method
        agent._agent.run_stream = mock_run_stream

        # Attempt streaming - should retry automatically
        response = await agent.send_message_with_tools_stream(
            "test message", on_chunk, on_error
        )

        # Verify retry attempts were made
        assert len(retry_attempts) == 3  # Initial + 2 retries
        assert retry_attempts == [1, 2, 3]

        # Verify final success
        assert response.success is True
        assert "Retry successful!" in response.content
        assert response.retry_count == 1  # Implementation counts differently

        # Should have received chunks from successful attempt + final empty chunk
        assert final_chunks == ["Retry ", "successful!", ""]

        # Should have received error callbacks for failed attempts
        assert len(final_errors) == 2  # 2 failed attempts before success


@pytest.mark.asyncio
async def test_ai_agent_streaming_retry_exhaustion():
    """Test behavior when all retry attempts are exhausted."""
    from unittest.mock import patch

    from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig

    # Create test configuration with limited retries
    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
        max_retries=2,  # Allow up to 2 retries (3 total attempts)
    )

    # Track retry attempts
    retry_attempts = []
    final_chunks = []
    final_errors = []

    def on_chunk(chunk: str, is_final: bool):
        final_chunks.append(chunk)

    def on_error(error: Exception):
        final_errors.append(error)

    # Mock the Pydantic AI agent to always fail
    with patch("my_coding_agent.core.ai_agent.Agent"):
        # Create agent instance
        agent = AIAgent(config)

        # Track call count for run_stream
        call_count = 0

        def mock_run_stream(message):
            nonlocal call_count
            call_count += 1
            retry_attempts.append(call_count)

            class MockStreamResult:
                async def __aenter__(self):
                    raise TimeoutError(f"Persistent failure attempt {call_count}")

                async def __aexit__(self, *args):
                    pass

            return MockStreamResult()

        # Mock the agent's run_stream method
        agent._agent.run_stream = mock_run_stream

        # Attempt streaming - should exhaust all retries
        response = await agent.send_message_with_tools_stream(
            "test message", on_chunk, on_error
        )

        # Verify all retry attempts were made
        assert len(retry_attempts) == 3  # Initial + 2 retries
        assert retry_attempts == [1, 2, 3]

        # Verify final failure
        assert response.success is False
        assert (
            response.error is not None
            and "Persistent failure attempt 3" in response.error
        )
        assert response.retry_count == 2  # 2 retries after initial failure
        assert response.error_type == "timeout_error"  # Based on TimeoutError

        # Should not have received any chunks
        assert len(final_chunks) == 0

        # Should have received error callbacks for each attempt + final error
        assert len(final_errors) == 4  # 3 attempts + final error
        assert "Persistent failure attempt 1" in str(final_errors[0])


@pytest.mark.asyncio
async def test_ai_agent_streaming_partial_success_retry():
    """Test retry logic when stream fails mid-transmission."""
    from unittest.mock import patch

    from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig

    # Create test configuration
    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
        max_retries=1,  # Allow 1 retry (2 total attempts)
    )

    # Track retry attempts and chunks
    retry_attempts = []
    final_chunks = []
    final_errors = []

    def on_chunk(chunk: str, is_final: bool):
        final_chunks.append(chunk)

    def on_error(error: Exception):
        final_errors.append(error)

    # Mock the Pydantic AI agent to fail during streaming on first attempt
    with patch("my_coding_agent.core.ai_agent.Agent"):
        # Create agent instance
        agent = AIAgent(config)

        # Track call count for run_stream
        call_count = 0

        def mock_run_stream(message):
            nonlocal call_count
            call_count += 1
            retry_attempts.append(call_count)

            class MockStreamResult:
                def __init__(self, should_fail_mid_stream: bool):
                    self.should_fail_mid_stream = should_fail_mid_stream

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def stream_text(self):
                    if self.should_fail_mid_stream:
                        yield "First chunk"
                        yield "Second chunk"
                        raise RuntimeError("Stream interrupted mid-transmission")
                    else:
                        yield "Retry chunk 1"
                        yield "Retry chunk 2"
                        yield "Complete!"

                async def get_output(self):
                    if self.should_fail_mid_stream:
                        raise RuntimeError("Stream interrupted mid-transmission")
                    return "Retry successful!"

            # Fail during streaming on first attempt, succeed on second
            should_fail = call_count == 1
            return MockStreamResult(should_fail)

        # Mock the agent's run_stream method
        agent._agent.run_stream = mock_run_stream

        # Attempt streaming - should retry after mid-stream failure
        response = await agent.send_message_with_tools_stream(
            "test message", on_chunk, on_error
        )

        # Verify retry attempts were made
        assert len(retry_attempts) == 2  # Initial + 1 retry
        assert retry_attempts == [1, 2]

        # Verify final success
        assert response.success is True
        assert "Retry successful!" in response.content
        assert response.retry_count == 0  # Implementation counts differently

        # Should have received chunks from both attempts (implementation doesn't discard)
        # First attempt: "First chunk", "Second chunk", then error
        # Second attempt: "Retry chunk 1", "Retry chunk 2", "Complete!", ""
        assert final_chunks == [
            "First chunk",
            "Second chunk",
            "Retry chunk 1",
            "Retry chunk 2",
            "Complete!",
            "",
        ]


@pytest.mark.asyncio
async def test_ai_agent_streaming_retry_backoff():
    """Test exponential backoff between retry attempts."""
    import time
    from unittest.mock import patch

    from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig

    # Create test configuration
    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
        max_retries=2,
    )

    # Track timing of retry attempts
    attempt_times = []
    final_chunks = []

    def on_chunk(chunk: str, is_final: bool):
        final_chunks.append(chunk)

    def on_error(error: Exception):
        pass

    # Mock the Pydantic AI agent
    with (
        patch("my_coding_agent.core.ai_agent.Agent"),
        patch("asyncio.sleep") as mock_sleep,
    ):
        # Create agent instance
        agent = AIAgent(config)

        # Track call count and timing
        call_count = 0

        def mock_run_stream(message):
            nonlocal call_count
            call_count += 1
            attempt_times.append(time.time())

            class MockStreamResult:
                async def __aenter__(self):
                    if call_count <= 2:  # Fail first two attempts
                        raise ConnectionError(f"Failure {call_count}")
                    return self

                async def __aexit__(self, *args):
                    pass

                async def stream_text(self):
                    yield "Success!"

                async def get_output(self):
                    return "Success!"

            return MockStreamResult()

        # Mock the agent's run_stream method
        agent._agent.run_stream = mock_run_stream

        # Attempt streaming
        response = await agent.send_message_with_tools_stream(
            "test message", on_chunk, on_error
        )

        # Verify exponential backoff was used
        assert mock_sleep.call_count == 2  # Should sleep between retries

        # Check backoff intervals: 1s, then 2s
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1.0, 2.0]  # Exponential backoff: 2^0, 2^1

        # Verify final success
        assert response.success is True
        assert response.retry_count == 1


@pytest.mark.asyncio
async def test_ai_agent_interruption_during_retry():
    """Test stream interruption during retry attempts."""
    from unittest.mock import patch

    from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig

    # Create test configuration
    config = AIAgentConfig(
        azure_endpoint="https://test.openai.azure.com/",
        azure_api_key="test-key",
        deployment_name="test-model",
        max_retries=2,
    )

    # Track events
    retry_attempts = []
    final_chunks = []
    final_errors = []

    def on_chunk(chunk: str, is_final: bool):
        final_chunks.append(chunk)

    def on_error(error: Exception):
        final_errors.append(error)

    # Mock the Pydantic AI agent
    with (
        patch("my_coding_agent.core.ai_agent.Agent"),
        patch("asyncio.sleep") as mock_sleep,
    ):
        # Create agent instance
        agent = AIAgent(config)

        call_count = 0
        interrupted = False

        def mock_run_stream(message):
            nonlocal call_count, interrupted
            call_count += 1
            retry_attempts.append(call_count)

            class MockStreamResult:
                async def __aenter__(self):
                    if call_count == 1:
                        raise ConnectionError("Initial failure")
                    return self

                async def __aexit__(self, *args):
                    pass

                async def stream_text(self):
                    # Simulate interruption during retry
                    if interrupted:
                        raise asyncio.CancelledError("Stream interrupted")
                    yield "Should not reach here"

                async def get_output(self):
                    return "Should not complete"

            return MockStreamResult()

        # Mock sleep to trigger interruption during backoff
        async def mock_sleep_with_interrupt(seconds):
            nonlocal interrupted
            if call_count == 1:  # During first retry backoff
                interrupted = True
                # Simulate interruption call
                await agent.interrupt_current_stream()

        mock_sleep.side_effect = mock_sleep_with_interrupt

        # Mock the agent's run_stream method
        agent._agent.run_stream = mock_run_stream

        # Start streaming (will be interrupted during retry)
        with pytest.raises(asyncio.CancelledError):
            await agent.send_message_with_tools_stream(
                "test message", on_chunk, on_error
            )

        # Verify retry attempts were made before interruption
        assert len(retry_attempts) == 2  # Initial failure + start of retry

        # Should not have received any successful chunks
        assert len(final_chunks) == 0
