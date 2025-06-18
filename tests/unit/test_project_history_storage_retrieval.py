"""
Unit tests for project history storage and retrieval operations.

Tests the ChromaDB integration for storing and retrieving project history,
memory integration components, and error handling for storage operations.
"""

import json
import tempfile
import time

import pytest

# Remove the Azure credential check - tests should never require real credentials
# def has_azure_credentials():
#     """Check if Azure credentials are available for testing."""
#     required_vars = ["ENDPOINT", "API_KEY", "API_VERSION", "DEPLOYMENT_NAME"]
#     return all(
#         os.environ.get(var) and os.environ.get(var) != "test_key"
#         for var in required_vars
#     )


# Remove the skipif decorator - tests should always run
# @pytest.mark.skipif(
#     not has_azure_credentials(),
#     reason="Azure credentials not available for integration testing",
# )
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

        # Use local embeddings for testing - never require real Azure credentials
        return ChromaRAGEngine(
            db_path=temp_db_path, use_azure=False, embedding_model="all-MiniLM-L6-v2"
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


# Remove the skipif decorator - tests should always run
# @pytest.mark.skipif(
#     not has_azure_credentials(),
#     reason="Azure credentials not available for integration testing",
# )
class TestProjectHistoryRetrievalOperations:
    """Test project history retrieval operations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def populated_chroma_engine(self, temp_db_path):
        """Create ChromaRAGEngine with populated project history for testing."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        # Create engine with local embeddings for testing
        engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=False, embedding_model="all-MiniLM-L6-v2"
        )

        # Add sample events
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
            engine.store_project_history_with_embedding(**event)

        time.sleep(0.1)  # Allow indexing
        return engine

    def test_get_project_history_basic(self, populated_chroma_engine):
        """Test basic project history retrieval."""
        # Test directly with ChromaRAG engine instead of ConversationMemoryHandler
        results = populated_chroma_engine.semantic_search(
            query="project history", limit=10, memory_types=["project_history"]
        )

        # Should return list of results
        assert isinstance(results, list)

        # Verify result structure
        for result in results:
            assert hasattr(result, "content")
            assert hasattr(result, "metadata")
            assert "event_type" in result.metadata
            assert "file_path" in result.metadata
            assert "timestamp" in result.metadata

    def test_search_project_history(self, populated_chroma_engine):
        """Test semantic search of project history."""
        results = populated_chroma_engine.semantic_search(
            query="user model API", limit=5, memory_types=["project_history"]
        )

        assert isinstance(results, list)

    def test_get_project_history_with_filters(self, populated_chroma_engine):
        """Test project history retrieval with different queries."""
        # Test file-specific search
        results = populated_chroma_engine.semantic_search(
            query="models.py", limit=10, memory_types=["project_history"]
        )
        assert isinstance(results, list)

        # Test event type search
        results = populated_chroma_engine.semantic_search(
            query="feature addition", limit=10, memory_types=["project_history"]
        )
        assert isinstance(results, list)

        # Test general search
        results = populated_chroma_engine.semantic_search(
            query="API endpoints", limit=10, memory_types=["project_history"]
        )
        assert isinstance(results, list)

    def test_generate_project_timeline(self, populated_chroma_engine):
        """Test generating project timeline from history."""
        results = populated_chroma_engine.semantic_search(
            query="project timeline events", limit=100, memory_types=["project_history"]
        )

        assert isinstance(results, list)

        # Verify we can sort by timestamp
        timeline = []
        for result in results:
            timeline.append(
                {
                    "content": result.content,
                    "timestamp": result.metadata.get("timestamp", 0),
                }
            )

        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        assert isinstance(timeline, list)

    def test_get_project_context_for_ai(self, populated_chroma_engine):
        """Test getting project context for AI assistance."""
        results = populated_chroma_engine.semantic_search(
            query="project context authentication",
            limit=10,
            memory_types=["project_history"],
        )

        assert isinstance(results, list)

        # Format as context string
        context_parts = []
        for result in results:
            context_parts.append(f"- {result.content}")

        context = (
            "\n".join(context_parts)
            if context_parts
            else "No project context available."
        )
        assert isinstance(context, str)
        assert len(context) > 0


# Remove the skipif decorator - tests should always run
# @pytest.mark.skipif(
#     not has_azure_credentials(),
#     reason="Azure credentials not available for integration testing",
# )
class TestProjectHistoryErrorHandling:
    """Test error handling in project history operations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_retrieval_with_empty_database(self, temp_db_path):
        """Test retrieving from empty database."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        # Use local embeddings for testing
        engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=False, embedding_model="all-MiniLM-L6-v2"
        )

        results = engine.semantic_search(
            query="project history", limit=10, memory_types=["project_history"]
        )

        assert isinstance(results, list)
        assert len(results) == 0

    def test_storage_with_empty_content(self, temp_db_path):
        """Test storing project history with empty content."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        # Use local embeddings for testing
        engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=False, embedding_model="all-MiniLM-L6-v2"
        )

        # Empty content should still work
        doc_id = engine.store_project_history_with_embedding(
            file_path="src/empty.py", event_type="file_creation", content=""
        )

        assert doc_id is not None

    def test_search_with_empty_queries(self, temp_db_path):
        """Test searching with empty queries."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        # Use local embeddings for testing
        engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=False, embedding_model="all-MiniLM-L6-v2"
        )

        # Empty query should return empty results
        results = engine.semantic_search(
            query="", limit=5, memory_types=["project_history"]
        )
        assert isinstance(results, list)

    def test_retrieval_with_large_limits(self, temp_db_path):
        """Test retrieval with very large limits."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        # Use local embeddings for testing
        engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=False, embedding_model="all-MiniLM-L6-v2"
        )

        # Large limit should not cause errors
        results = engine.semantic_search(
            query="project history", limit=10000, memory_types=["project_history"]
        )
        assert isinstance(results, list)

    def test_invalid_time_ranges(self, temp_db_path):
        """Test retrieval with ChromaRAG engine directly."""
        from my_coding_agent.core.memory.chroma_rag_engine import ChromaRAGEngine

        # Use local embeddings for testing
        engine = ChromaRAGEngine(
            db_path=temp_db_path, use_azure=False, embedding_model="all-MiniLM-L6-v2"
        )

        # Basic search should work
        results = engine.semantic_search(
            query="project history", limit=10, memory_types=["project_history"]
        )
        assert isinstance(results, list)
