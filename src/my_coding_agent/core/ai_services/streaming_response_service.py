"""Streaming Response Service for real-time AI communication.

This service handles all streaming-related functionality including:
- Tool-enabled streaming
- Memory-aware streaming
- Stream interruption and management
- Response buffering and chunk handling
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from contextlib import suppress
from typing import Any

from ..streaming import StreamHandler
from .ai_messaging_service import AIMessagingService
from .core_ai_service import AIResponse

logger = logging.getLogger(__name__)

# Type aliases for callbacks
ChunkCallback = Callable[[str, bool], Any]
ErrorCallback = Callable[[Exception], Any]


class StreamingResponseService:
    """Service for managing streaming AI responses with enhanced capabilities."""

    def __init__(
        self,
        ai_messaging_service: AIMessagingService,
        memory_system=None,
        enable_memory_awareness: bool = False,
    ) -> None:
        """Initialize the streaming response service.

        Args:
            ai_messaging_service: The AI messaging service for communication
            memory_system: Optional memory system for context-aware streaming
            enable_memory_awareness: Whether to enable memory-aware streaming
        """
        self._ai_messaging_service = ai_messaging_service
        self._memory_system = memory_system
        self._memory_aware_enabled = (
            enable_memory_awareness and memory_system is not None
        )

        # Stream management
        self._stream_handler: StreamHandler | None = None
        self.current_stream_handler: StreamHandler | None = None
        self.current_stream_id: str | None = None

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return (
            self.current_stream_handler is not None
            and self.current_stream_handler.is_streaming
        )

    @property
    def memory_aware_enabled(self) -> bool:
        """Check if memory-aware streaming is enabled."""
        return self._memory_aware_enabled

    async def send_message_with_tools_stream(
        self,
        message: str,
        on_chunk: ChunkCallback,
        on_error: ErrorCallback = None,
        enable_filesystem: bool = True,
        max_retries: int = 3,
    ) -> AIResponse:
        """Send a message with tool support and streaming output.

        Args:
            message: The message to send to the AI
            on_chunk: Callback function called for each chunk (chunk: str, is_final: bool)
            on_error: Optional callback function called on errors
            enable_filesystem: Whether to enable filesystem tools
            max_retries: Maximum number of retry attempts

        Returns:
            AIResponse: The response from the AI with streaming support
        """
        last_error = None
        retry_count = 0

        for attempt in range(max_retries + 1):
            try:
                # Ensure MCP connection if filesystem tools are enabled
                if enable_filesystem:
                    await self._ensure_filesystem_connection()

                # Create and track stream handler
                if not hasattr(self, "_stream_handler") or self._stream_handler is None:
                    self._stream_handler = StreamHandler()

                stream_handler = self._stream_handler
                self.current_stream_handler = stream_handler

                # Start streaming with our handler
                stream_id = await stream_handler.start_stream(
                    on_chunk, on_error=on_error
                )
                self.current_stream_id = stream_id

                try:
                    # Get the agent from the messaging service
                    agent = self._ai_messaging_service._agent

                    # Use Pydantic AI's streaming capabilities
                    async with agent.run_stream(message) as response:
                        # Stream the response text in real-time
                        full_content = []
                        chunk_count = 0

                        logger.debug(
                            f"Starting stream for message: '{message[:100]}...'"
                        )

                        # Get the stream text generator
                        stream_text = response.stream_text()

                        # Handle different stream text types
                        if hasattr(stream_text, "__aiter__"):
                            # This is an async generator, iterate through it
                            async for chunk in stream_text:
                                # Check for interruption
                                if (
                                    stream_handler._interrupt_event
                                    and stream_handler._interrupt_event.is_set()
                                ):
                                    logger.info("Stream interrupted by user")
                                    break

                                full_content.append(chunk)
                                chunk_count += 1

                                # Call the external callback directly for each chunk
                                try:
                                    callback_result = on_chunk(chunk, False)
                                    if hasattr(callback_result, "__await__"):
                                        await callback_result
                                except Exception as callback_error:
                                    logger.error(
                                        f"Error in streaming callback: {callback_error}"
                                    )
                                    if on_error:
                                        with suppress(Exception):
                                            on_error(callback_error)
                        else:
                            # This might be a coroutine (in tests), await it
                            try:
                                chunks = await stream_text
                                if isinstance(chunks, (list, tuple)):
                                    for chunk in chunks:
                                        full_content.append(chunk)
                                        chunk_count += 1

                                        # Call the external callback directly for each chunk
                                        try:
                                            callback_result = on_chunk(chunk, False)
                                            if hasattr(callback_result, "__await__"):
                                                await callback_result
                                        except Exception as callback_error:
                                            logger.error(
                                                f"Error in streaming callback: {callback_error}"
                                            )
                                            if on_error:
                                                with suppress(Exception):
                                                    on_error(callback_error)
                                else:
                                    # Single chunk
                                    full_content.append(str(chunks))
                                    chunk_count += 1
                                    callback_result = on_chunk(str(chunks), False)
                                    if hasattr(callback_result, "__await__"):
                                        await callback_result
                            except Exception as stream_await_error:
                                logger.error(
                                    f"Error awaiting stream: {stream_await_error}"
                                )
                                # Fallback - treat as empty stream
                                pass

                        # After all chunks are streamed, send a final empty chunk to mark completion
                        try:
                            callback_result = on_chunk(
                                "", True
                            )  # Empty chunk with is_final=True
                            if hasattr(callback_result, "__await__"):
                                await callback_result
                        except Exception as callback_error:
                            logger.error(
                                f"Error in final streaming callback: {callback_error}"
                            )

                        # Get the final output
                        try:
                            final_output = await response.get_output()

                            # Ensure final_output is a string
                            if hasattr(final_output, "data"):
                                final_output = str(final_output.data)
                            elif not isinstance(final_output, str):
                                final_output = str(final_output)

                            logger.debug(
                                f"Stream completed with output length: {len(final_output) if final_output else 0}"
                            )
                        except Exception as output_error:
                            logger.warning(
                                f"Error getting final output: {output_error}"
                            )
                            final_output = None

                        full_text = "".join(str(chunk) for chunk in full_content)

                        # Complete the stream in our handler (for internal tracking only)
                        if stream_handler:
                            await stream_handler.complete_stream(stream_id)

                        # Clear current stream tracking
                        self.current_stream_handler = None
                        self.current_stream_id = None

                        # Ensure we have valid string content
                        content = final_output or full_text or "Response completed"

                        return AIResponse(
                            success=True,
                            content=content,
                            stream_id=stream_id,
                            retry_count=retry_count,
                        )

                except Exception as stream_error:
                    # Handle streaming errors
                    await stream_handler.handle_error(stream_id, stream_error)
                    # Clear current stream tracking on error
                    self.current_stream_handler = None
                    self.current_stream_id = None
                    raise stream_error

            except Exception as e:
                last_error = e
                retry_count = attempt

                # Don't retry on the last attempt
                if attempt < max_retries:
                    # Calculate exponential backoff: 2^attempt seconds
                    backoff_time = 2**attempt
                    logger.warning(
                        f"Streaming attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {backoff_time}s (attempt {attempt + 2}/{max_retries + 1})"
                    )

                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(backoff_time)

                    # Check if stream was interrupted during backoff
                    if (
                        hasattr(self, "current_stream_handler")
                        and self.current_stream_handler
                        and hasattr(self.current_stream_handler, "_interrupt_event")
                        and self.current_stream_handler._interrupt_event.is_set()
                    ):
                        logger.info("Stream was interrupted during retry backoff")
                        break
                else:
                    logger.error(
                        f"All streaming attempts failed after {max_retries} retries. Final error: {e}"
                    )

        # All retries exhausted - return failure response
        if last_error:
            error_type, error_message = self._ai_messaging_service._categorize_error(
                last_error
            )

            # Call error callback if provided
            if on_error:
                try:
                    on_error(last_error)
                except Exception as callback_error:
                    logger.error(f"Error in error callback: {callback_error}")

            return AIResponse(
                success=False,
                content=error_message,
                error=str(last_error),
                error_type=error_type,
                retry_count=retry_count,
                stream_id=getattr(locals(), "stream_id", None),
            )

        # This should not be reached, but handle edge case
        return AIResponse(
            success=False,
            content="Unexpected error in retry logic",
            error="No error captured in retry loop",
            error_type="unknown",
            retry_count=retry_count,
        )

    async def send_memory_aware_message_stream(
        self,
        message: str,
        on_chunk: ChunkCallback,
        on_error: ErrorCallback = None,
        enable_filesystem: bool = True,
    ) -> AIResponse:
        """Send a message with memory awareness and streaming output.

        Args:
            message: The message to send to the AI
            on_chunk: Callback function called for each chunk (chunk: str, is_final: bool)
            on_error: Optional callback function called on errors
            enable_filesystem: Whether to enable filesystem tools

        Returns:
            AIResponse: The response from the AI with memory context
        """
        if not self.memory_aware_enabled or not self._memory_system:
            # Fall back to regular streaming if memory not enabled
            return await self.send_message_with_tools_stream(
                message, on_chunk, on_error, enable_filesystem
            )

        try:
            # Store the user message in memory
            self._memory_system.store_user_message(message)

            # Check if this message contains information to remember long-term
            if any(
                keyword in message.lower()
                for keyword in ["my name is", "i am", "call me", "remember that"]
            ):
                # Extract and store long-term memory
                self._memory_system.store_long_term_memory(
                    content=message, memory_type="user_info", importance_score=0.9
                )

            # Get conversation context and long-term memories for enhanced prompt
            context = self._memory_system.get_conversation_context(limit=50)
            long_term_memories = self._memory_system.get_long_term_memories(
                query=message, limit=5
            )

            # Enhance message with context if available
            enhanced_parts = []

            # Add memory context with clear labels
            if long_term_memories:
                memory_text = "\n".join(
                    [
                        f"- {mem['content']} (importance: {mem.get('importance_score', 'N/A')}, type: {mem.get('memory_type', 'unknown')})"
                        for mem in long_term_memories
                    ]
                )
                enhanced_parts.append(
                    f"=== LONG-TERM MEMORY (Persistent facts, preferences, and important information) ===\n{memory_text}"
                )

            if context:
                # Reverse the context to show in chronological order (oldest first)
                context_reversed = list(reversed(context))
                context_text = "\n".join(
                    [f"{msg['role']}: {msg['content']}" for msg in context_reversed]
                )
                enhanced_parts.append(
                    f"=== CONVERSATION HISTORY (Recent messages in chronological order - this is your short-term memory) ===\n{context_text}"
                )

            if enhanced_parts:
                enhanced_message = (
                    f"=== MEMORY CONTEXT ===\n"
                    f"{chr(10).join(enhanced_parts)}\n\n"
                    f"=== CURRENT USER MESSAGE ===\n{message}\n\n"
                    f"Please respond to the current user message above, taking into account the conversation history "
                    f"and any relevant long-term memories. The conversation history shows the complete context of "
                    f"our recent discussion, so you can reference previous topics and maintain continuity."
                )
            else:
                enhanced_message = message

            logger.info("Using memory-aware streaming with conversation context")

            # Send the enhanced message
            response = await self.send_message_with_tools_stream(
                enhanced_message, on_chunk, on_error, enable_filesystem
            )

            # Store the assistant response in memory if successful
            if response.success and response.content:
                self._memory_system.store_assistant_message(response.content)

            return response

        except Exception as e:
            logger.warning(
                f"Memory-aware streaming failed: {e}. Falling back to regular streaming."
            )
            # Fall back to regular streaming on memory system errors
            return await self.send_message_with_tools_stream(
                message, on_chunk, on_error, enable_filesystem
            )

    async def interrupt_current_stream(self) -> bool:
        """Interrupt the current stream if it exists.

        Returns:
            bool: True if a stream was interrupted, False if no active stream
        """
        if self.current_stream_handler and self.current_stream_id:
            await self.current_stream_handler.interrupt_stream(self.current_stream_id)
            self.current_stream_handler = None
            self.current_stream_id = None
            return True
        return False

    def get_stream_status(self) -> dict[str, Any]:
        """Get current streaming status information.

        Returns:
            dict: Dictionary containing streaming status information
        """
        return {
            "is_streaming": self.is_streaming,
            "current_stream_id": self.current_stream_id,
            "stream_handler_available": self._stream_handler is not None,
            "memory_aware_enabled": self.memory_aware_enabled,
        }

    async def _ensure_filesystem_connection(self) -> None:
        """Ensure filesystem tools are properly connected."""
        # This will be implemented to check MCP connection when integrated
        # For now, we'll delegate to the messaging service's connection logic
        if hasattr(self._ai_messaging_service, "_mcp_connection_service"):
            mcp_service = self._ai_messaging_service._mcp_connection_service
            if mcp_service and hasattr(mcp_service, "ensure_connection"):
                await mcp_service.ensure_connection()

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the streaming service.

        Returns:
            dict: Health status information
        """
        return {
            "service_name": "StreamingResponseService",
            "is_healthy": True,
            "streaming_enabled": True,
            "memory_aware_enabled": self.memory_aware_enabled,
            "current_streams": 1 if self.is_streaming else 0,
            "stream_handler_initialized": self._stream_handler is not None,
        }
