"""Memory integration for AI agent conversations using ChromaDB."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
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
        # Try to load existing session ID from a file
        session_file = (
            Path.home() / ".config" / "my_coding_agent" / "current_session.txt"
        )

        try:
            if session_file.exists():
                existing_session_id = session_file.read_text().strip()
                if existing_session_id:
                    print(
                        f"🔄 Resuming conversation session: {existing_session_id[:8]}..."
                    )
                    return existing_session_id
        except Exception as e:
            print(f"Failed to load existing session ID: {e}")

        # Create a new session ID if none exists or loading failed
        new_session_id = str(uuid.uuid4())

        try:
            # Save session ID for persistence
            session_file.parent.mkdir(parents=True, exist_ok=True)
            session_file.write_text(new_session_id)
            # Session created successfully - use logger instead of print
        except Exception as e:
            print(f"Failed to save session ID: {e}")

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

    def get_conversation_context(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent conversation context for AI agent.

        Args:
            limit: Maximum number of messages to retrieve (default: 50 for short-term memory)

        Returns:
            List of message dictionaries formatted for AI agent
        """
        try:
            # Get conversation history using a general query that should match conversations
            # Increase search limit to ensure we get enough results to filter from
            session_results = self.rag_engine.semantic_search(
                query="conversation messages chat dialog",  # Use relevant keywords instead of empty query
                limit=limit
                * 5,  # Get more results to filter by session - increased multiplier for larger limits
                memory_types=["conversation"],
            )

            # Filter results by current session and sort by timestamp
            current_session_messages = []
            for result in session_results:
                if result.metadata.get("session_id") == self.current_session_id:
                    current_session_messages.append(
                        {
                            "role": result.metadata.get("role", "unknown"),
                            "content": result.content,
                            "timestamp": result.metadata.get("timestamp", 0),
                            "metadata": result.metadata,
                        }
                    )

            # If we don't have enough from current session, get recent from all sessions
            if len(current_session_messages) < min(
                10, limit // 5
            ):  # If less than 10 messages or 1/5 of limit
                all_messages = []
                for result in session_results:
                    all_messages.append(
                        {
                            "role": result.metadata.get("role", "unknown"),
                            "content": result.content,
                            "timestamp": result.metadata.get("timestamp", 0),
                            "metadata": result.metadata,
                        }
                    )

                # Sort all messages by timestamp (most recent first) and take what we need
                all_messages.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                context = all_messages[:limit]
            else:
                # Sort current session messages by timestamp (most recent first)
                current_session_messages.sort(
                    key=lambda x: x.get("timestamp", 0), reverse=True
                )
                context = current_session_messages[:limit]

            return context

        except Exception as e:
            print(f"Error getting conversation context: {e}")
            # Fallback to original method if new method fails
            results = self.rag_engine.semantic_search(
                query="conversation history",
                limit=limit * 2,
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

        # Update the persisted session file
        session_file = (
            Path.home() / ".config" / "my_coding_agent" / "current_session.txt"
        )
        try:
            session_file.parent.mkdir(parents=True, exist_ok=True)
            session_file.write_text(self.current_session_id)
            # Session started successfully
        except Exception as e:
            print(f"Failed to persist new session ID: {e}")

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

    async def clear_all_memory_data(self) -> bool:
        """Clear all memory data from ChromaDB.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear all collections in the ChromaDB instance
            collections = await self.rag_engine.client.list_collections()
            for collection in collections:
                await self.rag_engine.client.delete_collection(collection.name)
            return True
        except Exception as e:
            print(f"Error clearing memory data: {e}")
            return False

    # Project History Integration Methods
    def get_project_history(
        self,
        file_path: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> list[dict[str, Any]]:
        """Get project history with optional filtering.

        Args:
            file_path: Optional file path to filter by
            event_type: Optional event type to filter by
            limit: Maximum number of events to retrieve
            start_time: Optional start timestamp filter
            end_time: Optional end timestamp filter

        Returns:
            List of project history events
        """
        try:
            # Build query based on filters
            query_terms = []
            if file_path:
                query_terms.append(f"file:{file_path}")
            if event_type:
                query_terms.append(f"event:{event_type}")

            # Use a general query if no specific terms
            query = (
                " ".join(query_terms)
                if query_terms
                else "project changes code modifications"
            )

            # Get project history from ChromaDB
            results = self.rag_engine.semantic_search(
                query=query,
                limit=limit * 2,  # Get more to filter
                memory_types=["project_history"],
            )

            # Filter and format results
            project_events = []
            for result in results:
                metadata = result.metadata

                # Apply filters
                if file_path and metadata.get("file_path") != file_path:
                    continue
                if event_type and metadata.get("event_type") != event_type:
                    continue
                if start_time and metadata.get("timestamp", 0) < start_time:
                    continue
                if end_time and metadata.get("timestamp", float("inf")) > end_time:
                    continue

                project_events.append(
                    {
                        "event_type": metadata.get("event_type", "unknown"),
                        "description": result.content.split("\n\n")[
                            0
                        ],  # First part is description
                        "file_path": metadata.get("file_path"),
                        "timestamp": metadata.get("timestamp", 0),
                        "content": result.content,
                        "metadata": metadata,
                    }
                )

            # Sort by timestamp (most recent first) and limit
            project_events.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return project_events[:limit]

        except Exception as e:
            print(f"Error getting project history: {e}")
            return []

    def get_project_history_for_file(
        self, file_path: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get project history for a specific file.

        Args:
            file_path: Path to the file
            limit: Maximum number of events to retrieve

        Returns:
            List of project history events for the file
        """
        return self.get_project_history(file_path=file_path, limit=limit)

    def search_project_history(
        self, query: str, limit: int = 25
    ) -> list[dict[str, Any]]:
        """Search project history using semantic search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching project history events
        """
        try:
            results = self.rag_engine.semantic_search(
                query=query,
                limit=limit,
                memory_types=["project_history"],
            )

            project_events = []
            for result in results:
                metadata = result.metadata
                project_events.append(
                    {
                        "event_type": metadata.get("event_type", "unknown"),
                        "description": result.content.split("\n\n")[
                            0
                        ],  # First part is description
                        "file_path": metadata.get("file_path"),
                        "timestamp": metadata.get("timestamp", 0),
                        "content": result.content,
                        "metadata": metadata,
                        "relevance_score": getattr(result, "score", 0.0),
                    }
                )

            # Sort by relevance score (higher is better)
            project_events.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            return project_events

        except Exception as e:
            print(f"Error searching project history: {e}")
            return []

    def generate_project_timeline(
        self,
        start_time: float,
        end_time: float,
        file_path: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a chronological timeline of project events.

        Args:
            start_time: Start timestamp
            end_time: End timestamp
            file_path: Optional file path filter

        Returns:
            Chronological list of project events
        """
        events = self.get_project_history(
            file_path=file_path,
            start_time=start_time,
            end_time=end_time,
            limit=100,  # Get more events for timeline
        )

        # Sort chronologically (oldest first for timeline)
        events.sort(key=lambda x: x.get("timestamp", 0))

        # Add formatted timestamp for display
        for event in events:
            timestamp = event.get("timestamp", 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                event["formatted_time"] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                event["formatted_time"] = "Unknown"

        return events

    def generate_file_timeline(
        self, file_path: str, limit: int = 30
    ) -> list[dict[str, Any]]:
        """Generate timeline for a specific file.

        Args:
            file_path: Path to the file
            limit: Maximum number of events

        Returns:
            Chronological list of events for the file
        """
        events = self.get_project_history_for_file(file_path, limit)

        # Sort chronologically (oldest first for timeline)
        events.sort(key=lambda x: x.get("timestamp", 0))

        # Add formatted timestamp
        for event in events:
            timestamp = event.get("timestamp", 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                event["formatted_time"] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                event["formatted_time"] = "Unknown"

        return events

    def get_project_context_for_ai(
        self,
        file_path: str | None = None,
        recent_hours: int = 24,
        max_events: int = 10,
    ) -> str:
        """Generate project context summary for AI agent.

        Args:
            file_path: Optional file path to focus on
            recent_hours: How many hours back to look
            max_events: Maximum number of events to include

        Returns:
            Formatted project context string
        """
        try:
            # Calculate time filter
            import time

            start_time = time.time() - (recent_hours * 3600)

            # Get recent project history
            events = self.get_project_history(
                file_path=file_path,
                start_time=start_time,
                limit=max_events,
            )

            if not events:
                return "No recent project history available."

            # Build context summary
            context_lines = []
            if file_path:
                context_lines.append(f"Recent changes to {file_path}:")
            else:
                context_lines.append(
                    f"Recent project changes (last {recent_hours} hours):"
                )

            for event in events:
                timestamp = event.get("timestamp", 0)
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    time_str = dt.strftime("%H:%M")
                else:
                    time_str = "??"

                file_info = (
                    f" ({event.get('file_path', 'unknown')})" if not file_path else ""
                )

                context_lines.append(
                    f"- [{time_str}] {event.get('event_type', 'unknown')}: "
                    f"{event.get('description', 'No description')}{file_info}"
                )

            return "\n".join(context_lines)

        except Exception as e:
            print(f"Error generating project context for AI: {e}")
            return "Error retrieving project context."

    def format_timeline_for_ai(self, events: list[dict[str, Any]]) -> str:
        """Format timeline events for AI consumption.

        Args:
            events: List of project events

        Returns:
            Formatted timeline string
        """
        if not events:
            return "No events in timeline."

        timeline_lines = ["Project Timeline:"]

        for event in events:
            time_str = event.get("formatted_time", "Unknown time")
            file_path = event.get("file_path", "unknown")
            event_type = event.get("event_type", "unknown")
            description = event.get("description", "No description")

            timeline_lines.append(
                f"[{time_str}] {event_type} in {file_path}: {description}"
            )

        return "\n".join(timeline_lines)

    def generate_grouped_timeline(
        self,
        events: list[dict[str, Any]],
        group_by: str = "file_path",
    ) -> dict[str, list[dict[str, Any]]]:
        """Generate timeline grouped by specified field.

        Args:
            events: List of project events
            group_by: Field to group by ('file_path', 'event_type', etc.)

        Returns:
            Dictionary of grouped timeline events
        """
        grouped = {}

        for event in events:
            group_key = event.get(group_by, "unknown")
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(event)

        # Sort events within each group chronologically
        for group_events in grouped.values():
            group_events.sort(key=lambda x: x.get("timestamp", 0))

        return grouped
