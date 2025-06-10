"""SQLite database schema for memory system with FTS5 support."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryDatabase:
    """SQLite database manager for memory system with FTS5 support."""

    def __init__(self, db_path: str | Path):
        """Initialize database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Initialize the database with all tables and indexes."""
        logger.info(f"Initializing memory database at {self.db_path}")

        with sqlite3.connect(self.db_path) as conn:
            self._enable_fts5(conn)
            self._create_tables(conn)
            self._create_indexes(conn)
            self._create_fts_tables(conn)

        logger.info("Memory database initialized successfully")

    def _enable_fts5(self, conn: sqlite3.Connection) -> None:
        """Enable FTS5 extension if available."""
        try:
            conn.execute("SELECT fts5(?)", ("test",))
            logger.debug("FTS5 extension is available")
        except sqlite3.OperationalError as e:
            logger.error(f"FTS5 extension not available: {e}")
            raise RuntimeError("FTS5 extension is required but not available") from e

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all memory system tables."""

        # Conversation messages table (short-term memory)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                timestamp TEXT NOT NULL,
                tokens INTEGER,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)

        # Long-term memories table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL CHECK (memory_type IN (
                    'preference', 'fact', 'lesson', 'instruction', 'project_info', 'user_info'
                )),
                importance_score REAL NOT NULL CHECK (importance_score >= 0.0 AND importance_score <= 1.0),
                tags TEXT DEFAULT '[]',
                embedding BLOB,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL
            )
        """)

        # Project history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL CHECK (event_type IN (
                    'file_modification', 'file_creation', 'file_deletion',
                    'feature_addition', 'bug_fix', 'refactoring',
                    'architecture_change', 'dependency_update', 'configuration_change'
                )),
                description TEXT NOT NULL,
                file_path TEXT,
                code_changes TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)

        logger.debug("Created all memory system tables")

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create indexes for better query performance."""

        # Conversation messages indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_session
            ON conversation_messages(session_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_timestamp
            ON conversation_messages(timestamp)
        """)

        # Long-term memories indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_longterm_type
            ON long_term_memories(memory_type)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_longterm_importance
            ON long_term_memories(importance_score DESC)
        """)

        # Project history indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_event_type
            ON project_history(event_type)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_timestamp
            ON project_history(created_at)
        """)

        logger.debug("Created all database indexes")

    def _create_fts_tables(self, conn: sqlite3.Connection) -> None:
        """Create FTS5 virtual tables for full-text search."""

        # FTS5 table for conversation messages
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS conversation_messages_fts USING fts5(
                content,
                role,
                metadata,
                content='conversation_messages',
                content_rowid='id'
            )
        """)

        # FTS5 table for long-term memories
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS long_term_memories_fts USING fts5(
                content,
                memory_type,
                tags,
                metadata,
                content='long_term_memories',
                content_rowid='id'
            )
        """)

        # FTS5 table for project history
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS project_history_fts USING fts5(
                description,
                file_path,
                code_changes,
                metadata,
                content='project_history',
                content_rowid='id'
            )
        """)

        # Create triggers to keep FTS tables in sync
        self._create_fts_triggers(conn)

        logger.debug("Created all FTS5 virtual tables")

    def _create_fts_triggers(self, conn: sqlite3.Connection) -> None:
        """Create triggers to keep FTS tables synchronized with main tables."""

        # Conversation messages FTS triggers
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS conversation_messages_fts_insert AFTER INSERT ON conversation_messages
            BEGIN
                INSERT INTO conversation_messages_fts(rowid, content, role, metadata)
                VALUES (new.id, new.content, new.role, new.metadata);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS conversation_messages_fts_update AFTER UPDATE ON conversation_messages
            BEGIN
                UPDATE conversation_messages_fts SET
                    content = new.content,
                    role = new.role,
                    metadata = new.metadata
                WHERE rowid = new.id;
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS conversation_messages_fts_delete AFTER DELETE ON conversation_messages
            BEGIN
                DELETE FROM conversation_messages_fts WHERE rowid = old.id;
            END
        """)

        # Long-term memories FTS triggers
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS long_term_memories_fts_insert AFTER INSERT ON long_term_memories
            BEGIN
                INSERT INTO long_term_memories_fts(rowid, content, memory_type, tags, metadata)
                VALUES (new.id, new.content, new.memory_type, new.tags, new.metadata);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS long_term_memories_fts_update AFTER UPDATE ON long_term_memories
            WHEN (old.content != new.content OR old.memory_type != new.memory_type OR
                  old.tags != new.tags OR old.metadata != new.metadata)
            BEGIN
                UPDATE long_term_memories_fts SET
                    content = new.content,
                    memory_type = new.memory_type,
                    tags = new.tags,
                    metadata = new.metadata
                WHERE rowid = new.id;
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS long_term_memories_fts_delete AFTER DELETE ON long_term_memories
            BEGIN
                DELETE FROM long_term_memories_fts WHERE rowid = old.id;
            END
        """)

        # Project history FTS triggers
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS project_history_fts_insert AFTER INSERT ON project_history
            BEGIN
                INSERT INTO project_history_fts(rowid, description, file_path, code_changes, metadata)
                VALUES (new.id, new.description, new.file_path, new.code_changes, new.metadata);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS project_history_fts_update AFTER UPDATE ON project_history
            BEGIN
                UPDATE project_history_fts SET
                    description = new.description,
                    file_path = new.file_path,
                    code_changes = new.code_changes,
                    metadata = new.metadata
                WHERE rowid = new.id;
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS project_history_fts_delete AFTER DELETE ON project_history
            BEGIN
                DELETE FROM project_history_fts WHERE rowid = old.id;
            END
        """)

        logger.debug("Created all FTS synchronization triggers")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection.

        Returns:
            SQLite database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn

    def check_health(self) -> bool:
        """Check database health and integrity.

        Returns:
            True if database is healthy, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check database integrity
                result = conn.execute("PRAGMA integrity_check").fetchone()
                if result[0] != "ok":
                    logger.error(f"Database integrity check failed: {result[0]}")
                    return False

                # Check FTS5 is working
                conn.execute("SELECT fts5(?)", ("test",))

                # Check tables exist
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()

                expected_tables = {
                    "conversation_messages",
                    "long_term_memories",
                    "project_history",
                    "conversation_messages_fts",
                    "long_term_memories_fts",
                    "project_history_fts",
                }

                existing_tables = {row[0] for row in tables}

                if not expected_tables.issubset(existing_tables):
                    missing = expected_tables - existing_tables
                    logger.error(f"Missing tables: {missing}")
                    return False

                return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


def init_database(db_path: str | Path) -> MemoryDatabase:
    """Initialize a new memory database.

    Args:
        db_path: Path to the database file

    Returns:
        Initialized MemoryDatabase instance
    """
    db = MemoryDatabase(db_path)
    db.initialize()
    return db


def create_tables(conn: sqlite3.Connection) -> None:
    """Create database tables (standalone function for testing)."""
    db = MemoryDatabase(":memory:")
    db._create_tables(conn)


def enable_fts5(conn: sqlite3.Connection) -> None:
    """Enable FTS5 extension (standalone function for testing)."""
    db = MemoryDatabase(":memory:")
    db._enable_fts5(conn)
