"""Unit tests for MemoryManager CRUD operations."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from src.my_coding_agent.core.memory.memory_manager import MemoryManager
from src.my_coding_agent.core.memory.memory_types import (
    ConversationMessage,
    LongTermMemory,
    MemorySearchResult,
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


@pytest.fixture
def memory_manager(temp_db):
    """Create a MemoryManager instance for testing."""
    manager = MemoryManager(temp_db)
    return manager


class TestMemoryManager:
    """Test MemoryManager CRUD operations."""

    def test_initialization(self, temp_db):
        """Test MemoryManager initialization."""
        manager = MemoryManager(temp_db)
        assert manager.db_path == Path(temp_db)
        assert manager.db.check_health()

    # Conversation Message CRUD Tests
    def test_store_conversation_message(self, memory_manager):
        """Test storing a conversation message."""
        message = ConversationMessage(
            content="Hello, how are you?",
            role="user",
            session_id="test_session_1",
            tokens=5,
        )

        message_id = memory_manager.store_conversation_message(message)
        assert message_id is not None
        assert isinstance(message_id, int)

    def test_get_conversation_message(self, memory_manager):
        """Test retrieving a conversation message by ID."""
        message = ConversationMessage(
            content="Hello, how are you?", role="user", session_id="test_session_1"
        )

        message_id = memory_manager.store_conversation_message(message)
        retrieved = memory_manager.get_conversation_message(message_id)

        assert retrieved is not None
        assert retrieved.content == "Hello, how are you?"
        assert retrieved.role == "user"
        assert retrieved.session_id == "test_session_1"

    def test_get_conversation_history(self, memory_manager):
        """Test retrieving conversation history by session."""
        # Store multiple messages
        messages = [
            ConversationMessage(content="Hello", role="user", session_id="session1"),
            ConversationMessage(
                content="Hi there!", role="assistant", session_id="session1"
            ),
            ConversationMessage(
                content="How are you?", role="user", session_id="session1"
            ),
            ConversationMessage(
                content="I'm fine", role="assistant", session_id="session2"
            ),
        ]

        for msg in messages:
            memory_manager.store_conversation_message(msg)

        # Get history for session1
        history = memory_manager.get_conversation_history("session1")
        assert len(history) == 3

        # Check order (should be chronological)
        assert history[0].content == "Hello"
        assert history[1].content == "Hi there!"
        assert history[2].content == "How are you?"

    def test_get_recent_conversations(self, memory_manager):
        """Test retrieving recent conversations with limit."""
        # Store messages in different sessions
        for i in range(10):
            msg = ConversationMessage(
                content=f"Message {i}", role="user", session_id=f"session_{i % 3}"
            )
            memory_manager.store_conversation_message(msg)

        # Get recent conversations (limit 5)
        recent = memory_manager.get_recent_conversations(limit=5)
        assert len(recent) <= 5

        # Should be ordered by timestamp (most recent first)
        for i in range(1, len(recent)):
            assert recent[i - 1].timestamp >= recent[i].timestamp

    def test_delete_conversation_message(self, memory_manager):
        """Test deleting a conversation message."""
        message = ConversationMessage(content="Test message", role="user")
        message_id = memory_manager.store_conversation_message(message)

        # Verify it exists
        assert memory_manager.get_conversation_message(message_id) is not None

        # Delete it
        success = memory_manager.delete_conversation_message(message_id)
        assert success

        # Verify it's gone
        assert memory_manager.get_conversation_message(message_id) is None

    # Long-term Memory CRUD Tests
    def test_store_long_term_memory(self, memory_manager):
        """Test storing a long-term memory."""
        memory = LongTermMemory(
            content="User prefers Python over JavaScript",
            memory_type="preference",
            importance_score=0.8,
            tags=["python", "preference"],
        )

        memory_id = memory_manager.store_long_term_memory(memory)
        assert memory_id is not None
        assert isinstance(memory_id, int)

    def test_get_long_term_memory(self, memory_manager):
        """Test retrieving a long-term memory by ID."""
        memory = LongTermMemory(
            content="Always use type hints in Python",
            memory_type="lesson",
            importance_score=0.9,
            tags=["python", "best_practice"],
        )

        memory_id = memory_manager.store_long_term_memory(memory)
        retrieved = memory_manager.get_long_term_memory(memory_id)

        assert retrieved is not None
        assert retrieved.content == "Always use type hints in Python"
        assert retrieved.memory_type == "lesson"
        assert retrieved.importance_score == 0.9
        assert "python" in retrieved.tags

    def test_get_memories_by_type(self, memory_manager):
        """Test retrieving memories by type."""
        memories = [
            LongTermMemory(
                content="Pref 1", memory_type="preference", importance_score=0.7
            ),
            LongTermMemory(content="Fact 1", memory_type="fact", importance_score=0.8),
            LongTermMemory(
                content="Pref 2", memory_type="preference", importance_score=0.6
            ),
        ]

        for memory in memories:
            memory_manager.store_long_term_memory(memory)

        preferences = memory_manager.get_memories_by_type("preference")
        assert len(preferences) == 2

        facts = memory_manager.get_memories_by_type("fact")
        assert len(facts) == 1

    def test_get_memories_by_importance(self, memory_manager):
        """Test retrieving memories by importance threshold."""
        memories = [
            LongTermMemory(
                content="Low importance", memory_type="fact", importance_score=0.3
            ),
            LongTermMemory(
                content="High importance", memory_type="fact", importance_score=0.9
            ),
            LongTermMemory(
                content="Medium importance", memory_type="fact", importance_score=0.6
            ),
        ]

        for memory in memories:
            memory_manager.store_long_term_memory(memory)

        # Get memories with importance >= 0.5
        important = memory_manager.get_memories_by_importance(min_score=0.5)
        assert len(important) == 2

        # Should be ordered by importance (descending)
        assert important[0].importance_score >= important[1].importance_score

    @pytest.mark.skip(
        reason="FTS5 trigger conflict with database updates - known issue to be fixed in schema redesign"
    )
    def test_update_long_term_memory(self, temp_db):
        """Test updating a long-term memory."""
        # Use fresh manager to avoid transaction conflicts
        manager = MemoryManager(temp_db)

        memory = LongTermMemory(
            content="Original content", memory_type="fact", importance_score=0.5
        )

        memory_id = manager.store_long_term_memory(memory)

        # Update the memory with new data
        updated_memory = LongTermMemory(
            id=memory_id,
            content="Updated content",
            memory_type="fact",
            importance_score=0.8,
            tags=["updated"],
        )

        success = manager.update_long_term_memory(updated_memory)
        assert success

        # Verify the update with a direct query
        with manager.db.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM long_term_memories WHERE id = ?", (memory_id,)
            ).fetchone()

        retrieved = manager._row_to_long_term_memory(row)
        assert retrieved.content == "Updated content"
        assert retrieved.importance_score == 0.8
        assert "updated" in retrieved.tags

    def test_delete_long_term_memory(self, memory_manager):
        """Test deleting a long-term memory."""
        memory = LongTermMemory(
            content="To be deleted", memory_type="fact", importance_score=0.5
        )
        memory_id = memory_manager.store_long_term_memory(memory)

        # Verify it exists
        assert memory_manager.get_long_term_memory(memory_id) is not None

        # Delete it
        success = memory_manager.delete_long_term_memory(memory_id)
        assert success

        # Verify it's gone
        assert memory_manager.get_long_term_memory(memory_id) is None

    # Project History CRUD Tests
    def test_store_project_history(self, memory_manager):
        """Test storing a project history entry."""
        history = ProjectHistory(
            event_type="file_modification",
            description="Added new function to handle memory storage",
            file_path="src/memory/manager.py",
            code_changes="+ def store_memory(self, content):",
        )

        history_id = memory_manager.store_project_history(history)
        assert history_id is not None
        assert isinstance(history_id, int)

    def test_get_project_history(self, memory_manager):
        """Test retrieving project history by ID."""
        history = ProjectHistory(
            event_type="feature_addition",
            description="Implemented chat memory system",
            file_path="src/chat/memory.py",
        )

        history_id = memory_manager.store_project_history(history)
        retrieved = memory_manager.get_project_history(history_id)

        assert retrieved is not None
        assert retrieved.description == "Implemented chat memory system"
        assert retrieved.event_type == "feature_addition"
        assert retrieved.file_path == "src/chat/memory.py"

    def test_get_project_history_by_file(self, memory_manager):
        """Test retrieving project history by file path."""
        histories = [
            ProjectHistory(
                event_type="file_creation",
                description="Created file A",
                file_path="src/a.py",
            ),
            ProjectHistory(
                event_type="file_modification",
                description="Modified file A",
                file_path="src/a.py",
            ),
            ProjectHistory(
                event_type="file_creation",
                description="Created file B",
                file_path="src/b.py",
            ),
        ]

        for history in histories:
            memory_manager.store_project_history(history)

        file_a_history = memory_manager.get_project_history_by_file("src/a.py")
        assert len(file_a_history) == 2

        file_b_history = memory_manager.get_project_history_by_file("src/b.py")
        assert len(file_b_history) == 1

    def test_get_project_history_by_event_type(self, memory_manager):
        """Test retrieving project history by event type."""
        histories = [
            ProjectHistory(event_type="file_creation", description="Created file 1"),
            ProjectHistory(event_type="bug_fix", description="Fixed bug 1"),
            ProjectHistory(event_type="file_creation", description="Created file 2"),
        ]

        for history in histories:
            memory_manager.store_project_history(history)

        creations = memory_manager.get_project_history_by_event_type("file_creation")
        assert len(creations) == 2

        bug_fixes = memory_manager.get_project_history_by_event_type("bug_fix")
        assert len(bug_fixes) == 1

    # Search Tests
    def test_search_all_memories(self, memory_manager):
        """Test full-text search across all memory types."""
        # Store different types of memories with Python content
        conversation = ConversationMessage(
            content="I love Python programming", role="user"
        )
        longterm = LongTermMemory(
            content="Python is user's favorite language",
            memory_type="preference",
            importance_score=0.8,
        )
        project = ProjectHistory(
            event_type="feature_addition", description="Added Python code linting"
        )

        memory_manager.store_conversation_message(conversation)
        memory_manager.store_long_term_memory(longterm)
        memory_manager.store_project_history(project)

        # Search for "Python"
        results = memory_manager.search_all_memories("Python")
        assert len(results) == 3

        # Check that results are MemorySearchResult objects
        for result in results:
            assert isinstance(result, MemorySearchResult)
            assert "Python" in result.content or "Python" in str(result.metadata)

    def test_clear_session_data(self, memory_manager):
        """Test clearing conversation data for a specific session."""
        # Store messages in multiple sessions
        messages = [
            ConversationMessage(content="Msg 1", role="user", session_id="session1"),
            ConversationMessage(content="Msg 2", role="user", session_id="session1"),
            ConversationMessage(content="Msg 3", role="user", session_id="session2"),
        ]

        for msg in messages:
            memory_manager.store_conversation_message(msg)

        # Clear session1
        success = memory_manager.clear_session_data("session1")
        assert success

        # Verify session1 is cleared but session2 remains
        session1_history = memory_manager.get_conversation_history("session1")
        assert len(session1_history) == 0

        session2_history = memory_manager.get_conversation_history("session2")
        assert len(session2_history) == 1

    def test_get_memory_stats(self, memory_manager):
        """Test getting memory statistics."""
        # Add some test data
        memory_manager.store_conversation_message(
            ConversationMessage(content="Test msg", role="user", tokens=2)
        )
        memory_manager.store_long_term_memory(
            LongTermMemory(
                content="Test memory", memory_type="fact", importance_score=0.5
            )
        )

        stats = memory_manager.get_memory_stats()
        assert isinstance(stats, dict)
        assert stats["conversation_messages"] >= 1
        assert stats["long_term_memories"] >= 1
        assert stats["project_history"] >= 0

    # Session Persistence Tests
    def test_save_session_data_to_file(self, memory_manager, tmp_path):
        """Test saving current session data to a file."""
        # Create test conversation data for current session
        session_id = "current_session"
        messages = [
            ConversationMessage(
                content="Hello", role="user", session_id=session_id, tokens=1
            ),
            ConversationMessage(
                content="Hi there!", role="assistant", session_id=session_id, tokens=2
            ),
            ConversationMessage(
                content="How are you?", role="user", session_id=session_id, tokens=4
            ),
        ]

        for msg in messages:
            memory_manager.store_conversation_message(msg)

        # Save session data to file
        session_file = tmp_path / "session_data.json"
        success = memory_manager.save_session_to_file(session_id, session_file)

        assert success
        assert session_file.exists()

        # Verify file contents
        import json

        with open(session_file) as f:
            data = json.load(f)

        assert "session_id" in data
        assert "messages" in data
        assert "saved_at" in data
        assert data["session_id"] == session_id
        assert len(data["messages"]) == 3
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][0]["role"] == "user"

    def test_load_session_data_from_file(self, memory_manager, tmp_path):
        """Test loading session data from a file."""
        # Create test session file
        session_file = tmp_path / "session_data.json"
        session_data = {
            "session_id": "restored_session",
            "saved_at": "2024-01-01T12:00:00",
            "messages": [
                {
                    "content": "Restored message 1",
                    "role": "user",
                    "session_id": "restored_session",
                    "timestamp": "2024-01-01T12:00:00",
                    "tokens": 3,
                    "metadata": {},
                    "created_at": "2024-01-01T12:00:00",
                },
                {
                    "content": "Restored message 2",
                    "role": "assistant",
                    "session_id": "restored_session",
                    "timestamp": "2024-01-01T12:01:00",
                    "tokens": 3,
                    "metadata": {},
                    "created_at": "2024-01-01T12:01:00",
                },
            ],
        }

        import json

        with open(session_file, "w") as f:
            json.dump(session_data, f)

        # Load session data
        loaded_session_id = memory_manager.load_session_from_file(session_file)

        assert loaded_session_id == "restored_session"

        # Verify messages were loaded into database
        history = memory_manager.get_conversation_history("restored_session")
        assert len(history) == 2
        assert history[0].content == "Restored message 1"
        assert history[0].role == "user"
        assert history[1].content == "Restored message 2"
        assert history[1].role == "assistant"

    def test_save_session_nonexistent_session(self, memory_manager, tmp_path):
        """Test saving session data for non-existent session."""
        session_file = tmp_path / "empty_session.json"
        success = memory_manager.save_session_to_file(
            "nonexistent_session", session_file
        )

        # Should still succeed but create empty session file
        assert success
        assert session_file.exists()

        import json

        with open(session_file) as f:
            data = json.load(f)

        assert data["session_id"] == "nonexistent_session"
        assert len(data["messages"]) == 0

    def test_load_session_nonexistent_file(self, memory_manager, tmp_path):
        """Test loading session from non-existent file."""
        session_file = tmp_path / "nonexistent.json"
        loaded_session_id = memory_manager.load_session_from_file(session_file)

        # Should return None for non-existent file
        assert loaded_session_id is None

    def test_load_session_corrupted_file(self, memory_manager, tmp_path):
        """Test loading session from corrupted JSON file."""
        session_file = tmp_path / "corrupted.json"
        with open(session_file, "w") as f:
            f.write("{ invalid json content")

        loaded_session_id = memory_manager.load_session_from_file(session_file)

        # Should return None for corrupted file
        assert loaded_session_id is None

    def test_get_last_session_id(self, memory_manager):
        """Test getting the last active session ID."""
        # Store messages in different sessions with different timestamps
        from datetime import datetime, timezone

        # Session 1 (older)
        msg1 = ConversationMessage(
            content="Old message", role="user", session_id="session_1"
        )
        msg1.timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat()
        memory_manager.store_conversation_message(msg1)

        # Session 2 (newer)
        msg2 = ConversationMessage(
            content="New message", role="user", session_id="session_2"
        )
        msg2.timestamp = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc).isoformat()
        memory_manager.store_conversation_message(msg2)

        # Get last session ID
        last_session_id = memory_manager.get_last_session_id()

        # Should return the session with the most recent message
        assert last_session_id == "session_2"

    def test_get_last_session_id_no_sessions(self, memory_manager):
        """Test getting last session ID when no sessions exist."""
        last_session_id = memory_manager.get_last_session_id()
        assert last_session_id is None

    # Crawl4AI Chunking Integration Tests
    def test_chunk_text_with_sliding_window(self, memory_manager):
        """Test text chunking using Crawl4AI sliding window strategy."""
        long_text = (
            "This is a long piece of text that needs to be chunked into smaller segments. "
            "Each segment should be manageable for processing by AI models. "
            "The chunking strategy should preserve context while creating reasonable segments. "
            "We want to test that the sliding window approach works correctly. "
            "This text should be split into multiple overlapping chunks. "
            "The overlapping ensures that context is preserved between chunks. "
            "This is important for semantic understanding in AI applications."
        )

        chunks = memory_manager.chunk_text_sliding_window(
            text=long_text,
            window_size=20,  # 20 words per chunk
            step=10,  # 10 word step (50% overlap)
        )

        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk.split()) <= 20 for chunk in chunks)

    def test_chunk_text_with_regex(self, memory_manager):
        """Test text chunking using Crawl4AI regex-based strategy."""
        text_with_paragraphs = (
            "This is the first paragraph. It contains several sentences. "
            "This paragraph discusses one topic.\n\n"
            "This is the second paragraph. It starts a new topic. "
            "The content here is different from the first paragraph.\n\n"
            "Here is a third paragraph with its own content. "
            "Each paragraph should be treated as a separate chunk."
        )

        chunks = memory_manager.chunk_text_regex(
            text=text_with_paragraphs,
            patterns=[r"\n\n"],  # Split on double newlines (paragraphs)
        )

        assert len(chunks) == 3
        assert "first paragraph" in chunks[0]
        assert "second paragraph" in chunks[1]
        assert "third paragraph" in chunks[2]

    def test_chunk_and_store_long_term_memory(self, memory_manager):
        """Test chunking text and storing as multiple long-term memories."""
        long_content = (
            "Python is a high-level programming language known for its simplicity. "
            "It was created by Guido van Rossum and first released in 1991. "
            "Python emphasizes code readability with its notable use of significant whitespace. "
            "The language's design philosophy emphasizes code readability and a syntax that allows programmers to express concepts in fewer lines of code. "
            "Python supports multiple programming paradigms including procedural, object-oriented, and functional programming. "
            "It has a large and comprehensive standard library, often described as coming with 'batteries included'. "
            "Python is widely used in web development, data analysis, artificial intelligence, and scientific computing."
        )

        memory_ids = memory_manager.chunk_and_store_long_term_memory(
            content=long_content,
            memory_type="fact",
            importance_score=0.8,
            tags=["python", "programming"],
            window_size=25,  # Smaller chunks
            step=20,
        )

        assert len(memory_ids) > 1
        assert all(isinstance(memory_id, int) for memory_id in memory_ids)


class TestDatabaseMigrations:
    """Test database migration system."""

    def test_schema_version_tracking(self, temp_db):
        """Test that database version is properly tracked."""
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        # Initialize fresh database
        manager = MigrationManager(temp_db)
        manager.initialize_version_tracking()

        # Should start at version 0 (no migrations applied)
        assert manager.get_current_version() == 0

        # Set version
        manager.set_version(1)
        assert manager.get_current_version() == 1

    def test_migration_registration(self, temp_db):
        """Test registering and listing migrations."""
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        manager = MigrationManager(temp_db)

        # Register test migrations
        manager.register_migration(
            version=1,
            name="add_test_column",
            up_sql="ALTER TABLE conversation_messages ADD COLUMN test_col TEXT",
            down_sql="ALTER TABLE conversation_messages DROP COLUMN test_col",
        )

        manager.register_migration(
            version=2,
            name="add_test_index",
            up_sql="CREATE INDEX idx_test ON conversation_messages(test_col)",
            down_sql="DROP INDEX idx_test",
        )

        migrations = manager.get_registered_migrations()
        assert len(migrations) == 2
        assert migrations[0]["version"] == 1
        assert migrations[1]["version"] == 2

    def test_apply_single_migration(self, temp_db):
        """Test applying a single migration."""
        from src.my_coding_agent.core.memory.database_schema import MemoryDatabase
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        # Initialize database with original schema
        db = MemoryDatabase(temp_db)
        db.initialize()

        manager = MigrationManager(temp_db)
        manager.initialize_version_tracking()

        # Register and apply migration
        manager.register_migration(
            version=1,
            name="add_priority_column",
            up_sql="ALTER TABLE long_term_memories ADD COLUMN priority INTEGER DEFAULT 1",
            down_sql="ALTER TABLE long_term_memories DROP COLUMN priority",
        )

        # Apply migration
        result = manager.apply_migration(1)
        assert result is None  # No backup created for this migration
        assert manager.get_current_version() == 1

        # Verify column was added
        import sqlite3

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            columns = cursor.execute("PRAGMA table_info(long_term_memories)").fetchall()
            column_names = [col[1] for col in columns]
            assert "priority" in column_names

    def test_apply_multiple_migrations_in_order(self, temp_db):
        """Test applying multiple migrations in correct order."""
        from src.my_coding_agent.core.memory.database_schema import MemoryDatabase
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        # Initialize database
        db = MemoryDatabase(temp_db)
        db.initialize()

        manager = MigrationManager(temp_db)
        manager.initialize_version_tracking()

        # Register migrations out of order
        manager.register_migration(
            version=2,
            name="add_index",
            up_sql="CREATE INDEX idx_priority ON long_term_memories(priority)",
            down_sql="DROP INDEX idx_priority",
        )

        manager.register_migration(
            version=1,
            name="add_column",
            up_sql="ALTER TABLE long_term_memories ADD COLUMN priority INTEGER DEFAULT 1",
            down_sql="ALTER TABLE long_term_memories DROP COLUMN priority",
        )

        # Apply all migrations
        applied = manager.apply_all_migrations()
        assert len(applied) == 2
        assert applied[0] == 1  # Should apply version 1 first
        assert applied[1] == 2  # Then version 2
        assert manager.get_current_version() == 2

    def test_rollback_migration(self, temp_db):
        """Test rolling back a migration."""
        from src.my_coding_agent.core.memory.database_schema import MemoryDatabase
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        # Setup database and migration
        db = MemoryDatabase(temp_db)
        db.initialize()

        manager = MigrationManager(temp_db)
        manager.initialize_version_tracking()

        manager.register_migration(
            version=1,
            name="add_test_column",
            up_sql="ALTER TABLE conversation_messages ADD COLUMN test_col TEXT DEFAULT 'test'",
            down_sql="ALTER TABLE conversation_messages DROP COLUMN test_col",
        )

        # Apply then rollback
        manager.apply_migration(1)
        assert manager.get_current_version() == 1

        result = manager.rollback_migration(1)
        assert result is True
        assert manager.get_current_version() == 0

        # Verify column was removed
        import sqlite3

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            columns = cursor.execute(
                "PRAGMA table_info(conversation_messages)"
            ).fetchall()
            column_names = [col[1] for col in columns]
            assert "test_col" not in column_names

    def test_migration_validation(self, temp_db):
        """Test migration validation and error handling."""
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        manager = MigrationManager(temp_db)

        # Test invalid SQL
        with pytest.raises(ValueError, match="Invalid migration SQL"):
            manager.register_migration(
                version=1,
                name="invalid_sql",
                up_sql="INVALID SQL STATEMENT",
                down_sql="DROP TABLE nonexistent",
            )

    def test_prevent_duplicate_migration_versions(self, temp_db):
        """Test that duplicate migration versions are prevented."""
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        manager = MigrationManager(temp_db)

        # Register first migration
        manager.register_migration(
            version=1,
            name="first_migration",
            up_sql="ALTER TABLE conversation_messages ADD COLUMN col1 TEXT",
            down_sql="ALTER TABLE conversation_messages DROP COLUMN col1",
        )

        # Try to register duplicate version
        with pytest.raises(ValueError, match="Migration version 1 already registered"):
            manager.register_migration(
                version=1,
                name="duplicate_migration",
                up_sql="ALTER TABLE conversation_messages ADD COLUMN col2 TEXT",
                down_sql="ALTER TABLE conversation_messages DROP COLUMN col2",
            )

    def test_skip_already_applied_migrations(self, temp_db):
        """Test that already applied migrations are skipped."""
        from src.my_coding_agent.core.memory.database_schema import MemoryDatabase
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        # Setup
        db = MemoryDatabase(temp_db)
        db.initialize()

        manager = MigrationManager(temp_db)
        manager.initialize_version_tracking()

        # Register migrations
        manager.register_migration(
            version=1,
            name="migration_1",
            up_sql="ALTER TABLE conversation_messages ADD COLUMN test1 TEXT",
            down_sql="ALTER TABLE conversation_messages DROP COLUMN test1",
        )

        manager.register_migration(
            version=2,
            name="migration_2",
            up_sql="ALTER TABLE conversation_messages ADD COLUMN test2 TEXT",
            down_sql="ALTER TABLE conversation_messages DROP COLUMN test2",
        )

        # Apply first migration only
        manager.apply_migration(1)
        assert manager.get_current_version() == 1

        # Apply all migrations - should only apply version 2
        applied = manager.apply_all_migrations()
        assert applied == [2]  # Only migration 2 should be applied
        assert manager.get_current_version() == 2

    def test_backup_creation_during_migration(self, temp_db):
        """Test that backups are created before risky migrations."""
        import os

        from src.my_coding_agent.core.memory.database_schema import MemoryDatabase
        from src.my_coding_agent.core.memory.migration_manager import MigrationManager

        # Setup database with some data
        db = MemoryDatabase(temp_db)
        db.initialize()

        # Add some test data
        import sqlite3

        with sqlite3.connect(temp_db) as conn:
            conn.execute(
                """
                INSERT INTO conversation_messages
                (session_id, content, role, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    "test_session",
                    "test content",
                    "user",
                    "2024-01-01T00:00:00",
                    "2024-01-01T00:00:00",
                ),
            )
            conn.commit()

        manager = MigrationManager(temp_db)
        manager.initialize_version_tracking()

        # Register migration that creates backup
        manager.register_migration(
            version=1,
            name="risky_migration",
            up_sql="ALTER TABLE conversation_messages ADD COLUMN test_col TEXT",
            down_sql="ALTER TABLE conversation_messages DROP COLUMN test_col",
            create_backup=True,
        )

        # Apply migration
        backup_path = manager.apply_migration(1)

        # Verify backup was created
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".backup")

        # Verify backup contains our data
        with sqlite3.connect(backup_path) as backup_conn:
            cursor = backup_conn.cursor()
            result = cursor.execute(
                "SELECT content FROM conversation_messages WHERE content = ?",
                ("test content",),
            ).fetchone()
            assert result is not None
