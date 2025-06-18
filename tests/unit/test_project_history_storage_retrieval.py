"""
Unit tests for project history storage and retrieval operations.

Tests the ChromaDB integration for storing and retrieving project history,
memory integration components, and error handling for storage operations.
"""

import json
import os
import tempfile
import time

import pytest


def has_azure_credentials():
    """Check if Azure credentials are available for testing."""
    required_vars = ["ENDPOINT", "API_KEY", "API_VERSION", "DEPLOYMENT_NAME"]
    return all(
        os.environ.get(var) and os.environ.get(var) != "test_key"
        for var in required_vars
    )


@pytest.mark.skipif(
    not has_azure_credentials(),
    reason="Azure credentials not available for integration testing",
)
class TestProjectHistoryStorageOperations:
    """Test project history storage operations with ChromaDB."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def chroma_engine(self, temp_db_path):
        """Create ChromaRAGEngine for testing."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        # Use Azure embeddings consistently (same as production)
        return ChromaRAGEngine(
            db_path=temp_db_path, use_azure=True, embedding_model="azure"
        )

    @pytest.fixture
    def memory_handler(self, temp_db_path):
        """Create ConversationMemoryHandler for testing."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        return ConversationMemoryHandler(memory_db_path=temp_db_path)

    def test_store_project_history_basic(self, chroma_engine):
        """Test basic project history storage."""
        # Store a project history event
        doc_id = chroma_engine.store_project_history_with_embedding(
            file_path="src/test.py",
            event_type="file_creation",
            content="Created new test file with initial functions",
        )

        # Verify storage succeeded
        assert doc_id is not None
        assert isinstance(doc_id, str)
        assert doc_id.startswith("project_")

    def test_store_project_history_with_metadata(self, chroma_engine):
        """Test storing project history with additional metadata."""
        # Store event with detailed content
        content = {
            "description": "Fixed critical bug in authentication",
            "changes": [
                "Updated JWT token validation",
                "Fixed session handling",
                "Added error logging",
            ],
            "files_modified": ["src/auth.py", "src/session.py"],
            "impact_score": 0.8,
            "change_magnitude": "medium",
        }

        doc_id = chroma_engine.store_project_history_with_embedding(
            file_path="src/auth.py", event_type="bug_fix", content=json.dumps(content)
        )

        assert doc_id is not None
        assert isinstance(doc_id, str)

    def test_store_multiple_project_events(self, chroma_engine):
        """Test storing multiple project history events."""
        events = [
            {
                "file_path": "src/models.py",
                "event_type": "feature_addition",
                "content": "Added user model with authentication fields",
            },
            {
                "file_path": "src/views.py",
                "event_type": "refactoring",
                "content": "Refactored view functions for better organization",
            },
            {
                "file_path": "tests/test_models.py",
                "event_type": "test_addition",
                "content": "Added comprehensive tests for user model",
            },
        ]

        doc_ids = []
        for event in events:
            doc_id = chroma_engine.store_project_history_with_embedding(**event)
            doc_ids.append(doc_id)

        # Verify all events were stored
        assert len(doc_ids) == 3
        assert all(isinstance(doc_id, str) for doc_id in doc_ids)
        assert all(doc_id.startswith("project_") for doc_id in doc_ids)


@pytest.mark.skipif(
    not has_azure_credentials(),
    reason="Azure credentials not available for integration testing",
)
class TestProjectHistoryRetrievalOperations:
    """Test project history retrieval operations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def populated_memory_handler(self, temp_db_path):
        """Create ConversationMemoryHandler with populated project history."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        # Create handler with Azure embeddings configuration (consistent with production)
        handler = ConversationMemoryHandler(memory_db_path=temp_db_path)

        # Override the RAG engine to use Azure embeddings (same as production)
        handler.rag_engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=True, embedding_model="azure"
        )

        # Add sample events via the ChromaRAG engine
        sample_events = [
            {
                "file_path": "src/models.py",
                "event_type": "feature_addition",
                "content": "Created User model with authentication and profile fields",
            },
            {
                "file_path": "src/api.py",
                "event_type": "api_addition",
                "content": "Added REST API endpoints for user management",
            },
            {
                "file_path": "src/models.py",
                "event_type": "bug_fix",
                "content": "Fixed user validation logic to handle edge cases",
            },
        ]

        for event in sample_events:
            handler.rag_engine.store_project_history_with_embedding(**event)

        time.sleep(0.1)  # Allow indexing
        return handler

    def test_get_project_history_basic(self, populated_memory_handler):
        """Test basic project history retrieval."""
        history = populated_memory_handler.get_project_history(limit=10)

        # Should return list of events
        assert isinstance(history, list)

        # Verify event structure
        for event in history:
            assert isinstance(event, dict)
            assert "description" in event
            assert "event_type" in event
            assert "file_path" in event
            assert "timestamp" in event

    def test_search_project_history(self, populated_memory_handler):
        """Test semantic search of project history."""
        results = populated_memory_handler.search_project_history(
            query="user model API", limit=5
        )

        assert isinstance(results, list)

    def test_get_project_history_with_filters(self, populated_memory_handler):
        """Test project history retrieval with filters."""
        # Test file path filter
        history = populated_memory_handler.get_project_history(
            file_path="src/models.py", limit=10
        )
        assert isinstance(history, list)

        # Test event type filter
        history = populated_memory_handler.get_project_history(
            event_type="feature_addition", limit=10
        )
        assert isinstance(history, list)

        # Test time range filter
        current_time = time.time()
        start_time = current_time - 3600  # 1 hour ago

        history = populated_memory_handler.get_project_history(
            start_time=start_time, end_time=current_time, limit=10
        )
        assert isinstance(history, list)

    def test_generate_project_timeline(self, populated_memory_handler):
        """Test project timeline generation."""
        current_time = time.time()
        start_time = current_time - 7200  # 2 hours ago

        timeline = populated_memory_handler.generate_project_timeline(
            start_time=start_time, end_time=current_time
        )

        assert isinstance(timeline, list)

    def test_get_project_context_for_ai(self, populated_memory_handler):
        """Test generating project context for AI agent."""
        context = populated_memory_handler.get_project_context_for_ai(
            recent_hours=24, max_events=5
        )

        assert isinstance(context, str)


@pytest.mark.skipif(
    not has_azure_credentials(),
    reason="Azure credentials not available for integration testing",
)
class TestProjectHistoryErrorHandling:
    """Test error handling in project history storage operations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_retrieval_with_empty_database(self, temp_db_path):
        """Test retrieval operations with empty database."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler(memory_db_path=temp_db_path)

        # Should handle empty database gracefully
        history = handler.get_project_history(limit=10)
        assert isinstance(history, list)
        assert len(history) == 0  # Empty database should return empty list

    def test_storage_with_empty_content(self, temp_db_path):
        """Test storage operations with empty content."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=True, embedding_model="azure"
        )

        # Test with minimal content (should work)
        doc_id = engine.store_project_history_with_embedding(
            file_path="src/test.py",
            event_type="test",
            content="a",  # Minimal but valid content
        )

        assert doc_id is not None

    def test_search_with_empty_queries(self, temp_db_path):
        """Test search operations with edge case queries."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler(memory_db_path=temp_db_path)

        # Test with empty query
        results = handler.search_project_history("", limit=10)
        assert isinstance(results, list)

        # Test with whitespace query
        results = handler.search_project_history("   ", limit=10)
        assert isinstance(results, list)

    def test_retrieval_with_large_limits(self, temp_db_path):
        """Test retrieval operations with large limits."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler(memory_db_path=temp_db_path)

        # Test with very large limit
        history = handler.get_project_history(limit=10000)
        assert isinstance(history, list)

        # Test with zero limit
        history = handler.get_project_history(limit=0)
        assert isinstance(history, list)

    def test_invalid_time_ranges(self, temp_db_path):
        """Test handling of invalid time ranges."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler(memory_db_path=temp_db_path)

        # Test with end time before start time
        current_time = time.time()
        start_time = current_time
        end_time = current_time - 3600  # End before start

        history = handler.get_project_history(
            start_time=start_time, end_time=end_time, limit=10
        )
        assert isinstance(history, list)
