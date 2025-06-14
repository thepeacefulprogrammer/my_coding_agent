"""
Unit tests for memory transparency features.

Tests the system that shows users when and how the AI agent uses stored memories
to enhance its responses, providing transparency into the memory system.
"""

from datetime import datetime

import pytest
from src.my_coding_agent.core.memory.memory_transparency import (
    MemoryTransparencyManager,
    MemoryTransparencySettings,
    MemoryUsageEvent,
    TransparencyLevel,
)
from src.my_coding_agent.core.memory.memory_types import (
    MemoryRetrievalResult,
    SemanticSearchResult,
)


class TestMemoryTransparencyManager:
    """Test suite for MemoryTransparencyManager."""

    @pytest.fixture
    def transparency_settings(self):
        """Create test transparency settings."""
        return MemoryTransparencySettings(
            enabled=True,
            level=TransparencyLevel.DETAILED,
            show_memory_sources=True,
            show_relevance_scores=True,
            show_memory_count=True,
            show_search_queries=True,
            max_displayed_memories=5,
        )

    @pytest.fixture
    def transparency_manager(self, transparency_settings):
        """Create test transparency manager."""
        return MemoryTransparencyManager(settings=transparency_settings)

    @pytest.fixture
    def sample_semantic_results(self):
        """Create sample semantic search results for testing."""
        return [
            SemanticSearchResult(
                id=1,
                content="User prefers Python over JavaScript",
                memory_type="preference",
                importance_score=0.8,
                tags=["programming", "languages"],
                similarity_score=0.85,
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
            ),
            SemanticSearchResult(
                id=2,
                content="User is working on a chat application project",
                memory_type="project_info",
                importance_score=0.9,
                tags=["project", "chat", "application"],
                similarity_score=0.92,
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
            ),
        ]

    @pytest.fixture
    def sample_retrieval_results(self):
        """Create sample memory retrieval results for testing."""
        return [
            MemoryRetrievalResult(
                memory_id=1,
                source_type="longterm",
                content="User prefers Python over JavaScript",
                search_score=0.85,
                importance_score=0.8,
                tags=["programming", "languages"],
            ),
            MemoryRetrievalResult(
                memory_id=2,
                source_type="project",
                content="User is working on a chat application project",
                search_score=0.92,
                importance_score=0.9,
                tags=["project", "chat", "application"],
            ),
        ]

    def test_transparency_manager_initialization(self, transparency_settings):
        """Test MemoryTransparencyManager initialization."""
        manager = MemoryTransparencyManager(settings=transparency_settings)

        assert manager.settings == transparency_settings
        assert manager.is_enabled() is True
        assert len(manager.usage_events) == 0
        assert manager.statistics["total_memory_uses"] == 0

    def test_transparency_manager_disabled(self):
        """Test transparency manager when disabled."""
        settings = MemoryTransparencySettings(enabled=False)
        manager = MemoryTransparencyManager(settings=settings)

        assert manager.is_enabled() is False

        # Should not record events when disabled
        manager.record_memory_usage("test query", [], "semantic")
        assert len(manager.usage_events) == 0

    def test_record_memory_usage(self, transparency_manager, sample_semantic_results):
        """Test recording memory usage events."""
        query = "How to implement streaming?"
        search_type = "hybrid"

        transparency_manager.record_memory_usage(
            query, sample_semantic_results, search_type
        )

        assert len(transparency_manager.usage_events) == 1
        event = transparency_manager.usage_events[0]

        assert isinstance(event, MemoryUsageEvent)
        assert event.query == query
        assert event.memories_used == sample_semantic_results
        assert event.search_type == search_type
        assert event.memory_count == 2
        assert isinstance(event.timestamp, datetime)

    def test_generate_transparency_message_detailed(
        self, transparency_manager, sample_semantic_results
    ):
        """Test generating detailed transparency message."""
        query = "programming help"
        transparency_manager.record_memory_usage(
            query, sample_semantic_results, "semantic"
        )

        message = transparency_manager.generate_transparency_message(
            sample_semantic_results, query
        )

        assert "💭 **Memory Context**" in message
        assert "Found 2 relevant memories" in message
        assert "Search query: programming help" in message
        assert "User prefers Python over JavaScript" in message
        assert "Relevance: 85%" in message
        assert "Source: Preference" in message

    def test_generate_transparency_message_simple(self, sample_semantic_results):
        """Test generating simple transparency message."""
        settings = MemoryTransparencySettings(
            enabled=True,
            level=TransparencyLevel.SIMPLE,
            show_memory_sources=False,
            show_relevance_scores=False,
        )
        manager = MemoryTransparencyManager(settings=settings)

        message = manager.generate_transparency_message(
            sample_semantic_results, "test query"
        )

        assert "💭 Using 2 memories to enhance response" in message
        assert "Relevance:" not in message
        assert "Source:" not in message

    def test_generate_transparency_message_minimal(self, sample_semantic_results):
        """Test generating minimal transparency message."""
        settings = MemoryTransparencySettings(
            enabled=True, level=TransparencyLevel.MINIMAL, show_memory_count=False
        )
        manager = MemoryTransparencyManager(settings=settings)

        message = manager.generate_transparency_message(
            sample_semantic_results, "test query"
        )

        assert message == "💭 Enhanced with memories"

    def test_format_memory_preview_semantic(
        self, transparency_manager, sample_semantic_results
    ):
        """Test formatting memory preview for semantic search results."""
        search_result = sample_semantic_results[0]

        preview = transparency_manager._format_memory_preview(search_result)

        assert "User prefers Python over JavaScript" in preview
        assert "Relevance: 85%" in preview
        assert "Source: Preference" in preview
        assert "Tags: programming, languages" in preview

    def test_format_memory_preview_retrieval(
        self, transparency_manager, sample_retrieval_results
    ):
        """Test formatting memory preview for retrieval results."""
        retrieval_result = sample_retrieval_results[0]

        preview = transparency_manager._format_memory_preview(retrieval_result)

        assert "User prefers Python over JavaScript" in preview
        assert "Relevance: 85%" in preview
        assert "Source: Long-term memory" in preview
        assert "Tags: programming, languages" in preview

    def test_format_memory_preview_without_scores(self, sample_semantic_results):
        """Test formatting memory preview without relevance scores."""
        settings = MemoryTransparencySettings(
            enabled=True, show_relevance_scores=False, show_memory_sources=False
        )
        manager = MemoryTransparencyManager(settings=settings)

        search_result = sample_semantic_results[0]

        preview = manager._format_memory_preview(search_result)

        assert "User prefers Python over JavaScript" in preview
        assert "Relevance:" not in preview
        assert "Source:" not in preview

    def test_get_memory_usage_statistics(
        self, transparency_manager, sample_semantic_results
    ):
        """Test getting memory usage statistics."""
        # Record some usage events
        transparency_manager.record_memory_usage(
            "query1", sample_semantic_results[:1], "semantic"
        )
        transparency_manager.record_memory_usage(
            "query2", sample_semantic_results, "hybrid"
        )

        stats = transparency_manager.get_memory_usage_statistics()

        assert stats["total_memory_uses"] == 2
        assert stats["total_memories_retrieved"] == 3
        assert stats["average_memories_per_query"] == 1.5
        assert "semantic" in stats["search_types_used"]
        assert "hybrid" in stats["search_types_used"]
        assert stats["search_types_used"]["semantic"] == 1
        assert stats["search_types_used"]["hybrid"] == 1

    def test_get_recent_usage_events(
        self, transparency_manager, sample_semantic_results
    ):
        """Test getting recent usage events."""
        # Record multiple events
        for i in range(5):
            transparency_manager.record_memory_usage(
                f"query{i}", sample_semantic_results, "semantic"
            )

        recent_events = transparency_manager.get_recent_usage_events(limit=3)

        assert len(recent_events) == 3
        assert all(isinstance(event, MemoryUsageEvent) for event in recent_events)
        # Should be in reverse chronological order (most recent first)
        assert recent_events[0].query == "query4"
        assert recent_events[1].query == "query3"
        assert recent_events[2].query == "query2"

    def test_clear_usage_history(self, transparency_manager, sample_semantic_results):
        """Test clearing usage history."""
        transparency_manager.record_memory_usage(
            "test", sample_semantic_results, "semantic"
        )
        assert len(transparency_manager.usage_events) == 1

        transparency_manager.clear_usage_history()

        assert len(transparency_manager.usage_events) == 0
        stats = transparency_manager.get_memory_usage_statistics()
        assert stats["total_memory_uses"] == 0

    def test_max_displayed_memories_limit(self, sample_semantic_results):
        """Test that max displayed memories limit is respected."""
        settings = MemoryTransparencySettings(
            enabled=True, level=TransparencyLevel.DETAILED, max_displayed_memories=1
        )
        manager = MemoryTransparencyManager(settings=settings)

        message = manager.generate_transparency_message(sample_semantic_results, "test")

        # Should only show 1 memory despite having 2
        assert "Found 2 relevant memories" in message
        assert message.count("User prefers Python") == 1
        assert "User is working on a chat application" not in message
        assert "(showing top 1)" in message

    def test_transparency_with_mixed_memory_types(
        self, transparency_manager, sample_semantic_results, sample_retrieval_results
    ):
        """Test transparency with different memory result types."""
        # Mix semantic and retrieval results
        mixed_memories = [sample_semantic_results[0], sample_retrieval_results[1]]

        message = transparency_manager.generate_transparency_message(
            mixed_memories, "test query"
        )

        assert "Source: Preference" in message
        assert "Source: Project history" in message

    def test_transparency_settings_validation(self):
        """Test transparency settings validation."""
        # Valid settings
        settings = MemoryTransparencySettings(
            enabled=True, level=TransparencyLevel.DETAILED, max_displayed_memories=10
        )
        assert settings.max_displayed_memories == 10

        # Test with invalid max_displayed_memories
        with pytest.raises(ValueError):
            MemoryTransparencySettings(max_displayed_memories=0)

        with pytest.raises(ValueError):
            MemoryTransparencySettings(max_displayed_memories=-1)

    def test_memory_usage_event_creation(self, sample_semantic_results):
        """Test MemoryUsageEvent creation and properties."""
        query = "test query"
        search_type = "hybrid"

        event = MemoryUsageEvent(
            query=query, memories_used=sample_semantic_results, search_type=search_type
        )

        assert event.query == query
        assert event.memories_used == sample_semantic_results
        assert event.search_type == search_type
        assert event.memory_count == len(sample_semantic_results)
        assert isinstance(event.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_async_transparency_integration(
        self, transparency_manager, sample_semantic_results
    ):
        """Test transparency manager integration with async operations."""

        async def mock_memory_search(query: str) -> list[SemanticSearchResult]:
            return sample_semantic_results

        # Simulate async memory search and transparency recording
        query = "async test query"
        results = await mock_memory_search(query)
        transparency_manager.record_memory_usage(query, results, "async_search")

        assert len(transparency_manager.usage_events) == 1
        event = transparency_manager.usage_events[0]
        assert event.search_type == "async_search"
        assert event.memory_count == len(sample_semantic_results)
