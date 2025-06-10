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
        Add a text chunk to the buffer.

        Args:
            chunk: Text chunk to add to buffer
        """
        if not chunk:
            return

        self.current_buffer += chunk
        self._chunks_processed += 1
        self._total_characters += len(chunk)

        # Check if buffer exceeds size threshold
        if len(self.current_buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """
        Manually flush the current buffer content.

        Calls the display callback with buffered content and resets buffer.
        """
        if not self.current_buffer:
            return

        if self._display_callback:
            self._display_callback(self.current_buffer)

        self.current_buffer = ""
        self._flushes_performed += 1
        self._last_flush_time = time.time()

        logger.debug(f"Buffer flushed. Total flushes: {self._flushes_performed}")

    def start_buffering(self) -> None:
        """
        Start automatic time-based buffering.

        Creates a background task that flushes buffer at regular intervals.
        """
        if self.is_buffering:
            return

        self.is_buffering = True
        self._flush_task = asyncio.create_task(self._auto_flush_loop())
        logger.debug("Started automatic buffering")

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
        Background task for automatic time-based flushing.

        Flushes buffer at regular intervals while buffering is active.
        """
        try:
            while self.is_buffering:
                await asyncio.sleep(self.flush_interval)

                # Only flush if we have content and enough time has passed
                if (
                    self.current_buffer
                    and time.time() - self._last_flush_time >= self.flush_interval
                ):
                    self.flush()

        except asyncio.CancelledError:
            logger.debug("Auto-flush loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in auto-flush loop: {e}", exc_info=True)
