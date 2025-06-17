"""Tests for project history integration with memory system."""

import time
from unittest.mock import Mock

import pytest


class TestProjectHistoryRetrieval:
    """Test project history retrieval functionality."""

    @pytest.fixture
    def mock_chroma_engine(self):
        """Create mock ChromaRAGEngine with project history."""
        mock_engine = Mock()

        # Mock search results for project history
        mock_results = [
            Mock(
                content="Added user authentication feature\n\nChanges: Implemented JWT token support",
                metadata={
                    "file_path": "src/auth.py",
                    "event_type": "feature_addition",
                    "timestamp": time.time() - 3600,  # 1 hour ago
                    "source": "project_history",
                },
            ),
            Mock(
                content="Fixed login bug with session handling\n\nChanges: Fixed token validation logic",
                metadata={
                    "file_path": "src/auth.py",
                    "event_type": "bug_fix",
                    "timestamp": time.time() - 1800,  # 30 minutes ago
                    "source": "project_history",
                },
            ),
            Mock(
                content="Refactored database connection logic\n\nChanges: Improved connection pooling",
                metadata={
                    "file_path": "src/database.py",
                    "event_type": "refactoring",
                    "timestamp": time.time() - 900,  # 15 minutes ago
                    "source": "project_history",
                },
            ),
        ]

        mock_engine.semantic_search.return_value = mock_results
        return mock_engine

    def test_get_project_history_basic(self, mock_chroma_engine):
        """Test basic project history retrieval."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        # Create handler with mocked engine
        handler = ConversationMemoryHandler()
        handler.rag_engine = mock_chroma_engine

        # Test basic retrieval
        history = handler.get_project_history()

        # Verify results
        assert len(history) == 3
        assert all("event_type" in event for event in history)
        assert all("description" in event for event in history)
        assert all("file_path" in event for event in history)
        assert all("timestamp" in event for event in history)

        # Verify sorted by timestamp (most recent first)
        timestamps = [event["timestamp"] for event in history]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_project_history_with_file_filter(self, mock_chroma_engine):
        """Test project history retrieval with file path filtering."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler()
        handler.rag_engine = mock_chroma_engine

        # Test file-specific retrieval
        handler.get_project_history(file_path="src/auth.py")

        # Should call semantic search
        mock_chroma_engine.semantic_search.assert_called_once()

        # Verify call parameters
        call_args = mock_chroma_engine.semantic_search.call_args
        assert "file:src/auth.py" in call_args[1]["query"]
        assert call_args[1]["memory_types"] == ["project_history"]

    def test_search_project_history(self, mock_chroma_engine):
        """Test semantic search across project history."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler()
        handler.rag_engine = mock_chroma_engine

        # Test semantic search
        results = handler.search_project_history("authentication bugs")

        # Verify search was called correctly
        mock_chroma_engine.semantic_search.assert_called_once_with(
            query="authentication bugs",
            limit=25,
            memory_types=["project_history"],
        )

        # Verify results format
        assert isinstance(results, list)

    def test_generate_project_timeline(self, mock_chroma_engine):
        """Test project timeline generation."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler()
        handler.rag_engine = mock_chroma_engine

        # Test timeline generation
        start_time = time.time() - 7200  # 2 hours ago
        end_time = time.time()
        timeline = handler.generate_project_timeline(start_time, end_time)

        # Verify timeline format
        assert isinstance(timeline, list)

    def test_get_project_context_for_ai(self, mock_chroma_engine):
        """Test generating project context for AI agent."""
        from my_coding_agent.core.memory_integration import ConversationMemoryHandler

        handler = ConversationMemoryHandler()
        handler.rag_engine = mock_chroma_engine

        # Test AI context generation
        context = handler.get_project_context_for_ai()

        # Should return a string
        assert isinstance(context, str)
        assert len(context) > 0
