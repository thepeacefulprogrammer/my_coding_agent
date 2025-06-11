"""
StreamHandler for managing chunk-by-chunk AI response streaming.

Provides:
- Asynchronous streaming of AI responses
- Stream state management and progress tracking
- Interruption capability with proper cleanup
- Error handling and recovery
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class StreamState(Enum):
    """Enumeration of possible stream states."""

    IDLE = "idle"
    STREAMING = "streaming"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class StreamHandler:
    """
    Manages chunk-by-chunk streaming of AI responses with state management.

    Features:
    - Asynchronous processing of response chunks
    - Stream interruption and cleanup
    - Progress tracking
    - Error handling with state management
    """

    def __init__(self):
        """Initialize the StreamHandler."""
        self.state = StreamState.IDLE
        self.current_stream_id: str | None = None
        self.total_chunks = 0
        self.processed_chunks = 0
        self.last_error: Exception | None = None
        self._stream_task: asyncio.Task | None = None
        self._interrupt_event = asyncio.Event()
        # New: Support for simple callback interface
        self._active_streams: dict[str, dict] = {}

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self.state == StreamState.STREAMING

    async def start_stream(
        self, chunk_generator_or_callback, callback_or_none=None, on_error=None
    ) -> str:
        """
        Start streaming - supports two interfaces:
        1. start_stream(chunk_generator, callback) - original interface
        2. start_stream(callback, on_error=error_callback) - simplified interface for AI Agent

        Args:
            chunk_generator_or_callback: Either async generator or callback function
            callback_or_none: Callback function if first arg is generator, None otherwise
            on_error: Error callback for simplified interface

        Returns:
            Unique stream ID for this streaming session

        Raises:
            RuntimeError: If a stream is already active (for original interface)
        """
        if callback_or_none is not None:
            # Original interface: start_stream(chunk_generator, callback)
            return await self._start_stream_with_generator(
                chunk_generator_or_callback, callback_or_none
            )
        else:
            # Simplified interface: start_stream(callback, on_error=error_callback)
            return await self._start_stream_with_callback(
                chunk_generator_or_callback, on_error
            )

    async def _start_stream_with_generator(
        self,
        chunk_generator: AsyncGenerator[str, None],
        callback: Callable[[str, str, int, bool], None],
    ) -> str:
        """Original streaming interface with async generator."""
        if self.is_streaming:
            raise RuntimeError(
                "Stream already active. Stop current stream before starting new one."
            )

        # Reset state and generate new stream ID
        self._reset_state()
        stream_id = str(uuid.uuid4())
        self.current_stream_id = stream_id
        self.state = StreamState.STREAMING

        # Start the streaming task
        self._stream_task = asyncio.create_task(
            self._process_stream(chunk_generator, callback, stream_id)
        )

        return stream_id

    async def _start_stream_with_callback(
        self,
        on_chunk: Callable[[str, bool], None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> str:
        """Simplified streaming interface for AI Agent integration."""
        stream_id = str(uuid.uuid4())

        self._active_streams[stream_id] = {
            "on_chunk": on_chunk,
            "on_error": on_error,
            "state": StreamState.STREAMING,
            "chunk_count": 0,
            "error": None,
        }

        # If this is the first stream, update global state
        if not self.current_stream_id:
            self.current_stream_id = stream_id
            self.state = StreamState.STREAMING

        return stream_id

    async def add_chunk(self, stream_id: str, chunk: str) -> None:
        """Add a chunk to the specified stream."""
        if stream_id not in self._active_streams:
            raise ValueError(f"Stream {stream_id} not found")

        stream_info = self._active_streams[stream_id]
        if stream_info["state"] != StreamState.STREAMING:
            return  # Stream no longer active

        stream_info["chunk_count"] += 1
        self.processed_chunks += 1

        # Call the callback (handle both sync and async callbacks)
        try:
            callback_result = stream_info["on_chunk"](chunk, False)  # Not final yet
            if hasattr(callback_result, "__await__"):
                await callback_result
        except Exception as e:
            logger.error(f"Error in chunk callback for stream {stream_id}: {e}")
            await self.handle_error(stream_id, e)

    async def complete_stream(self, stream_id: str) -> None:
        """Mark a stream as completed."""
        if stream_id not in self._active_streams:
            return

        stream_info = self._active_streams[stream_id]
        stream_info["state"] = StreamState.COMPLETED

        # Don't call final callback with empty chunk - just mark as completed
        # The last real chunk will have been marked as final

        # Update global state if this was the current stream
        if self.current_stream_id == stream_id:
            self.state = StreamState.COMPLETED
            self.total_chunks = stream_info["chunk_count"]

    async def handle_error(self, stream_id: str, error: Exception) -> None:
        """Handle an error for the specified stream."""
        if stream_id not in self._active_streams:
            return

        stream_info = self._active_streams[stream_id]
        stream_info["state"] = StreamState.ERROR
        stream_info["error"] = error

        # Call error callback if provided
        if stream_info["on_error"]:
            try:
                stream_info["on_error"](error)
            except Exception as callback_error:
                logger.error(
                    f"Error in error callback for stream {stream_id}: {callback_error}"
                )

        # Update global state if this was the current stream
        if self.current_stream_id == stream_id:
            self.state = StreamState.ERROR
            self.last_error = error

    async def interrupt_stream(self, stream_id: str | None = None) -> None:
        """
        Interrupt the specified stream or current stream gracefully.

        Args:
            stream_id: Stream to interrupt, or None for current stream
        """
        if stream_id is None:
            # Original interface - interrupt current stream
            if not self.is_streaming:
                return

            logger.info(f"Interrupting stream {self.current_stream_id}")
            self._interrupt_event.set()

            if self._stream_task:
                try:
                    await asyncio.wait_for(self._stream_task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(
                        "Stream task did not complete within timeout, cancelling"
                    )
                    self._stream_task.cancel()
                    try:
                        await self._stream_task
                    except asyncio.CancelledError:
                        pass

            self.state = StreamState.INTERRUPTED
        else:
            # New interface - interrupt specific stream
            if stream_id in self._active_streams:
                stream_info = self._active_streams[stream_id]

                # Don't interrupt streams that are already completed
                if stream_info["state"] == StreamState.COMPLETED:
                    return

                stream_info["state"] = StreamState.INTERRUPTED

                if self.current_stream_id == stream_id:
                    self.state = StreamState.INTERRUPTED

    def get_stream_state(self, stream_id: str | None = None) -> str:
        """
        Get the state of a specific stream or the current stream.

        Args:
            stream_id: Stream to check, or None for current stream

        Returns:
            Stream state as string
        """
        if stream_id is None:
            return self.state.value.upper()

        if stream_id in self._active_streams:
            return self._active_streams[stream_id]["state"].value.upper()

        return StreamState.IDLE.value.upper()

    def get_progress(self) -> float:
        """
        Get stream progress as a fraction between 0.0 and 1.0.

        Returns:
            Progress fraction, or 0.0 if no chunks processed
        """
        if self.total_chunks == 0:
            return 0.0
        return min(1.0, self.processed_chunks / self.total_chunks)

    def _reset_state(self) -> None:
        """Reset internal state for new stream."""
        self.state = StreamState.IDLE
        self.current_stream_id = None
        self.total_chunks = 0
        self.processed_chunks = 0
        self.last_error = None
        self._interrupt_event.clear()
        self._stream_task = None

    async def _process_stream(
        self,
        chunk_generator: AsyncGenerator[str, None],
        callback: Callable[[str, str, int, bool], None],
        stream_id: str,
    ) -> None:
        """
        Process chunks from the generator and handle them with comprehensive error handling.

        Enhanced with:
        - Callback error isolation
        - Circuit breaker pattern for repeated callback failures
        - Graceful degradation on errors
        - Memory pressure detection
        - Progressive backoff on failures

        Args:
            chunk_generator: Generator producing text chunks
            callback: Function to call for each chunk
            stream_id: Unique identifier for this stream
        """
        chunk_count = 0
        callback_failure_count = 0
        max_callback_failures = 3  # Circuit breaker threshold
        last_callback_error = None

        try:
            # Check for interruption before starting
            if self._interrupt_event.is_set():
                logger.info(f"Stream {stream_id} interrupted before processing")
                self.state = StreamState.INTERRUPTED
                return

            async for current_chunk in chunk_generator:
                # Check for interruption during processing
                if self._interrupt_event.is_set():
                    logger.info(f"Stream {stream_id} interrupted during processing")
                    self.state = StreamState.INTERRUPTED
                    return

                chunk_count += 1
                self.processed_chunks = chunk_count

                # Circuit breaker: stop calling callback if too many failures
                if callback_failure_count >= max_callback_failures:
                    logger.warning(
                        f"Stream {stream_id}: Circuit breaker open - too many callback failures ({callback_failure_count}). "
                        f"Continuing stream without callbacks. Last error: {last_callback_error}"
                    )
                    continue

                # Memory pressure detection
                try:
                    import sys

                    if sys.getsizeof(current_chunk) > 1024 * 1024:  # 1MB chunk
                        logger.warning(
                            f"Stream {stream_id}: Large chunk detected ({len(current_chunk)} chars), may cause memory pressure"
                        )
                        # Could implement chunk splitting here for graceful degradation

                except Exception as memory_check_error:
                    logger.debug(f"Memory check failed: {memory_check_error}")

                # Call callback with error isolation
                try:
                    # Handle both sync and async callbacks
                    if asyncio.iscoroutinefunction(callback):
                        await callback(current_chunk, stream_id, chunk_count, False)
                    else:
                        callback(current_chunk, stream_id, chunk_count, False)

                    # Reset failure count on successful callback
                    if callback_failure_count > 0:
                        logger.info(
                            f"Stream {stream_id}: Callback recovered after {callback_failure_count} failures"
                        )
                        callback_failure_count = 0
                        last_callback_error = None

                except Exception as callback_error:
                    callback_failure_count += 1
                    last_callback_error = callback_error

                    logger.error(
                        f"Stream {stream_id}: Callback failed for chunk {chunk_count} "
                        f"(failure {callback_failure_count}/{max_callback_failures}): {callback_error}"
                    )

                    # Implement progressive backoff for callback failures
                    if callback_failure_count < max_callback_failures:
                        backoff_time = min(
                            0.1 * (2 ** (callback_failure_count - 1)), 1.0
                        )  # Max 1 second
                        logger.debug(
                            f"Stream {stream_id}: Backing off {backoff_time}s after callback failure"
                        )
                        await asyncio.sleep(backoff_time)

                    # Continue processing even if callback fails (error isolation)
                    continue

            # Final callback (only if circuit breaker is not open)
            if callback_failure_count < max_callback_failures:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback("", stream_id, chunk_count, True)
                    else:
                        callback("", stream_id, chunk_count, True)
                except Exception as final_callback_error:
                    logger.error(
                        f"Stream {stream_id}: Final callback failed: {final_callback_error}"
                    )
                    # Don't fail the stream for final callback errors

            # Set completion state
            self.state = StreamState.COMPLETED
            self.total_chunks = chunk_count

            logger.debug(
                f"Stream {stream_id} completed successfully. "
                f"Processed {chunk_count} chunks with {callback_failure_count} callback failures"
            )

        except asyncio.CancelledError:
            logger.info(f"Stream {stream_id} was cancelled")
            self.state = StreamState.INTERRUPTED
            raise

        except Exception as e:
            # Handle stream-level errors with graceful degradation
            logger.error(f"Stream {stream_id} failed: {e}")
            self.state = StreamState.ERROR
            self.last_error = e

            # Attempt graceful cleanup
            try:
                # Try to notify about the error (but don't fail if this fails too)
                if callback_failure_count < max_callback_failures:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(
                            f"[Stream Error: {str(e)}]",
                            stream_id,
                            chunk_count + 1,
                            True,
                        )
                    else:
                        callback(
                            f"[Stream Error: {str(e)}]",
                            stream_id,
                            chunk_count + 1,
                            True,
                        )
            except Exception as cleanup_error:
                logger.debug(
                    f"Stream {stream_id}: Error cleanup callback failed: {cleanup_error}"
                )

            # Don't re-raise to prevent cascading errors in the calling code
            # The error state and last_error are available for inspection
