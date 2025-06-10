"""MemoryManager class for handling CRUD operations on all memory types."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .database_schema import init_database
from .memory_types import (
    ConversationMessage,
    LongTermMemory,
    MemorySearchResult,
    ProjectHistory,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manager class for handling all memory operations with CRUD functionality."""

    def __init__(self, db_path: str | Path):
        """Initialize MemoryManager with database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db = init_database(db_path)
        logger.info(f"MemoryManager initialized with database at {self.db_path}")

    # Conversation Message CRUD Operations
    def store_conversation_message(self, message: ConversationMessage) -> int:
        """Store a conversation message in the database.

        Args:
            message: ConversationMessage instance to store

        Returns:
            int: The ID of the stored message
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO conversation_messages
                   (session_id, content, role, timestamp, tokens, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    message.session_id,
                    message.content,
                    message.role,
                    message.timestamp,
                    message.tokens,
                    message.metadata_json,
                    message.created_at,
                ),
            )
            message_id = cursor.lastrowid
            conn.commit()

        logger.debug(f"Stored conversation message with ID {message_id}")
        return message_id

    def get_conversation_message(self, message_id: int) -> ConversationMessage | None:
        """Retrieve a conversation message by ID.

        Args:
            message_id: ID of the message to retrieve

        Returns:
            ConversationMessage instance or None if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM conversation_messages WHERE id = ?", (message_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_conversation_message(row)

    def get_conversation_history(
        self, session_id: str, limit: int | None = None
    ) -> list[ConversationMessage]:
        """Get conversation history for a specific session.

        Args:
            session_id: Session ID to retrieve history for
            limit: Optional limit on number of messages to return

        Returns:
            List of ConversationMessage instances in chronological order
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            query = """SELECT * FROM conversation_messages
                      WHERE session_id = ?
                      ORDER BY timestamp ASC"""
            params = [session_id]

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            rows = cursor.execute(query, params).fetchall()

        return [self._row_to_conversation_message(row) for row in rows]

    def get_recent_conversations(self, limit: int = 50) -> list[ConversationMessage]:
        """Get recent conversation messages across all sessions.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of ConversationMessage instances ordered by timestamp (most recent first)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                """SELECT * FROM conversation_messages
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

        return [self._row_to_conversation_message(row) for row in rows]

    def delete_conversation_message(self, message_id: int) -> bool:
        """Delete a conversation message by ID.

        Args:
            message_id: ID of the message to delete

        Returns:
            bool: True if message was deleted, False if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM conversation_messages WHERE id = ?", (message_id,)
            )
            deleted = cursor.rowcount > 0
            conn.commit()

        logger.debug(f"Deleted conversation message {message_id}: {deleted}")
        return deleted

    # Long-term Memory CRUD Operations
    def store_long_term_memory(self, memory: LongTermMemory) -> int:
        """Store a long-term memory in the database.

        Args:
            memory: LongTermMemory instance to store

        Returns:
            int: The ID of the stored memory
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO long_term_memories
                   (content, memory_type, importance_score, tags, embedding, metadata, created_at, last_accessed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    memory.content,
                    memory.memory_type,
                    memory.importance_score,
                    memory.tags_json,
                    memory.embedding,
                    memory.metadata_json,
                    memory.created_at,
                    memory.last_accessed,
                ),
            )
            memory_id = cursor.lastrowid
            conn.commit()

        logger.debug(f"Stored long-term memory with ID {memory_id}")
        return memory_id

    def get_long_term_memory(self, memory_id: int) -> LongTermMemory | None:
        """Retrieve a long-term memory by ID.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            LongTermMemory instance or None if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM long_term_memories WHERE id = ?", (memory_id,)
            ).fetchone()

            if not row:
                return None

            # Update last_accessed timestamp
            cursor.execute(
                "UPDATE long_term_memories SET last_accessed = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), memory_id),
            )
            conn.commit()

            return self._row_to_long_term_memory(row)

    def get_memories_by_type(self, memory_type: str) -> list[LongTermMemory]:
        """Get all long-term memories of a specific type.

        Args:
            memory_type: Type of memory to retrieve

        Returns:
            List of LongTermMemory instances
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                "SELECT * FROM long_term_memories WHERE memory_type = ? ORDER BY importance_score DESC",
                (memory_type,),
            ).fetchall()

        return [self._row_to_long_term_memory(row) for row in rows]

    def get_memories_by_importance(
        self, min_score: float, max_score: float = 1.0
    ) -> list[LongTermMemory]:
        """Get long-term memories by importance score range.

        Args:
            min_score: Minimum importance score
            max_score: Maximum importance score

        Returns:
            List of LongTermMemory instances ordered by importance (descending)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                """SELECT * FROM long_term_memories
                   WHERE importance_score >= ? AND importance_score <= ?
                   ORDER BY importance_score DESC""",
                (min_score, max_score),
            ).fetchall()

        return [self._row_to_long_term_memory(row) for row in rows]

    def update_long_term_memory(self, memory: LongTermMemory) -> bool:
        """Update an existing long-term memory.

        Args:
            memory: LongTermMemory instance with updated data (must have ID)

        Returns:
            bool: True if memory was updated, False if not found
        """
        if not memory.id:
            raise ValueError("Memory must have an ID to be updated")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # First update only the FTS-tracked fields to avoid trigger conflicts
            cursor.execute(
                """UPDATE long_term_memories
                   SET content = ?, memory_type = ?, importance_score = ?,
                       tags = ?, embedding = ?, metadata = ?
                   WHERE id = ?""",
                (
                    memory.content,
                    memory.memory_type,
                    memory.importance_score,
                    memory.tags_json,
                    memory.embedding,
                    memory.metadata_json,
                    memory.id,
                ),
            )

            # Then update last_accessed separately to avoid FTS trigger issues
            if cursor.rowcount > 0:
                cursor.execute(
                    "UPDATE long_term_memories SET last_accessed = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), memory.id),
                )
                updated = True
            else:
                updated = False

            conn.commit()

        logger.debug(f"Updated long-term memory {memory.id}: {updated}")
        return updated

    def delete_long_term_memory(self, memory_id: int) -> bool:
        """Delete a long-term memory by ID.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            bool: True if memory was deleted, False if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memories WHERE id = ?", (memory_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        logger.debug(f"Deleted long-term memory {memory_id}: {deleted}")
        return deleted

    # Project History CRUD Operations
    def store_project_history(self, history: ProjectHistory) -> int:
        """Store a project history entry in the database.

        Args:
            history: ProjectHistory instance to store

        Returns:
            int: The ID of the stored history entry
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO project_history
                   (event_type, description, file_path, code_changes, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    history.event_type,
                    history.description,
                    history.file_path,
                    history.code_changes,
                    history.metadata_json,
                    history.created_at,
                ),
            )
            history_id = cursor.lastrowid
            conn.commit()

        logger.debug(f"Stored project history with ID {history_id}")
        return history_id

    def get_project_history(self, history_id: int) -> ProjectHistory | None:
        """Retrieve a project history entry by ID.

        Args:
            history_id: ID of the history entry to retrieve

        Returns:
            ProjectHistory instance or None if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM project_history WHERE id = ?", (history_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_project_history(row)

    def get_project_history_by_file(self, file_path: str) -> list[ProjectHistory]:
        """Get project history entries for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of ProjectHistory instances ordered by timestamp (most recent first)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                "SELECT * FROM project_history WHERE file_path = ? ORDER BY created_at DESC",
                (file_path,),
            ).fetchall()

        return [self._row_to_project_history(row) for row in rows]

    def get_project_history_by_event_type(
        self, event_type: str
    ) -> list[ProjectHistory]:
        """Get project history entries by event type.

        Args:
            event_type: Type of event to filter by

        Returns:
            List of ProjectHistory instances ordered by timestamp (most recent first)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                "SELECT * FROM project_history WHERE event_type = ? ORDER BY created_at DESC",
                (event_type,),
            ).fetchall()

        return [self._row_to_project_history(row) for row in rows]

    # Search Operations
    def search_all_memories(
        self, query: str, limit: int = 20
    ) -> list[MemorySearchResult]:
        """Search across all memory types using FTS5.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of MemorySearchResult instances with relevance scores
        """
        results = []

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Search conversation messages
            conv_results = cursor.execute(
                """SELECT cm.*, rank FROM conversation_messages cm
                   JOIN conversation_messages_fts ON cm.id = conversation_messages_fts.rowid
                   WHERE conversation_messages_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit // 3),
            ).fetchall()

            for row in conv_results:
                results.append(
                    MemorySearchResult(
                        memory_id=row[0],
                        memory_type="conversation",
                        content=row[2],  # content column
                        relevance_score=min(1.0, abs(row[-1]) / 10.0),  # normalize rank
                        metadata={"role": row[3], "session_id": row[1]},
                    )
                )

            # Search long-term memories
            lt_results = cursor.execute(
                """SELECT ltm.*, rank FROM long_term_memories ltm
                   JOIN long_term_memories_fts ON ltm.id = long_term_memories_fts.rowid
                   WHERE long_term_memories_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit // 3),
            ).fetchall()

            for row in lt_results:
                results.append(
                    MemorySearchResult(
                        memory_id=row[0],
                        memory_type="longterm",
                        content=row[1],  # content column
                        relevance_score=min(1.0, abs(row[-1]) / 10.0),  # normalize rank
                        metadata={"memory_type": row[2], "importance_score": row[3]},
                    )
                )

            # Search project history
            ph_results = cursor.execute(
                """SELECT ph.*, rank FROM project_history ph
                   JOIN project_history_fts ON ph.id = project_history_fts.rowid
                   WHERE project_history_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit // 3),
            ).fetchall()

            for row in ph_results:
                results.append(
                    MemorySearchResult(
                        memory_id=row[0],
                        memory_type="project",
                        content=row[2],  # description column
                        relevance_score=min(1.0, abs(row[-1]) / 10.0),  # normalize rank
                        metadata={"event_type": row[1], "file_path": row[3]},
                    )
                )

        # Sort by relevance score (highest first)
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    # Utility Operations
    def clear_session_data(self, session_id: str) -> bool:
        """Clear all conversation data for a specific session.

        Args:
            session_id: Session ID to clear

        Returns:
            bool: True if data was cleared
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM conversation_messages WHERE session_id = ?", (session_id,)
            )
            deleted = cursor.rowcount > 0
            conn.commit()

        logger.info(f"Cleared session data for {session_id}: {deleted}")
        return deleted

    def get_memory_stats(self) -> dict[str, int]:
        """Get statistics about stored memories.

        Returns:
            Dictionary with counts for each memory type
        """
        stats = {}

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Count conversation messages
            count = cursor.execute(
                "SELECT COUNT(*) FROM conversation_messages"
            ).fetchone()[0]
            stats["conversation_messages"] = count

            # Count long-term memories
            count = cursor.execute(
                "SELECT COUNT(*) FROM long_term_memories"
            ).fetchone()[0]
            stats["long_term_memories"] = count

            # Count project history
            count = cursor.execute("SELECT COUNT(*) FROM project_history").fetchone()[0]
            stats["project_history"] = count

        return stats

    # Helper Methods for Converting Database Rows to Objects
    def _row_to_conversation_message(self, row) -> ConversationMessage:
        """Convert database row to ConversationMessage instance."""
        return ConversationMessage(
            id=row[0],
            session_id=row[1],
            content=row[2],
            role=row[3],
            timestamp=row[4],
            tokens=row[5],
            metadata=json.loads(row[6]) if row[6] else {},
            created_at=row[7],
        )

    def _row_to_long_term_memory(self, row) -> LongTermMemory:
        """Convert database row to LongTermMemory instance."""
        return LongTermMemory(
            id=row[0],
            content=row[1],
            memory_type=row[2],
            importance_score=row[3],
            tags=json.loads(row[4]) if row[4] else [],
            embedding=row[5],
            metadata=json.loads(row[6]) if row[6] else {},
            created_at=row[7],
            last_accessed=row[8],
        )

    def _row_to_project_history(self, row) -> ProjectHistory:
        """Convert database row to ProjectHistory instance.

        Args:
            row: Database row from project_history table

        Returns:
            ProjectHistory instance
        """
        return ProjectHistory(
            id=row[0],
            event_type=row[1],
            description=row[2],
            file_path=row[3],
            code_changes=row[4],
            metadata=json.loads(row[5]) if row[5] else {},
            created_at=row[6],
        )

    # Session Persistence Methods
    def save_session_to_file(self, session_id: str, file_path: str | Path) -> bool:
        """Save session conversation data to a JSON file.

        Args:
            session_id: Session ID to save
            file_path: Path to save the session data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)

            # Get conversation history for the session
            messages = self.get_conversation_history(session_id)

            # Convert messages to dictionaries for JSON serialization
            message_dicts = []
            for msg in messages:
                message_dict = {
                    "content": msg.content,
                    "role": msg.role,
                    "session_id": msg.session_id,
                    "timestamp": msg.timestamp,
                    "tokens": msg.tokens,
                    "metadata": msg.metadata,
                    "created_at": msg.created_at,
                }
                message_dicts.append(message_dict)

            # Create session data structure
            session_data = {
                "session_id": session_id,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "messages": message_dicts,
            }

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Saved session {session_id} with {len(messages)} messages to {file_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save session {session_id} to {file_path}: {e}")
            return False

    def load_session_from_file(self, file_path: str | Path) -> str | None:
        """Load session conversation data from a JSON file.

        Args:
            file_path: Path to the session data file

        Returns:
            str | None: Session ID if successful, None if failed
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                logger.warning(f"Session file does not exist: {file_path}")
                return None

            # Read session data
            with open(file_path, encoding="utf-8") as f:
                session_data = json.load(f)

            # Validate session data structure
            if not isinstance(session_data, dict):
                logger.error(f"Invalid session data format in {file_path}")
                return None

            required_keys = ["session_id", "messages"]
            if not all(key in session_data for key in required_keys):
                logger.error(f"Missing required keys in session data: {file_path}")
                return None

            session_id = session_data["session_id"]
            messages_data = session_data["messages"]

            # Load messages into database
            loaded_count = 0
            for msg_data in messages_data:
                try:
                    # Create ConversationMessage instance
                    message = ConversationMessage(
                        content=msg_data["content"],
                        role=msg_data["role"],
                        session_id=msg_data["session_id"],
                        timestamp=msg_data.get("timestamp"),
                        tokens=msg_data.get("tokens"),
                        metadata=msg_data.get("metadata", {}),
                        created_at=msg_data.get("created_at"),
                    )

                    # Store in database
                    self.store_conversation_message(message)
                    loaded_count += 1

                except Exception as e:
                    logger.warning(f"Failed to load message from session file: {e}")
                    continue

            logger.info(
                f"Loaded session {session_id} with {loaded_count} messages from {file_path}"
            )
            return session_id

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in session file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load session from {file_path}: {e}")
            return None

    def get_last_session_id(self) -> str | None:
        """Get the session ID of the most recent conversation.

        Returns:
            str | None: Session ID with most recent message, None if no sessions
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                row = cursor.execute(
                    """SELECT session_id FROM conversation_messages
                       ORDER BY timestamp DESC
                       LIMIT 1"""
                ).fetchone()

                return row[0] if row else None

        except Exception as e:
            logger.error(f"Failed to get last session ID: {e}")
            return None

    def get_session_file_path(self, session_id: str | None = None) -> Path:
        """Get the default file path for saving/loading session data.

        Args:
            session_id: Session ID to generate path for. If None, uses last session.

        Returns:
            Path: Default path for session file
        """
        if session_id is None:
            session_id = self.get_last_session_id() or "default"

        # Create sessions directory relative to database
        sessions_dir = self.db_path.parent / "sessions"
        sessions_dir.mkdir(exist_ok=True)

        return sessions_dir / f"{session_id}.json"

    # Crawl4AI Text Chunking Methods
    def chunk_text_sliding_window(
        self, text: str, window_size: int = 100, step: int = 50
    ) -> list[str]:
        """Chunk text using sliding window strategy from Crawl4AI.

        Args:
            text: Text to chunk
            window_size: Window size in words
            step: Step size between windows

        Returns:
            list[str]: List of text chunks
        """
        try:
            from crawl4ai.chunking_strategy import SlidingWindowChunking

            chunker = SlidingWindowChunking(window_size=window_size, step=step)
            chunks = chunker.chunk(text)

            logger.info(
                f"Chunked text into {len(chunks)} segments using sliding window"
            )
            return chunks

        except ImportError as e:
            logger.error(f"Crawl4AI not available for chunking: {e}")
            # Fallback to simple word-based chunking
            return self._fallback_sliding_window_chunk(text, window_size, step)
        except Exception as e:
            logger.error(f"Failed to chunk text with sliding window: {e}")
            return [text]  # Return original text if chunking fails

    def chunk_text_regex(self, text: str, patterns: list[str] = None) -> list[str]:
        """Chunk text using regex patterns from Crawl4AI.

        Args:
            text: Text to chunk
            patterns: List of regex patterns for splitting

        Returns:
            list[str]: List of text chunks
        """
        try:
            from crawl4ai.chunking_strategy import RegexChunking

            if patterns is None:
                patterns = [r"\n\n"]  # Default: split on double newlines

            chunker = RegexChunking(patterns=patterns)
            chunks = chunker.chunk(text)

            # Filter out empty chunks
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

            logger.info(
                f"Chunked text into {len(chunks)} segments using regex patterns"
            )
            return chunks

        except ImportError as e:
            logger.error(f"Crawl4AI not available for chunking: {e}")
            # Fallback to simple regex chunking
            return self._fallback_regex_chunk(text, patterns or [r"\n\n"])
        except Exception as e:
            logger.error(f"Failed to chunk text with regex: {e}")
            return [text]

    def chunk_text_overlapping_window(
        self, text: str, window_size: int = 1000, overlap: int = 100
    ) -> list[str]:
        """Chunk text using overlapping window strategy from Crawl4AI.

        Args:
            text: Text to chunk
            window_size: Window size in words
            overlap: Overlap size in words

        Returns:
            list[str]: List of text chunks
        """
        try:
            from crawl4ai.chunking_strategy import OverlappingWindowChunking

            chunker = OverlappingWindowChunking(
                window_size=window_size, overlap=overlap
            )
            chunks = chunker.chunk(text)

            logger.info(
                f"Chunked text into {len(chunks)} segments using overlapping window"
            )
            return chunks

        except ImportError as e:
            logger.error(f"Crawl4AI not available for chunking: {e}")
            # Fallback to simple overlapping chunking
            return self._fallback_overlapping_chunk(text, window_size, overlap)
        except Exception as e:
            logger.error(f"Failed to chunk text with overlapping window: {e}")
            return [text]

    def chunk_and_store_long_term_memory(
        self,
        content: str,
        memory_type: str,
        importance_score: float,
        tags: list[str] = None,
        chunk_strategy: str = "sliding_window",
        window_size: int = 200,
        step: int = 150,
        overlap: int = 50,
        patterns: list[str] = None,
    ) -> list[int]:
        """Chunk text and store each chunk as a separate long-term memory.

        Args:
            content: Text content to chunk and store
            memory_type: Type of memory
            importance_score: Importance score for memories
            tags: Tags to add to memories
            chunk_strategy: Chunking strategy ('sliding_window', 'regex', 'overlapping_window')
            window_size: Window size for sliding window or overlapping window
            step: Step size for sliding window
            overlap: Overlap size for overlapping window
            patterns: Regex patterns for regex chunking

        Returns:
            list[int]: List of memory IDs for stored chunks
        """
        try:
            # Choose chunking strategy
            if chunk_strategy == "sliding_window":
                chunks = self.chunk_text_sliding_window(content, window_size, step)
            elif chunk_strategy == "regex":
                chunks = self.chunk_text_regex(content, patterns)
            elif chunk_strategy == "overlapping_window":
                chunks = self.chunk_text_overlapping_window(
                    content, window_size, overlap
                )
            else:
                logger.warning(
                    f"Unknown chunking strategy: {chunk_strategy}, using sliding_window"
                )
                chunks = self.chunk_text_sliding_window(content, window_size, step)

            # Store each chunk as a separate memory
            memory_ids = []
            for i, chunk in enumerate(chunks):
                if not chunk.strip():  # Skip empty chunks
                    continue

                chunk_tags = (tags or []).copy()
                chunk_tags.extend(["chunked", f"chunk_{i + 1}_of_{len(chunks)}"])

                chunk_memory = LongTermMemory(
                    content=chunk.strip(),
                    memory_type=memory_type,
                    importance_score=importance_score,
                    tags=chunk_tags,
                    embedding=None,  # Embedding will be generated when needed
                    metadata={
                        "chunk_strategy": chunk_strategy,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "original_length": len(content),
                        "chunk_parameters": {
                            "window_size": window_size,
                            "step": step,
                            "overlap": overlap,
                            "patterns": patterns,
                        },
                    },
                )

                memory_id = self.store_long_term_memory(chunk_memory)
                memory_ids.append(memory_id)

            logger.info(
                f"Stored {len(memory_ids)} chunked memories using {chunk_strategy} strategy"
            )
            return memory_ids

        except Exception as e:
            logger.error(f"Failed to chunk and store long-term memory: {e}")
            # Fallback: store as single memory without chunking
            memory = LongTermMemory(
                content=content,
                memory_type=memory_type,
                importance_score=importance_score,
                tags=(tags or []) + ["chunking_failed"],
                embedding=None,
            )
            return [self.store_long_term_memory(memory)]

    def get_available_chunking_strategies(self) -> dict[str, dict]:
        """Get information about available chunking strategies.

        Returns:
            dict: Dictionary of strategy names and their information
        """
        strategies = {
            "sliding_window": {
                "description": "Creates overlapping chunks with sliding window approach",
                "parameters": [
                    {
                        "name": "window_size",
                        "type": "int",
                        "default": 100,
                        "description": "Window size in words",
                    },
                    {
                        "name": "step",
                        "type": "int",
                        "default": 50,
                        "description": "Step size between windows",
                    },
                ],
            },
            "regex": {
                "description": "Splits text based on regex patterns",
                "parameters": [
                    {
                        "name": "patterns",
                        "type": "list[str]",
                        "default": ["\\n\\n"],
                        "description": "Regex patterns for splitting",
                    }
                ],
            },
            "overlapping_window": {
                "description": "Creates chunks with specified overlap",
                "parameters": [
                    {
                        "name": "window_size",
                        "type": "int",
                        "default": 1000,
                        "description": "Window size in words",
                    },
                    {
                        "name": "overlap",
                        "type": "int",
                        "default": 100,
                        "description": "Overlap size in words",
                    },
                ],
            },
        }
        return strategies

    # Fallback chunking methods (when Crawl4AI is not available)
    def _fallback_sliding_window_chunk(
        self, text: str, window_size: int, step: int
    ) -> list[str]:
        """Fallback sliding window chunking implementation."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), step):
            chunk_words = words[i : i + window_size]
            if chunk_words:
                chunks.append(" ".join(chunk_words))

        return chunks

    def _fallback_regex_chunk(self, text: str, patterns: list[str]) -> list[str]:
        """Fallback regex chunking implementation."""
        import re

        chunks = [text]
        for pattern in patterns:
            new_chunks = []
            for chunk in chunks:
                parts = re.split(pattern, chunk)
                new_chunks.extend(parts)
            chunks = new_chunks

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _fallback_overlapping_chunk(
        self, text: str, window_size: int, overlap: int
    ) -> list[str]:
        """Fallback overlapping window chunking implementation."""
        words = text.split()
        chunks = []
        step = window_size - overlap

        for i in range(0, len(words) - overlap, step):
            chunk_words = words[i : i + window_size]
            if chunk_words:
                chunks.append(" ".join(chunk_words))

        return chunks
