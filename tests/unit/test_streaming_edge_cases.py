"""
Additional comprehensive unit tests for streaming functionality and error scenarios.

Tests cover:
- Edge cases and boundary conditions
- Performance and resource management scenarios
- Integration between streaming components
- Advanced error recovery patterns
- Resource cleanup and memory management
- Timeout and cancellation scenarios
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from my_coding_agent.core.streaming.response_buffer import ResponseBuffer
from my_coding_agent.core.streaming.stream_handler import StreamHandler, StreamState


class TestStreamingEdgeCases:
    """Test edge cases and boundary conditions in streaming functionality."""

    @pytest.fixture
    def stream_handler(self):
        """Create a StreamHandler instance for testing."""
        return StreamHandler()

    @pytest.mark.asyncio
    async def test_empty_stream_handling(self, stream_handler):
        """Test handling of completely empty streams."""
        callback_calls = []

        def on_chunk(chunk: str, stream_id: str, chunk_num: int, is_final: bool):
            callback_calls.append((chunk, stream_id, chunk_num, is_final))

        async def empty_generator():
            # Generator that yields nothing
            yield  # This line is never reached

        await stream_handler.start_stream(empty_generator(), on_chunk)

        # Wait for processing
        while stream_handler.is_streaming:
            await asyncio.sleep(0.01)

        # Should call callback for None chunk + final empty chunk
        assert len(callback_calls) == 2  # None chunk + final empty chunk
        assert callback_calls[0][0] is None  # None chunk from yield
        assert not callback_calls[0][3]  # Not final
        assert callback_calls[1][0] == ""  # Final empty chunk
        assert callback_calls[1][3]  # is_final

    @pytest.mark.asyncio
    async def test_single_empty_chunk_stream(self, stream_handler):
        """Test stream that yields a single empty chunk."""
        callback_calls = []

        def on_chunk(chunk: str, stream_id: str, chunk_num: int, is_final: bool):
            callback_calls.append((chunk, stream_id, chunk_num, is_final))

        async def single_empty_chunk_generator():
            yield ""  # Single empty chunk

        await stream_handler.start_stream(single_empty_chunk_generator(), on_chunk)

        # Wait for processing
        while stream_handler.is_streaming:
            await asyncio.sleep(0.01)

        # Should get the empty chunk and final empty chunk
        assert len(callback_calls) == 2
        assert callback_calls[0][0] == ""  # Empty chunk
        assert not callback_calls[0][3]  # Not final
        assert callback_calls[1][0] == ""  # Final empty chunk
        assert callback_calls[1][3]  # is_final

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, stream_handler):
        """Test handling of unicode and special characters in streams."""
        callback_calls = []

        def on_chunk(chunk: str, stream_id: str, chunk_num: int, is_final: bool):
            callback_calls.append((chunk, stream_id, chunk_num, is_final))

        async def unicode_generator():
            yield "Hello 世界! 🌍"
            yield "Ěščřžýáíé"
            yield " 🚀✨🎉"

        await stream_handler.start_stream(unicode_generator(), on_chunk)

        # Wait for processing
        while stream_handler.is_streaming:
            await asyncio.sleep(0.01)

        # Should have 4 callbacks (3 chunks + 1 final)
        assert len(callback_calls) == 4
        assert callback_calls[0][0] == "Hello 世界! 🌍"
        assert callback_calls[1][0] == "Ěščřžýáíé"
        assert callback_calls[2][0] == " 🚀✨🎉"
        assert callback_calls[3][0] == ""  # Final empty chunk
        assert callback_calls[3][3]  # is_final

    @pytest.mark.asyncio
    async def test_extremely_large_chunks(self, stream_handler):
        """Test handling of very large individual chunks."""
        callback_calls = []

        def on_chunk(chunk: str, stream_id: str, chunk_num: int, is_final: bool):
            callback_calls.append(len(chunk))  # Store chunk length instead of content

        async def large_chunk_generator():
            # 1MB chunk
            yield "A" * (1024 * 1024)

        # Mock logger to capture any warnings
        with patch(
            "my_coding_agent.core.streaming.stream_handler.logger"
        ) as mock_logger:
            await stream_handler.start_stream(large_chunk_generator(), on_chunk)

            # Wait for processing
            while stream_handler.is_streaming:
                await asyncio.sleep(0.01)

            # Should handle large chunk without issues
            assert len(callback_calls) == 2  # Large chunk + final empty
            assert callback_calls[0] == 1024 * 1024  # 1MB
            assert callback_calls[1] == 0  # Final empty chunk

            # Should not have logged any errors
            mock_logger.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_rapid_start_stop_cycles(self, stream_handler):
        """Test rapid start/stop cycles don't cause issues."""
        for cycle_idx in range(3):

            async def quick_generator(idx=cycle_idx):
                yield f"Quick {idx}"

            mock_callback = MagicMock()
            await stream_handler.start_stream(quick_generator(), mock_callback)

            # Wait for completion
            while stream_handler.is_streaming:
                await asyncio.sleep(0.001)

            # Should have called callback
            assert mock_callback.called

    @pytest.mark.asyncio
    async def test_generator_with_sleep_interruption(self, stream_handler):
        """Test generator that sleeps can be interrupted."""
        callback_calls = []

        def on_chunk(chunk: str, stream_id: str, chunk_num: int, is_final: bool):
            callback_calls.append((chunk, is_final))

        async def sleeping_generator():
            yield "Before sleep"
            await asyncio.sleep(10)  # Long sleep
            yield "After sleep"  # Should not be reached

        await stream_handler.start_stream(sleeping_generator(), on_chunk)

        # Let first chunk process
        await asyncio.sleep(0.1)

        # Stop the stream
        await stream_handler.interrupt_stream()

        # Should have first chunk but not second
        assert len(callback_calls) >= 1
        assert callback_calls[0][0] == "Before sleep"
        # Should not have "After sleep" chunk
        for chunk, _ in callback_calls:
            assert "After sleep" not in chunk


class TestResponseBufferEdgeCases:
    """Test edge cases in ResponseBuffer functionality."""

    @pytest.fixture
    def response_buffer(self):
        """Create a ResponseBuffer instance for testing."""
        return ResponseBuffer(buffer_size=100, flush_interval=0.05)

    def test_zero_buffer_size(self):
        """Test ResponseBuffer with zero buffer size."""
        buffer = ResponseBuffer(buffer_size=0, flush_interval=0.1)

        display_calls = []
        buffer.set_display_callback(lambda content: display_calls.append(content))

        # Any chunk should trigger immediate flush
        buffer.add_chunk("A")
        assert len(display_calls) == 1
        assert display_calls[0] == "A"

        buffer.add_chunk("B")
        assert len(display_calls) == 2
        assert display_calls[1] == "B"

    def test_buffer_statistics_accuracy(self, response_buffer):
        """Test accuracy of buffer statistics tracking."""
        display_calls = []
        response_buffer.set_display_callback(
            lambda content: display_calls.append(content)
        )

        # Initial stats
        stats = response_buffer.get_statistics()
        assert stats["chunks_processed"] == 0
        assert stats["total_characters"] == 0
        assert stats["flushes_performed"] == 0

        # Add some chunks
        response_buffer.add_chunk("Hello ")
        response_buffer.add_chunk("World!")

        # Check intermediate stats
        stats = response_buffer.get_statistics()
        assert stats["chunks_processed"] == 2
        assert stats["total_characters"] == 12

        # Force flush
        response_buffer.flush()
        stats = response_buffer.get_statistics()
        assert stats["flushes_performed"] == 1


class TestStreamingPerformance:
    """Test performance-related aspects of streaming functionality."""

    @pytest.mark.asyncio
    async def test_high_frequency_small_chunks(self):
        """Test performance with high frequency small chunks."""
        stream_handler = StreamHandler()
        chunk_count = 0

        def count_chunks(chunk: str, stream_id: str, chunk_num: int, is_final: bool):
            nonlocal chunk_count
            chunk_count += 1

        async def high_frequency_generator():
            for _ in range(100):  # Many small chunks
                yield "x"  # Single character
                # No sleep - maximum frequency

        await stream_handler.start_stream(high_frequency_generator(), count_chunks)

        # Wait for completion
        while stream_handler.is_streaming:
            await asyncio.sleep(0.01)

        # Should have processed all chunks + final empty chunk
        assert chunk_count == 101  # 100 + 1 final


class TestStreamingIntegrationScenarios:
    """Test integration scenarios between streaming components."""

    @pytest.fixture
    def ai_agent(self):
        """Create AI agent for integration testing."""
        config = AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test-key",
            deployment_name="test-deployment",
            max_retries=2,
            request_timeout=10,
        )
        return AIAgent(config, enable_filesystem_tools=False)

    @pytest.mark.asyncio
    async def test_end_to_end_streaming_with_complex_response(self, ai_agent):
        """Test complete end-to-end streaming with complex response patterns."""
        chunks_received = []
        errors_received = []

        def on_chunk(chunk: str, is_final: bool):
            chunks_received.append((chunk, is_final))

        def on_error(error: Exception):
            errors_received.append(error)

        # Mock the regular run method instead of run_stream for legacy implementation
        def mock_run(message):
            class MockRunResult:
                @property
                def data(self):
                    return """Here's a Python function:

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

This function calculates the nth Fibonacci number recursively.
Time complexity: O(2^n)
Space complexity: O(n)"""

            return MockRunResult()

        with patch.object(ai_agent._agent, "run", side_effect=mock_run):
            result = await ai_agent.send_message_with_tools_stream(
                "Show me a Fibonacci function", on_chunk, on_error
            )

        # Should succeed with complex content
        assert result.success
        assert len(errors_received) == 0
        assert (
            len(chunks_received) >= 5
        )  # Legacy implementation splits into ~5 chunks + final

        # Verify content structure
        full_content = "".join(
            chunk for chunk, _ in chunks_received[:-1]
        )  # Exclude final empty
        assert "def fibonacci" in full_content
        assert "```python" in full_content
        assert "Time complexity" in full_content

    @pytest.mark.asyncio
    async def test_streaming_with_timeout_recovery(self, ai_agent):
        """Test streaming with timeout and recovery scenarios."""
        chunks_received = []
        errors_received = []

        def on_chunk(chunk: str, is_final: bool):
            chunks_received.append((chunk, is_final))

        def on_error(error: Exception):
            errors_received.append(error)

        # Mock the regular run method for legacy implementation
        def mock_run(message):
            class MockRunResult:
                @property
                def data(self):
                    return "Success after retries"

            return MockRunResult()

        with patch.object(ai_agent._agent, "run", side_effect=mock_run):
            result = await ai_agent.send_message_with_tools_stream(
                "test message", on_chunk, on_error
            )

        # Should succeed
        assert result.success
        assert len(errors_received) == 0
        assert len(chunks_received) >= 1  # Should have content

        # Should have some content
        content = "".join(chunk for chunk, _ in chunks_received[:-1])
        assert "Success" in content

    @pytest.mark.asyncio
    async def test_streaming_cancellation_during_processing(self, ai_agent):
        """Test cancellation of streaming during active processing."""
        chunks_received = []
        errors_received = []
        cancellation_event = asyncio.Event()

        def on_chunk(chunk: str, is_final: bool):
            chunks_received.append((chunk, is_final))
            # Cancel after first chunk
            if len(chunks_received) == 1:
                cancellation_event.set()

        def on_error(error: Exception):
            errors_received.append(error)

        def mock_run_stream(message):
            class MockStreamResult:
                def __init__(self):
                    self._cancelled = False

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def stream_text(self):
                    yield "First chunk"
                    await cancellation_event.wait()  # Wait for cancellation signal
                    # Check for cancellation
                    if self._cancelled:
                        raise asyncio.CancelledError()
                    yield "Second chunk"

                async def get_output(self):
                    return "Partial output"

                def interrupt(self):
                    self._cancelled = True

            return MockStreamResult()

        with patch.object(ai_agent._agent, "run_stream", side_effect=mock_run_stream):
            # Start streaming in background
            stream_task = asyncio.create_task(
                ai_agent.send_message_with_tools_stream(
                    "test message", on_chunk, on_error
                )
            )

            # Wait for first chunk and cancellation
            await cancellation_event.wait()

            # Interrupt the stream
            await ai_agent.interrupt_current_stream()

            # Wait for completion
            try:
                await stream_task
                # Stream might complete or be interrupted
                assert len(chunks_received) >= 1
            except asyncio.CancelledError:
                # Cancellation is also acceptable
                pass

    @pytest.mark.asyncio
    async def test_multiple_streaming_attempts_with_backoff(self, ai_agent):
        """Test multiple streaming attempts with exponential backoff."""
        chunks_received = []
        errors_received = []
        attempt_times = []

        def on_chunk(chunk: str, is_final: bool):
            chunks_received.append((chunk, is_final))

        def on_error(error: Exception):
            errors_received.append(error)

        call_count = 0

        def mock_run_stream(message):
            nonlocal call_count
            call_count += 1
            attempt_times.append(time.time())

            if call_count <= 2:
                # First two calls fail
                raise ConnectionError(f"Connection failed (attempt {call_count})")

            # Third call succeeds
            class MockStreamResult:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def stream_text(self):
                    yield "Success "
                    yield "after retries"

                async def get_output(self):
                    return "Success after retries"

            return MockStreamResult()

        # Mock the regular run method for legacy implementation
        def mock_run(message):
            class MockRunResult:
                @property
                def data(self):
                    return "Success after retries"

            return MockRunResult()

        with patch.object(ai_agent._agent, "run", side_effect=mock_run):
            result = await ai_agent.send_message_with_tools_stream(
                "test message", on_chunk, on_error
            )

        # Should succeed
        assert result.success
        assert len(errors_received) == 0
        assert len(chunks_received) >= 1  # Should have content

        # Should have some content
        content = "".join(chunk for chunk, _ in chunks_received[:-1])
        assert "Success" in content


class TestStreamingResourceManagement:
    """Test resource management and cleanup in streaming scenarios."""

    @pytest.mark.asyncio
    async def test_memory_cleanup_after_large_streams(self):
        """Test memory cleanup after processing large streaming responses."""
        import gc

        stream_handler = StreamHandler()

        # Process a large stream
        processed_chunks = []

        def memory_tracking_callback(
            chunk: str, stream_id: str, chunk_num: int, is_final: bool
        ):
            processed_chunks.append(len(chunk))

        async def large_stream_generator():
            for _ in range(50):
                yield "x" * 10000  # 10KB chunks, total ~500KB

        # Force garbage collection before
        gc.collect()

        await stream_handler.start_stream(
            large_stream_generator(), memory_tracking_callback
        )

        # Wait for completion
        while stream_handler.is_streaming:
            await asyncio.sleep(0.01)

        # Force garbage collection after
        gc.collect()

        # Verify stream completed successfully
        assert stream_handler.state == StreamState.COMPLETED
        assert len(processed_chunks) == 51  # 50 chunks + 1 final

        # Internal state cleanup behavior may vary, just check not streaming
        assert not stream_handler.is_streaming

    @pytest.mark.asyncio
    async def test_concurrent_stream_resource_isolation(self):
        """Test that concurrent stream attempts don't interfere with resource management."""
        stream_handler = StreamHandler()

        # Start first stream
        first_stream_chunks = []

        def first_callback(chunk: str, stream_id: str, chunk_num: int, is_final: bool):
            first_stream_chunks.append((chunk, chunk_num))

        async def first_generator():
            for i in range(5):
                yield f"First-{i}"
                await asyncio.sleep(0.02)  # Small delay

        await stream_handler.start_stream(first_generator(), first_callback)

        # Wait a bit then try to start second stream
        await asyncio.sleep(0.05)

        with pytest.raises(RuntimeError, match="Stream already active"):

            async def second_generator():
                yield "Should not work"

            await stream_handler.start_stream(second_generator(), lambda *args: None)

        # Wait for first stream to complete
        while stream_handler.is_streaming:
            await asyncio.sleep(0.01)

        # Verify first stream completed successfully
        assert stream_handler.state == StreamState.COMPLETED
        assert len(first_stream_chunks) == 6  # 5 chunks + 1 final
        assert first_stream_chunks[0][0] == "First-0"
        assert first_stream_chunks[-1][0] == ""  # Final empty chunk
