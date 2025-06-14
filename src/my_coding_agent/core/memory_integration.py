"""Memory integration for AI agent conversations using ChromaDB."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .memory.chroma_rag_engine import ChromaRAGEngine


class ConversationMemoryHandler:
    """Handles conversation memory integration for AI agent using ChromaDB."""

    def __init__(self, memory_db_path: str | Path | None = None):
        """Initialize the conversation memory handler.

        Args:
            memory_db_path: Path to the ChromaDB database directory. If None, uses default location.
        """
        if memory_db_path is None:
            memory_db_path = Path.home() / ".config" / "my_coding_agent" / "chroma_db"

        # Ensure directory exists
        Path(memory_db_path).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB RAG engine for memory operations
        self.rag_engine = ChromaRAGEngine(
            memory_manager=None,  # We'll handle this directly
            db_path=str(memory_db_path),
        )
        self.current_session_id = self._get_or_create_session_id()

    def _get_or_create_session_id(self) -> str:
        """Generate a new session ID for conversation persistence."""
        # For now, always create a new session ID when the app starts
        # This can be modified later to restore sessions
        new_session_id = str(uuid.uuid4())
        return new_session_id

    def store_user_message(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Store a user message in ChromaDB.

        Args:
            content: The message content
            metadata: Optional metadata for the message

        Returns:
            The ID of the stored message
        """
        # Store using the conversation method
        message_id = self.rag_engine.store_conversation_with_embedding(
            message_content=content, role="user", session_id=self.current_session_id
        )

        return message_id

    def store_assistant_message(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Store an assistant message in ChromaDB.

        Args:
            content: The message content
            metadata: Optional metadata for the message

        Returns:
            The ID of the stored message
        """
        # Store using the conversation method
        message_id = self.rag_engine.store_conversation_with_embedding(
            message_content=content,
            role="assistant",
            session_id=self.current_session_id,
        )

        return message_id

    def get_conversation_context(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent conversation context for AI agent.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries formatted for AI agent
        """
        # Use semantic search to get conversation history
        # Search for all conversation messages (not just current session for cross-session memory)
        results = self.rag_engine.semantic_search(
            query="conversation history",  # Use a query to get relevant conversations
            limit=limit * 2,  # Get more results to filter
            memory_types=["conversation"],
        )

        # Convert to format expected by AI agent
        context = []
        for result in results:
            context.append(
                {
                    "role": result.metadata.get("role", "unknown"),
                    "content": result.content,
                    "timestamp": result.metadata.get("timestamp", 0),
                    "metadata": result.metadata,
                }
            )

        # Sort by timestamp (most recent first) and limit
        context.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return context[:limit]

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
        context = self.get_conversation_context()

        # Add messages to chat widget
        for msg in context:
            if msg["role"] == "user":
                chat_widget.add_user_message(msg["content"], msg.get("metadata", {}))
            elif msg["role"] == "assistant":
                chat_widget.add_assistant_message(
                    msg["content"], msg.get("metadata", {})
                )
            elif msg["role"] == "system":
                chat_widget.add_system_message(msg["content"], msg.get("metadata", {}))

    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory system statistics.

        Returns:
            Dictionary with memory statistics
        """
        return self.rag_engine.get_memory_statistics()

    def store_long_term_memory(
        self,
        content: str,
        memory_type: str = "user_info",
        importance_score: float = 0.8,
    ) -> str:
        """Store a long-term memory that persists across sessions.

        Args:
            content: The memory content
            memory_type: Type of memory (user_info, preference, fact, etc.)
            importance_score: Importance score from 0.0 to 1.0

        Returns:
            The ID of the stored memory
        """
        from .memory.memory_types import LongTermMemory

        # Create a long-term memory object
        memory = LongTermMemory(
            content=content,
            memory_type=memory_type,
            importance_score=importance_score,
            tags=[memory_type, "persistent"],
            embedding=None,  # ChromaDB will generate the embedding
        )

        # Store using the RAG engine
        memory_id = self.rag_engine.store_memory_with_embedding(memory)
        return memory_id

    def get_long_term_memories(
        self, query: str = "", limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get long-term memories that match a query.

        Args:
            query: Search query (empty string gets all memories)
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory dictionaries
        """
        # Search for long-term memories
        results = self.rag_engine.semantic_search(
            query=query or "user information preferences facts",
            limit=limit,
            memory_types=["user_info", "preference", "fact", "instruction"],
        )

        # Convert to format expected by AI agent
        memories = []
        for result in results:
            memories.append(
                {
                    "content": result.content,
                    "memory_type": result.memory_type,
                    "importance_score": result.importance_score,
                    "tags": result.tags,
                    "created_at": result.created_at,
                    "metadata": result.metadata,
                }
            )

        return memories

    async def close(self) -> None:
        """Close the memory handler and cleanup resources."""
        if self.rag_engine:
            await self.rag_engine.close()
