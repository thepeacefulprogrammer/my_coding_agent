"""Unit tests for memory system database schema."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import datetime, timezone

import pytest
from src.my_coding_agent.core.memory.database_schema import (
    MemoryDatabase,
)
from src.my_coding_agent.core.memory.memory_types import (
    ConversationMessage,
    LongTermMemory,
    ProjectHistory,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestDatabaseSchema:
    """Test database schema creation and functionality."""

    def test_database_initialization(self, temp_db):
        """Test that database can be initialized with all tables."""
        db = MemoryDatabase(temp_db)
        db.initialize()

        # Verify tables exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        expected_tables = [
            "conversation_messages",
            "long_term_memories",
            "project_history",
            "conversation_messages_fts",
            "long_term_memories_fts",
            "project_history_fts",
        ]

        for table in expected_tables:
            assert table in table_names

        conn.close()

    def test_fts5_support(self, temp_db):
        """Test that FTS5 is properly enabled and configured."""
        db = MemoryDatabase(temp_db)
        db.initialize()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Test FTS5 virtual tables exist
        fts_tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'"
        ).fetchall()

        assert len(fts_tables) == 3

        # Test FTS5 can perform text search
        cursor.execute(
            "INSERT INTO conversation_messages (content, role, session_id, timestamp, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                "Test message about Python programming",
                "user",
                "test_session",
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Test FTS search works
        results = cursor.execute(
            "SELECT * FROM conversation_messages_fts WHERE conversation_messages_fts MATCH 'Python'"
        ).fetchall()

        assert len(results) > 0

        conn.close()

    def test_conversation_messages_table(self, temp_db):
        """Test conversation messages table structure and operations."""
        db = MemoryDatabase(temp_db)
        db.initialize()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Test table structure
        columns = cursor.execute("PRAGMA table_info(conversation_messages)").fetchall()
        column_names = [col[1] for col in columns]

        expected_columns = [
            "id",
            "session_id",
            "content",
            "role",
            "timestamp",
            "tokens",
            "metadata",
            "created_at",
        ]

        for col in expected_columns:
            assert col in column_names

        # Test insertion
        test_message = ConversationMessage(
            content="Hello, how are you?",
            role="user",
            session_id="test_session_1",
            tokens=5,
            metadata={"test": "data"},
        )

        cursor.execute(
            """INSERT INTO conversation_messages
               (content, role, session_id, tokens, metadata, timestamp, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                test_message.content,
                test_message.role,
                test_message.session_id,
                test_message.tokens,
                test_message.metadata_json,
                test_message.timestamp,
                test_message.created_at,
            ),
        )

        # Verify insertion
        result = cursor.execute(
            "SELECT * FROM conversation_messages WHERE session_id=?",
            ("test_session_1",),
        ).fetchone()

        assert result is not None
        assert result[2] == "Hello, how are you?"  # content
        assert result[3] == "user"  # role

        conn.close()

    def test_long_term_memories_table(self, temp_db):
        """Test long-term memories table structure and operations."""
        db = MemoryDatabase(temp_db)
        db.initialize()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Test table structure
        columns = cursor.execute("PRAGMA table_info(long_term_memories)").fetchall()
        column_names = [col[1] for col in columns]

        expected_columns = [
            "id",
            "content",
            "memory_type",
            "importance_score",
            "tags",
            "embedding",
            "metadata",
            "created_at",
            "last_accessed",
        ]

        for col in expected_columns:
            assert col in column_names

        # Test insertion
        test_memory = LongTermMemory(
            content="User prefers Python over JavaScript",
            memory_type="preference",
            importance_score=0.8,
            tags=["python", "preference"],
            metadata={"context": "coding discussion"},
        )

        cursor.execute(
            """INSERT INTO long_term_memories
               (content, memory_type, importance_score, tags, metadata, created_at, last_accessed)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                test_memory.content,
                test_memory.memory_type,
                test_memory.importance_score,
                test_memory.tags_json,
                test_memory.metadata_json,
                test_memory.created_at,
                test_memory.last_accessed,
            ),
        )

        # Verify insertion
        result = cursor.execute(
            "SELECT * FROM long_term_memories WHERE memory_type=?", ("preference",)
        ).fetchone()

        assert result is not None
        assert result[1] == "User prefers Python over JavaScript"  # content

        conn.close()

    def test_project_history_table(self, temp_db):
        """Test project history table structure and operations."""
        db = MemoryDatabase(temp_db)
        db.initialize()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Test table structure
        columns = cursor.execute("PRAGMA table_info(project_history)").fetchall()
        column_names = [col[1] for col in columns]

        expected_columns = [
            "id",
            "event_type",
            "description",
            "file_path",
            "code_changes",
            "metadata",
            "created_at",
        ]

        for col in expected_columns:
            assert col in column_names

        # Test insertion
        test_history = ProjectHistory(
            event_type="file_modification",
            description="Added new function to handle memory storage",
            file_path="src/memory/database.py",
            code_changes="+ def store_memory(self, content):",
            metadata={"lines_added": 5, "lines_removed": 0},
        )

        cursor.execute(
            """INSERT INTO project_history
               (event_type, description, file_path, code_changes, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                test_history.event_type,
                test_history.description,
                test_history.file_path,
                test_history.code_changes,
                test_history.metadata_json,
                test_history.created_at,
            ),
        )

        # Verify insertion
        result = cursor.execute(
            "SELECT * FROM project_history WHERE event_type=?", ("file_modification",)
        ).fetchone()

        assert result is not None
        assert result[2] == "Added new function to handle memory storage"  # description

        conn.close()

    def test_database_indexes(self, temp_db):
        """Test that proper indexes are created for performance."""
        db = MemoryDatabase(temp_db)
        db.initialize()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check indexes exist
        indexes = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        index_names = [idx[0] for idx in indexes]

        expected_indexes = [
            "idx_conversation_session",
            "idx_conversation_timestamp",
            "idx_longterm_type",
            "idx_longterm_importance",
            "idx_project_event_type",
            "idx_project_timestamp",
        ]

        for idx in expected_indexes:
            assert idx in index_names

        conn.close()

    def test_database_constraints(self, temp_db):
        """Test database constraints and data validation."""
        db = MemoryDatabase(temp_db)
        db.initialize()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Test NOT NULL constraints
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO conversation_messages (content) VALUES (NULL)")

        # Test CHECK constraints for importance score
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """INSERT INTO long_term_memories
                   (content, memory_type, importance_score, created_at, last_accessed)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    "test",
                    "test",
                    1.5,
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),  # importance_score > 1.0
            )

        conn.close()
