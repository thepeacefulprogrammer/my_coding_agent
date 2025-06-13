"""Memory integration for AI agent conversations."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .memory.memory_manager import MemoryManager
from .memory.memory_types import ConversationMessage


class ConversationMemoryHandler:
    """Handles conversation memory integration for AI agent."""

    def __init__(self, memory_db_path: str | Path | None = None):
        """Initialize the conversation memory handler.

        Args:
            memory_db_path: Path to the memory database. If None, uses default location.
        """
        if memory_db_path is None:
            memory_db_path = Path.home() / ".config" / "my_coding_agent" / "memory.db"

        # Ensure directory exists
        Path(memory_db_path).parent.mkdir(parents=True, exist_ok=True)

        self.memory_manager = MemoryManager(memory_db_path)
        self.current_session_id = self._get_or_create_session_id()

    def _get_or_create_session_id(self) -> str:
        """Generate or restore session ID for conversation persistence."""
        # Try to get the last session ID from memory
        self.memory_manager.get_last_session_id()

        # For now, always create a new session ID when the app starts
        # This can be modified later to restore sessions
        new_session_id = str(uuid.uuid4())

        return new_session_id

    def store_user_message(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> int:
        """Store a user message in memory.

        Args:
            content: The message content
            metadata: Optional metadata for the message

        Returns:
            The ID of the stored message
        """
        message = ConversationMessage(
            session_id=self.current_session_id,
            content=content,
            role="user",
            metadata=metadata or {},
        )
        return self.memory_manager.store_conversation_message(message)

    def store_assistant_message(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> int:
        """Store an assistant message in memory.

        Args:
            content: The message content
            metadata: Optional metadata for the message

        Returns:
            The ID of the stored message
        """
        message = ConversationMessage(
            session_id=self.current_session_id,
            content=content,
            role="assistant",
            metadata=metadata or {},
        )
        return self.memory_manager.store_conversation_message(message)

    def get_conversation_context(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent conversation context for AI agent.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries formatted for AI agent
        """
        # Get recent conversation history for current session
        messages = self.memory_manager.get_conversation_history(
            session_id=self.current_session_id, limit=limit
        )

        # Convert to format expected by AI agent
        context = []
        for msg in messages:
            context.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata,
                }
            )

        return context

    def start_new_session(self) -> str:
        """Start a new conversation session.

        Returns:
            The new session ID
        """
        self.current_session_id = str(uuid.uuid4())
        return self.current_session_id

    def load_conversation_history(self, chat_widget) -> None:
        """Load conversation history into chat widget.

        Args:
            chat_widget: The chat widget to load history into
        """
        # Get conversation history for current session
        messages = self.memory_manager.get_conversation_history(
            session_id=self.current_session_id
        )

        # Add messages to chat widget
        for msg in messages:
            if msg.role == "user":
                chat_widget.add_user_message(msg.content, msg.metadata)
            elif msg.role == "assistant":
                chat_widget.add_assistant_message(msg.content, msg.metadata)
            elif msg.role == "system":
                chat_widget.add_system_message(msg.content, msg.metadata)

    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory system statistics.

        Returns:
            Dictionary with memory statistics
        """
        return self.memory_manager.get_memory_stats()
