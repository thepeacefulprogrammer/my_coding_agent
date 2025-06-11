"""
ResponseBuffer for intelligent buffering and smooth text display.

Provides:
- Intelligent buffering based on size and time thresholds
- Word boundary detection for smooth display
- Automatic and manual flush capabilities
- Statistics tracking for buffer performance
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class ResponseBuffer:
    """
    Intelligent buffering system for smooth streaming text display.

    Features:
    - Size-based buffering with automatic flush
    - Time-based automatic flush
    - Word boundary detection
    - Performance statistics
    """

    def __init__(self, buffer_size: int = 100, flush_interval: float = 0.1):
        """
        Initialize the ResponseBuffer.

        Args:
            buffer_size: Maximum buffer size before automatic flush
            flush_interval: Time interval (seconds) for automatic flush
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.current_buffer = ""
        self.is_buffering = False

        # Statistics tracking
        self._chunks_processed = 0
        self._flushes_performed = 0
        self._total_characters = 0
        self._last_flush_time = time.time()

        # Callback and task management
        self._display_callback: Callable[[str], None] | None = None
        self._flush_task: asyncio.Task | None = None

        # Word boundary pattern for intelligent splitting
        self._word_boundary_pattern = re.compile(r"\s+")

    def set_display_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set the callback function for displaying buffered content.

        Args:
            callback: Function to call when flushing content
        """
        self._display_callback = callback

    def add_chunk(self, chunk: str) -> None:
        """
        Add a text chunk to the buffer with comprehensive error handling.

        Enhanced with:
        - Memory pressure detection and handling
        - Display callback error isolation
        - Automatic chunk size adaptation
        - Circuit breaker for repeated display failures

        Args:
            chunk: Text chunk to add to buffer
        """
        if not chunk:
            return

        # Memory pressure detection
        try:
            import sys

            chunk_size = sys.getsizeof(chunk)
            buffer_size = sys.getsizeof(self.current_buffer)

            # Adaptive behavior under memory pressure
            if chunk_size > 1024 * 1024:  # 1MB chunk
                logger.warning(
                    f"Large chunk detected ({chunk_size} bytes), implementing memory-safe handling"
                )
                # Split large chunks to prevent memory issues
                self._handle_large_chunk(chunk)
                return

            if buffer_size > 10 * 1024 * 1024:  # 10MB buffer
                logger.warning(
                    "Buffer getting large, forcing flush to prevent memory issues"
                )
                self.flush()

        except Exception as memory_check_error:
            logger.debug(f"Memory check failed: {memory_check_error}")

        self.current_buffer += chunk
        self._chunks_processed += 1
        self._total_characters += len(chunk)

        # Check if buffer exceeds size threshold
        if len(self.current_buffer) >= self.buffer_size:
            self.flush()

    def _handle_large_chunk(self, chunk: str) -> None:
        """
        Handle large chunks by splitting them into smaller pieces.

        Args:
            chunk: Large text chunk to split and process
        """
        max_chunk_size = self.buffer_size // 2  # Use half buffer size for safety

        for i in range(0, len(chunk), max_chunk_size):
            sub_chunk = chunk[i : i + max_chunk_size]

            # Use word boundary detection for better splitting
            if i + max_chunk_size < len(chunk):  # Not the last piece
                boundary_pos = self.find_word_boundary(sub_chunk, len(sub_chunk))
                if boundary_pos < len(sub_chunk):
                    # Adjust split to word boundary
                    actual_chunk = sub_chunk[:boundary_pos]
                    remaining = sub_chunk[boundary_pos:]

                    # Add the properly split chunk
                    self.current_buffer += actual_chunk
                    self._chunks_processed += 1
                    self._total_characters += len(actual_chunk)

                    # Check if we need to flush
                    if len(self.current_buffer) >= self.buffer_size:
                        self.flush()

                    # Put remaining back for next iteration
                    chunk = remaining + chunk[i + max_chunk_size :]
                    i = -max_chunk_size  # Reset counter since we're modifying chunk
                    continue

            # Regular processing for manageable chunks
            self.current_buffer += sub_chunk
            self._chunks_processed += 1
            self._total_characters += len(sub_chunk)

            if len(self.current_buffer) >= self.buffer_size:
                self.flush()

    def flush(self) -> None:
        """
        Manually flush the current buffer content with error handling and graceful degradation.

        Enhanced with:
        - Display callback error isolation
        - Circuit breaker pattern
        - Graceful degradation on failures
        """
        if not self.current_buffer:
            return

        # Circuit breaker for display callback failures
        if not hasattr(self, "_display_failure_count"):
            self._display_failure_count = 0
            self._max_display_failures = 5
            self._last_display_error = None

        if self._display_failure_count >= self._max_display_failures:
            logger.error(
                f"Display callback circuit breaker open - too many failures ({self._display_failure_count}). "
                f"Last error: {self._last_display_error}. Dropping content."
            )
            # Clear buffer to prevent memory buildup
            self.current_buffer = ""
            return

        if self._display_callback:
            try:
                # Attempt to display with error isolation
                self._display_callback(self.current_buffer)

                # Reset failure count on success
                if self._display_failure_count > 0:
                    logger.info(
                        f"Display callback recovered after {self._display_failure_count} failures"
                    )
                    self._display_failure_count = 0
                    self._last_display_error = None

            except MemoryError as mem_error:
                # Handle memory pressure specifically
                self._display_failure_count += 1
                self._last_display_error = mem_error
                logger.error(f"Memory error in display callback: {mem_error}")

                # Attempt graceful degradation - try with truncated content
                try:
                    truncated_content = (
                        self.current_buffer[: len(self.current_buffer) // 2]
                        + "\n[Content truncated due to memory pressure]"
                    )
                    self._display_callback(truncated_content)
                    logger.info("Successfully displayed truncated content")
                except Exception as truncate_error:
                    logger.error(
                        f"Failed to display truncated content: {truncate_error}"
                    )

            except Exception as display_error:
                # Handle other display errors
                self._display_failure_count += 1
                self._last_display_error = display_error
                logger.error(
                    f"Display callback failed (failure {self._display_failure_count}/{self._max_display_failures}): {display_error}"
                )

                # Don't return here - still clear the buffer to prevent buildup

        self.current_buffer = ""
        self._flushes_performed += 1
        self._last_flush_time = time.time()

        logger.debug(f"Buffer flushed. Total flushes: {self._flushes_performed}")

    def start_buffering(self) -> None:
        """
        Start automatic time-based buffering with enhanced error handling.

        Creates a background task that flushes buffer at regular intervals
        and handles errors gracefully.
        """
        if self.is_buffering:
            return

        self.is_buffering = True
        self._flush_task = asyncio.create_task(self._auto_flush_loop())
        logger.debug("Started automatic buffering with error handling")

    def stop_buffering(self) -> None:
        """
        Stop automatic buffering and flush any remaining content.
        """
        if not self.is_buffering:
            return

        self.is_buffering = False

        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None

        # Final flush
        self.flush()
        logger.debug("Stopped automatic buffering")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get buffer performance statistics.

        Returns:
            Dictionary with buffer statistics
        """
        return {
            "chunks_processed": self._chunks_processed,
            "flushes_performed": self._flushes_performed,
            "total_characters": self._total_characters,
            "current_buffer_size": len(self.current_buffer),
            "average_chunk_size": (
                self._total_characters / self._chunks_processed
                if self._chunks_processed > 0
                else 0
            ),
            "average_flush_size": (
                self._total_characters / self._flushes_performed
                if self._flushes_performed > 0
                else 0
            ),
        }

    def find_word_boundary(self, text: str, max_length: int) -> int:
        """
        Find the best word boundary position within max_length.

        Args:
            text: Text to analyze
            max_length: Maximum length to consider

        Returns:
            Position of word boundary, or max_length if none found
        """
        if len(text) <= max_length:
            return len(text)

        # Look for word boundaries (spaces, punctuation) working backwards
        for i in range(max_length, max(0, max_length - 20), -1):
            if i < len(text) and self._word_boundary_pattern.match(text[i : i + 1]):
                return i

        # If no word boundary found, return max_length
        return max_length

    async def _auto_flush_loop(self) -> None:
        """
        Background task for automatic time-based flushing with comprehensive error handling.

        Enhanced with:
        - Error isolation
        - Adaptive flush intervals
        - Memory pressure monitoring
        """
        consecutive_errors = 0
        max_consecutive_errors = 3
        base_flush_interval = self.flush_interval

        try:
            while self.is_buffering:
                try:
                    # Adaptive flush interval based on error count
                    current_interval = base_flush_interval * (
                        1 + consecutive_errors * 0.5
                    )
                    await asyncio.sleep(current_interval)

                    # Only flush if we have content and enough time has passed
                    if (
                        self.current_buffer
                        and time.time() - self._last_flush_time >= base_flush_interval
                    ):
                        # Memory pressure check before flush
                        try:
                            import sys

                            if (
                                sys.getsizeof(self.current_buffer) > 5 * 1024 * 1024
                            ):  # 5MB
                                logger.warning(
                                    "Large buffer detected during auto-flush, forcing immediate flush"
                                )
                        except Exception:
                            pass

                        self.flush()
                        consecutive_errors = 0  # Reset on successful flush

                except Exception as flush_error:
                    consecutive_errors += 1
                    logger.error(
                        f"Auto-flush error {consecutive_errors}/{max_consecutive_errors}: {flush_error}"
                    )

                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(
                            "Too many consecutive auto-flush errors, stopping auto-flush"
                        )
                        break

                    # Exponential backoff on errors
                    await asyncio.sleep(
                        min(base_flush_interval * (2**consecutive_errors), 10.0)
                    )

        except asyncio.CancelledError:
            logger.debug("Auto-flush loop cancelled")
            raise
        except Exception as loop_error:
            logger.error(f"Auto-flush loop failed: {loop_error}")
        finally:
            # Ensure we're marked as not buffering
            self.is_buffering = False
