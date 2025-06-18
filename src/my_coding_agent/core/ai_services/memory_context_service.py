"""Memory Context Service for AI conversation memory and context management.

This service handles all memory-related functionality including:
- Conversation memory and context management
- Long-term memory storage and retrieval
- Memory statistics and monitoring
- Memory cleanup and session management
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MemoryContextService:
    """Service for managing AI conversation memory and context."""

    def __init__(
        self,
        enable_memory_awareness: bool = False,
        memory_db_path: str | Path | None = None,
    ) -> None:
        """Initialize the memory context service.

        Args:
            enable_memory_awareness: Whether to enable memory-aware functionality
            memory_db_path: Path to the ChromaDB database directory
        """
        self._memory_aware_enabled = enable_memory_awareness
        self._memory_system = None

        if enable_memory_awareness:
            self._initialize_memory_system(memory_db_path)

    def _initialize_memory_system(
        self, memory_db_path: str | Path | None = None
    ) -> None:
        """Initialize the memory system if memory awareness is enabled."""
        try:
            from ..memory_integration import ConversationMemoryHandler

            self._memory_system = ConversationMemoryHandler(memory_db_path)
            logger.info("Memory system initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize memory system: {e}")
            self._memory_aware_enabled = False
            self._memory_system = None

    @property
    def memory_aware_enabled(self) -> bool:
        """Check if memory awareness is enabled."""
        return self._memory_aware_enabled and self._memory_system is not None

    @property
    def memory_system(self):
        """Get the underlying memory system."""
        return self._memory_system

    def store_user_message(
        self, message: str, metadata: dict[str, Any] | None = None
    ) -> str | None:
        """Store a user message in memory.

        Args:
            message: The user message content
            metadata: Optional metadata for the message

        Returns:
            Message ID if successful, None if memory not enabled
        """
        if not self.memory_aware_enabled:
            return None

        try:
            return self._memory_system.store_user_message(message, metadata)
        except Exception as e:
            logger.error(f"Failed to store user message: {e}")
            return None

    def store_assistant_message(
        self, message: str, metadata: dict[str, Any] | None = None
    ) -> str | None:
        """Store an assistant message in memory.

        Args:
            message: The assistant message content
            metadata: Optional metadata for the message

        Returns:
            Message ID if successful, None if memory not enabled
        """
        if not self.memory_aware_enabled:
            return None

        try:
            return self._memory_system.store_assistant_message(message, metadata)
        except Exception as e:
            logger.error(f"Failed to store assistant message: {e}")
            return None

    def store_long_term_memory(
        self,
        content: str,
        memory_type: str = "user_info",
        importance_score: float = 0.8,
    ) -> str | None:
        """Store long-term memory information.

        Args:
            content: The memory content
            memory_type: Type of memory (user_info, preference, fact, etc.)
            importance_score: Importance score (0.0 to 1.0)

        Returns:
            Memory ID if successful, None if memory not enabled
        """
        if not self.memory_aware_enabled:
            return None

        try:
            return self._memory_system.store_long_term_memory(
                content, memory_type, importance_score
            )
        except Exception as e:
            logger.error(f"Failed to store long-term memory: {e}")
            return None

    def get_conversation_context(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent conversation context.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of conversation messages
        """
        if not self.memory_aware_enabled:
            return []

        try:
            return self._memory_system.get_conversation_context(limit)
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return []

    def get_long_term_memories(
        self, query: str = "", limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get long-term memories that match a query.

        Args:
            query: Search query for memories
            limit: Maximum number of memories to retrieve

        Returns:
            List of matching memories
        """
        if not self.memory_aware_enabled:
            return []

        try:
            return self._memory_system.get_long_term_memories(query, limit)
        except Exception as e:
            logger.error(f"Failed to get long-term memories: {e}")
            return []

    def enhance_message_with_memory_context(self, message: str) -> str:
        """Enhance a message with memory context for AI processing.

        Args:
            message: The original message

        Returns:
            Enhanced message with memory context
        """
        if not self.memory_aware_enabled:
            return message

        try:
            # Check if this message contains information to remember long-term
            if any(
                keyword in message.lower()
                for keyword in ["my name is", "i am", "call me", "remember that"]
            ):
                # Extract and store long-term memory
                self.store_long_term_memory(
                    content=message, memory_type="user_info", importance_score=0.9
                )

            # Get conversation context and long-term memories for enhanced prompt
            context = self.get_conversation_context(limit=50)
            long_term_memories = self.get_long_term_memories(query=message, limit=5)

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
                return enhanced_message
            else:
                return message

        except Exception as e:
            logger.warning(f"Failed to enhance message with memory context: {e}")
            return message

    def get_memory_statistics(self) -> dict[str, Any]:
        """Get memory usage statistics.

        Returns:
            Dictionary containing memory usage statistics
        """
        if not self.memory_aware_enabled:
            return {"memory_enabled": False, "error": "Memory system not enabled"}

        try:
            stats = self._memory_system.get_memory_stats()
            stats["memory_enabled"] = True
            return stats
        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {"memory_enabled": True, "error": str(e)}

    async def clear_all_memory(self) -> bool:
        """Clear all stored memory data and start fresh.

        Returns:
            True if successful, False otherwise
        """
        if not self.memory_aware_enabled:
            logger.warning("Memory system not enabled - nothing to clear")
            return False

        try:
            success = await self._memory_system.clear_all_memory_data()
            if success:
                logger.info("Successfully cleared all memory data")
            else:
                logger.error("Failed to clear memory data")
            return success
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False

    def start_new_session(self) -> str | None:
        """Start a new conversation session.

        Returns:
            New session ID if successful, None if memory not enabled
        """
        if not self.memory_aware_enabled:
            return None

        try:
            return self._memory_system.start_new_session()
        except Exception as e:
            logger.error(f"Failed to start new session: {e}")
            return None

    def get_current_session_id(self) -> str | None:
        """Get the current session ID.

        Returns:
            Current session ID if available, None otherwise
        """
        if not self.memory_aware_enabled:
            return None

        try:
            return self._memory_system.current_session_id
        except Exception as e:
            logger.error(f"Failed to get current session ID: {e}")
            return None

    def load_conversation_history(self, chat_widget) -> bool:
        """Load conversation history into a chat widget.

        Args:
            chat_widget: The chat widget to load history into

        Returns:
            True if successful, False otherwise
        """
        if not self.memory_aware_enabled:
            return False

        try:
            self._memory_system.load_conversation_history(chat_widget)
            return True
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            return False

    def get_project_context_for_ai(
        self,
        file_path: str | None = None,
        recent_hours: int = 24,
        max_events: int = 10,
    ) -> str:
        """Get project context for AI processing.

        Args:
            file_path: Optional file path to focus on
            recent_hours: Hours of recent history to include
            max_events: Maximum number of events to include

        Returns:
            Formatted project context string
        """
        if not self.memory_aware_enabled:
            return ""

        try:
            return self._memory_system.get_project_context_for_ai(
                file_path, recent_hours, max_events
            )
        except Exception as e:
            logger.error(f"Failed to get project context: {e}")
            return ""

    async def close(self) -> None:
        """Close the memory service and cleanup resources."""
        if self._memory_system:
            try:
                await self._memory_system.close()
            except Exception as e:
                logger.error(f"Error closing memory system: {e}")

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the memory service.

        Returns:
            Dictionary containing health status information
        """
        return {
            "service_name": "MemoryContextService",
            "memory_enabled": self.memory_aware_enabled,
            "memory_system_initialized": self._memory_system is not None,
            "current_session_id": self.get_current_session_id(),
            "is_healthy": True,
        }
